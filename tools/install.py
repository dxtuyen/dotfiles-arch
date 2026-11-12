#!/usr/bin/env python3
"""Install native Arch dotfiles in explicit, independently repeatable stages."""

import argparse
import fcntl
import hashlib
import json
import os
import pwd
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_GROUPS = ("base", "desktop", "apps", "development", "virtualisation")


def write_journal(path, data):
    """Publish complete recovery metadata before changing the corresponding file."""
    temporary = path.with_suffix(".new")
    with temporary.open("w") as output:
        json.dump(data, output, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)
    sync_directory(path.parent)


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def identity(path):
    status = path.lstat()
    return [status.st_dev, status.st_ino]


def run(*args, **kwargs):
    print("+", " ".join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def require_arch():
    if "ID=arch" not in Path("/etc/os-release").read_text().splitlines():
        raise RuntimeError(
            "This stage must run on Arch Linux. The current system was not changed."
        )


def packages(group):
    path = ROOT / "packages" / (group + ".txt")
    if not path.is_file():
        raise RuntimeError(f"Unknown package group: {group}")
    result = []
    for line in path.read_text().splitlines():
        name = line.split("#", 1)[0].strip()
        if not name:
            continue
        pattern = (
            r"[A-Za-z][A-Za-z0-9_.-]+"
            if group == "flatpak"
            else r"[a-z0-9][a-z0-9@+_.-]*"
        )
        if not re.fullmatch(pattern, name):
            raise RuntimeError(f"Invalid package name in {path}: {name!r}")
        if name in result:
            raise RuntimeError(f"Duplicate package in {path}: {name}")
        result.append(name)
    return result


def manifest():
    data = json.loads((ROOT / "install-manifest.json").read_text())
    if data.get("version") != 1:
        raise RuntimeError("Unsupported installation manifest")
    for groups in (("home",), ("system", "laptop")):
        seen = set()
        for item in (item for group in groups for item in data.get(group, [])):
            src = (ROOT / item["source"]).resolve()
            target = Path(item["target"])
            if not src.is_relative_to(ROOT) or not src.exists():
                raise RuntimeError(f"Missing or external source: {src}")
            if target.is_absolute() or ".." in target.parts or str(target) in ("", "."):
                raise RuntimeError(f"Unsafe target: {target}")
            if str(target) in seen:
                raise RuntimeError(f"Duplicate target: {target}")
            if item.get("mode", "link") not in ("link", "render", "seed", "copy"):
                raise RuntimeError(f"Unsupported installation mode: {item}")
            seen.add(str(target))
        targets = [Path(p) for p in seen]
        for path in targets:
            if any(other in path.parents for other in targets):
                raise RuntimeError(f"Overlapping installation targets: {path}")
    return data


def system_files(*, laptop=False):
    """Common files are always selected; laptop policy is explicitly opt-in."""
    data = manifest()
    return data["system"] + (data["laptop"] if laptop else [])


def exists(path):
    return path.exists() or path.is_symlink()


def content(item, base):
    return (ROOT / item["source"]).read_text().replace("@@HOME@@", str(base)).encode()


def unchanged(item, dest, base):
    mode = item.get("mode", "link")
    if mode == "seed" and dest.is_file() and not dest.is_symlink():
        return True
    if mode == "link":
        return dest.is_symlink() and dest.resolve() == (ROOT / item["source"]).resolve()
    expected = (
        content(item, base)
        if mode == "render"
        else (ROOT / item["source"]).read_bytes()
    )
    return (
        dest.is_file()
        and not dest.is_symlink()
        and dest.read_bytes() == expected
        and dest.stat().st_mode & 0o777 == int(item.get("permissions", "644"), 8)
    )


def safe_parent(dest, base):
    # Replacing a leaf symlink is safe; writing through a symlinked parent is not.
    if not dest.parent.resolve().is_relative_to(base.resolve()):
        raise RuntimeError(f"Target parent escapes installation directory: {dest}")


def install_files(items, base, *, backup=False, dry_run=False):
    """Preflight all conflicts, journal replacements, then install atomically per file."""
    changes = []
    for item in items:
        dest = base / item["target"]
        safe_parent(dest, base)
        if unchanged(item, dest, base):
            continue
        if exists(dest) and not backup:
            raise RuntimeError(
                f"Existing unmanaged file: {dest}. Inspect it, then use --backup to preserve and replace it."
            )
        temporary = dest.with_name(dest.name + ".dotfiles-new")
        if exists(temporary):
            raise RuntimeError(f"Unexpected temporary file: {temporary}")
        changes.append((item, dest))
    for item, dest in changes:
        print(f"{item.get('mode', 'link'):6} {item['source']} -> {dest}")
    if dry_run or not changes:
        print(
            f"{len(changes)} file(s) would change."
            if dry_run
            else "Files already up to date."
        )
        return None
    state = base / (
        ".local/state/dotfiles" if base != Path("/") else "var/lib/dotfiles"
    )
    transaction = state / "backups" / (datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ"))
    safe_parent(transaction, base)
    transaction.mkdir(parents=True, mode=0o700)
    print(f"Recovery transaction: {transaction}", flush=True)
    records = []
    for item, dest in changes:
        dest.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "target": item["target"],
            "backup": None,
            "source": str(ROOT / item["source"]),
            "mode": item.get("mode", "link"),
        }
        temporary = dest.with_name(dest.name + ".dotfiles-new")
        mode = item.get("mode", "link")
        if mode != "link":
            payload = (
                content(item, base)
                if mode == "render"
                else (ROOT / item["source"]).read_bytes()
            )
            record["sha256"] = hashlib.sha256(payload).hexdigest()
        if exists(dest):
            saved = transaction / "files" / item["target"]
            saved.parent.mkdir(parents=True, exist_ok=True)
            record["backup"] = str(saved.relative_to(transaction))
            record["original_identity"] = identity(dest)
        records.append(record)
        journal = transaction / "journal.json"
        data = {"base": str(base), "files": records}
        # Write intent BEFORE moving the original, including its inode for recovery.
        write_journal(journal, data)
        if record["backup"]:
            dest.rename(saved)
            sync_directory(saved.parent)
            sync_directory(dest.parent)
        if mode == "link":
            temporary.symlink_to(ROOT / item["source"])
        else:
            temporary.write_bytes(payload)
            temporary.chmod(int(item.get("permissions", "644"), 8))
            with temporary.open("rb") as output:
                os.fsync(output.fileno())
        temporary.replace(dest)
        sync_directory(dest.parent)
    print(f"Transaction backup: {transaction}")
    return transaction


def user_install(args):
    base = Path(args.home).expanduser().resolve()
    live = base == Path.home().resolve()
    if live:
        require_arch()
        if os.geteuid() == 0:
            raise RuntimeError(
                "Run the user stage as your normal login user, without sudo."
            )
    install_files(manifest()["home"], base, backup=args.backup, dry_run=args.dry_run)
    if args.dry_run or not live:
        return
    for directory in (
        "Desktop",
        "Documents",
        "Downloads",
        "Music",
        "Pictures/Screenshots",
        "Public",
        "Videos",
        "VMs/disk",
        "VMs/iso",
    ):
        (base / directory).mkdir(parents=True, exist_ok=True)
    run("xdg-user-dirs-update")
    run("systemctl", "--user", "daemon-reload")
    units = manifest()["enable_user_units"]
    # Enabling session services does not start them in a TTY or lock the current session.
    run("systemctl", "--user", "enable", *units)
    run("systemctl", "--user", "start", "trash-clean.timer", "flatpak-update.timer")
    run(
        "gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "prefer-dark"
    )
    run(
        "gsettings",
        "set",
        "org.gnome.desktop.interface",
        "gtk-theme",
        "Gruvbox-Dark-Medium",
    )
    run(
        "gsettings",
        "set",
        "org.gnome.desktop.interface",
        "icon-theme",
        "Gruvbox-Plus-Dark",
    )
    run("fc-cache", "-f")
    run("update-desktop-database", base / ".local/share/applications")
    run(
        "python3",
        ROOT / "lib/vocabulary/scripts/configure-goldendict.py",
        "--config",
        base / ".config/goldendict/config",
        "--skip-running",
    )
    run(
        "bash",
        ROOT / "lib/configure-btop.sh",
        base / ".config/btop/btop.conf",
        "/usr/share/btop/themes/gruvbox_material_dark.theme",
    )
    print(
        "User configuration installed. Log out and log back in after the system stage."
    )


def system_install(args):
    require_arch()
    if os.geteuid() != 0:
        raise RuntimeError("Run: sudo ./install system --user YOUR_LOGIN")
    account = pwd.getpwnam(args.user)
    if account.pw_uid < 1000 or not Path(account.pw_dir).is_dir():
        raise RuntimeError("Choose an existing, regular login account.")
    conflicts = []
    for unit in (
        "NetworkManager.service",
        "NetworkManager-wait-online.service",
        "wpa_supplicant.service",
        "dhcpcd.service",
        "connman.service",
    ):
        enabled = (
            subprocess.run(
                ["systemctl", "is-enabled", "--quiet", unit],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )
        active = (
            subprocess.run(
                ["systemctl", "is-active", "--quiet", unit],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )
        if enabled or active:
            conflicts.append(unit)
    if conflicts:
        raise RuntimeError(
            "Network ownership conflict: "
            + ", ".join(conflicts)
            + ". Plan a deliberate handoff to iwd first; no services were disabled."
        )
    items = manifest()["system"]
    install_files(items, Path("/"), backup=args.backup, dry_run=args.dry_run)
    if args.dry_run:
        print(
            "Would rebuild initramfs with the installed Plymouth theme: mkinitcpio -P"
        )
        return
    # Boot reads the theme from initramfs, while shutdown reads the system copy.
    # Always rebuild so rerunning this stage retries a previously failed build.
    run("mkinitcpio", "-P")
    groups = []
    for group in ("wheel", "libvirt", "kvm"):
        try:
            __import__("grp").getgrnam(group)
        except KeyError:
            continue
        groups.append(group)
    run("usermod", "-aG", ",".join(groups), args.user)
    run("systemctl", "daemon-reload")
    run(
        "systemctl",
        "enable",
        "iwd.service",
        "systemd-networkd.service",
        "systemd-resolved.service",
        "systemd-timesyncd.service",
        "bluetooth.service",
        "power-profiles-daemon.service",
        "upower.service",
        "keyd.service",
        "earlyoom.service",
        "fstrim.timer",
        "nftables.service",
        "greetd.service",
    )
    # Do not restart networking, the login manager, key mappings or suspend services during installation.
    run("systemctl", "enable", f"fcitx5-lotus-server@{args.user}.service")
    print(
        "Common system files installed. Laptop: also run sudo ./install laptop --backup, "
        "then ./install doctor --laptop. PC: ./install doctor. "
        "Existing laptop policy is preserved. Reboot after checking. "
        "MySQL and libvirt remain on demand."
    )


def laptop_install(args):
    require_arch()
    if os.geteuid() != 0:
        raise RuntimeError("Run: sudo ./install laptop --backup")
    install_files(
        manifest()["laptop"], Path("/"), backup=args.backup, dry_run=args.dry_run
    )
    if args.dry_run:
        print("Would reload systemd and enable battery-threshold.service for the next boot.")
        return
    run("systemctl", "daemon-reload")
    run("systemctl", "enable", "battery-threshold.service")
    print(
        "Laptop policy installed: charge thresholds, lid/sleep and low-battery hibernation. "
        "Run ./install doctor --laptop. Reboot to apply after verifying swap/resume. "
        "This stage does not install common system files or rebuild initramfs."
    )


def installed(name):
    result = subprocess.run(
        ["pacman", "-Q", "--", name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"Cannot query installed package: {name}")
    return result.returncode == 0


def official_packages(args):
    require_arch()
    if any(group not in OFFICIAL_GROUPS for group in args.groups):
        raise RuntimeError("Use official groups only: " + ", ".join(OFFICIAL_GROUPS))
    names = list(
        dict.fromkeys(name for group in args.groups for name in packages(group))
    )
    command = ("sudo", "pacman", "-Syu", "--needed", "--", *names)
    if args.dry_run:
        print("Would run:", " ".join(command))
        return
    # Full upgrade avoids partial upgrades; pacman keeps its normal prompts.
    run(*command)


def package_status(args):
    """Read only: compare inventory with installed packages and local sync databases."""
    require_arch()
    repo = set(subprocess.check_output(["pacman", "-Slq"], text=True).splitlines())
    missing = []
    for group in (*OFFICIAL_GROUPS, "aur", "aur-database"):
        for name in packages(group):
            present = installed(name)
            print(
                f"{group:15} {name:32} {'installed' if present else 'missing':10} "
                f"{'sync repository' if name in repo else 'not in sync databases'}"
            )
            if group in OFFICIAL_GROUPS and name not in repo:
                missing.append(name)
    print(
        "Sync databases may be stale. Refresh only as part of a full pacman -Syu upgrade."
    )
    if missing:
        raise RuntimeError(
            "Official targets unavailable in sync databases: " + ", ".join(missing)
        )


def package_jobs(
    names, action, *, keep_going=False, dry_run=False, skip_installed=True
):
    failures = []
    for name in names:
        if skip_installed and installed(name):
            print("SKIP installed:", name)
            continue
        if dry_run:
            print("Would process:", name)
            continue
        try:
            action(name)
        except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
            print(f"FAIL {name}: {error}", file=sys.stderr)
            failures.append(name)
            if not keep_going:
                break
    if failures:
        raise RuntimeError(
            "Package failures: "
            + ", ".join(failures)
            + ". Fix the reported cause and rerun; installed targets are skipped."
        )


def aur(args):
    require_arch()
    if os.geteuid() == 0:
        raise RuntimeError("AUR/makepkg must run as your normal user, without sudo.")
    if not args.dry_run and not shutil.which("paru"):
        raise RuntimeError(
            "Paru is required for AUR dependencies. Review and bootstrap it using docs/packages.md."
        )
    if args.prepare:
        print(
            "Paru will print target PKGBUILDs; all recipe files and dependencies must be reviewed during --build."
        )

    def action(name):
        if args.prepare:
            run("paru", "-Gp", "--", name)
        else:
            # Never bypass review, dependency checks, checksums or installation prompts.
            # Paru refreshes cached sudo credentials during long unprivileged builds.
            run(
                "paru", "-S", "--needed", "--review", "--noremovemake",
                "--sudoloop", "--", name,
            )

    package_jobs(
        packages(args.group), action, keep_going=args.keep_going, dry_run=args.dry_run
    )


def local_packages(args):
    require_arch()
    if os.geteuid() == 0:
        raise RuntimeError("Run makepkg as your normal login user.")
    cache = (
        Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        / "dotfiles/local"
    )
    recipes = {p.parent.name: p for p in (ROOT / "packages/local").glob("*/PKGBUILD")}

    def action(name):
        recipe = recipes[name]
        path = cache / name
        path.mkdir(parents=True, exist_ok=True)
        for source in recipe.parent.iterdir():
            if source.is_file():
                shutil.copy2(source, path / source.name)
        print(recipe.read_text())
        if getattr(args, "unattended", False):
            run(
                "paru", "-Bi", "--needed", "--skipreview", "--noconfirm",
                "--sudoloop", "--noremovemake", "--", path,
                stdin=subprocess.DEVNULL,
            )
            return
        if input(f"Build reviewed local recipe {name}? [y/N] ").strip().lower() != "y":
            raise RuntimeError("Recipe not approved")
        run("makepkg", "--syncdeps", "--install", "--needed", cwd=path)

    # Local package names are explicit in our committed recipes.
    names = {
        name: re.search(
            r"^pkgname=([a-z0-9@+_.-]+)$", recipe.read_text(), re.MULTILINE
        ).group(1)
        for name, recipe in recipes.items()
    }
    pending = [name for name in sorted(recipes) if not installed(names[name])]
    package_jobs(
        pending,
        action,
        keep_going=args.keep_going,
        dry_run=args.dry_run,
        skip_installed=False,
    )


def flatpak_install(args):
    require_arch()
    if os.geteuid() == 0:
        raise RuntimeError("Flatpaks belong to your login user; run without sudo.")
    if args.dry_run and not shutil.which("flatpak"):
        print("Would install user Flatpaks:", ", ".join(packages("flatpak")))
        return
    present = set(
        subprocess.check_output(
            ["flatpak", "list", "--user", "--app", "--columns=application"],
            text=True,
        ).splitlines()
    )
    pending = [name for name in packages("flatpak") if name not in present]
    if args.dry_run:
        print("Missing user Flatpaks:", ", ".join(pending) or "none")
        return
    if not pending:
        print("User Flatpaks already installed.")
        return
    flags = ("--assumeyes", "--noninteractive") if getattr(args, "unattended", False) else ()
    run(
        "flatpak",
        "remote-add",
        "--user",
        "--if-not-exists",
        "flathub",
        "https://dl.flathub.org/repo/flathub.flatpakrepo",
    )
    run("flatpak", "install", "--user", *flags, "flathub", *pending)


def apps_install(args):
    """One native Paru transaction, then the existing local/Flatpak stages."""
    require_arch()
    if os.geteuid() == 0:
        raise RuntimeError("Run apps as your normal login user, without sudo.")
    if any(group not in OFFICIAL_GROUPS for group in args.groups):
        raise RuntimeError("Use official groups only: " + ", ".join(OFFICIAL_GROUPS))
    if not args.dry_run and not shutil.which("paru"):
        raise RuntimeError("Bootstrap Paru first using docs/packages.md; no packages were changed.")
    names = list(dict.fromkeys(
        name for group in (*args.groups, "aur") for name in packages(group)
    ))
    command = [
        "paru", "-Syu", "--needed", "--sudoloop", "--batchinstall", "--noremovemake",
        "--nofailfast" if args.keep_going else "--failfast",
    ]
    if args.unattended:
        command.extend(("--skipreview", "--noconfirm"))
        print("Unattended: package defaults accepted; recipe review skipped for this run.")
    else:
        command.append("--review")
    command.extend(("--", *names))
    if args.dry_run:
        print("Would run:", " ".join(command))
    elif args.unattended:
        run(*command, stdin=subprocess.DEVNULL)
    else:
        run(*command)
    # A failed full upgrade must stop before later stages; never catch that failure.
    local_packages(args)
    flatpak_install(args)
    if args.dry_run:
        print("Dry run complete; no packages changed.")
    else:
        print("Package stages complete. Apply home/system configuration separately.")


def doctor(args):
    require_arch()
    failures = []

    def check(*command):
        try:
            run(*command)
        except (OSError, subprocess.CalledProcessError) as error:
            print("FAIL", error)
            failures.append(" ".join(command))

    commands = (
        "sway",
        "swaylock",
        "swayidle",
        "foot",
        "tofi",
        "tofi-drun",
        "waybar",
        "mako",
        "wlsunset",
        "wl-copy",
        "grim",
        "slurp",
        "jq",
        "inotifywait",
        "wpctl",
        "playerctl",
        "paplay",
        "brightnessctl",
        "upower",
        "fcitx5",
        "impala",
        "iwctl",
        "wiremix",
        "bluetui",
        "swayview",
        "goldendict",
        "sioyek",
        "nvim",
        "brave",
    )
    for name in commands:
        path = shutil.which(name)
        print(("OK  " if path else "FAIL"), name, path or "not installed")
        if not path:
            failures.append(name)
    for item in manifest()["home"]:
        dest = Path.home() / item["target"]
        if not unchanged(item, dest, Path.home()):
            failures.append(str(dest))
            print("FAIL configuration", dest)
    for item in system_files(laptop=args.laptop):
        dest = Path("/") / item["target"]
        if not unchanged(item, dest, Path("/")):
            failures.append(str(dest))
            print("FAIL system configuration", dest)
    for path in (
        "/etc/pam.d/swaylock",
        "/usr/share/themes/Gruvbox-Dark-Medium/gtk-4.0/gtk.css",
        "/usr/share/icons/Gruvbox-Plus-Dark/index.theme",
        "/usr/share/icons/Bibata-Modern-Classic/index.theme",
        "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
        "/usr/share/edk2/x64/OVMF_CODE.4m.fd",
    ):
        ok = Path(path).is_file()
        print("OK  " if ok else "FAIL", path)
        if not ok:
            failures.append(path)
    check(
        "systemd-analyze",
        "--user",
        "verify",
        *[
            str(Path.home() / i["target"])
            for i in manifest()["home"]
            if i["target"].endswith((".service", ".timer", ".target"))
        ],
    )
    for scope in (["--user"], []):
        result = subprocess.run(
            [
                "systemctl",
                *scope,
                "list-units",
                "--failed",
                "--no-legend",
                "--plain",
                "--no-pager",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode or result.stdout.strip():
            print(result.stdout, result.stderr)
            failures.append("failed user units" if scope else "failed system units")
    check("findmnt", "/boot")
    check("swapon", "--show")
    for unit in (
        "iwd.service",
        "systemd-networkd.service",
        "systemd-resolved.service",
        "upower.service",
    ):
        check("systemctl", "is-enabled", "--quiet", unit)
    if args.laptop:
        check("systemctl", "is-enabled", "--quiet", "battery-threshold.service")
        print(
            "Check resume=UUID= and disk swap, then test lock, suspend and hibernate "
            "on the laptop: docs/installation.md."
        )
    else:
        print("Checked common configuration only. Use doctor --laptop for laptop policy.")
    if failures:
        raise RuntimeError(
            f"{len(failures)} check(s) failed; resolve them before relying on the desktop."
        )


def replacement_matches(record, dest):
    if not exists(dest):
        return False
    if record["mode"] == "link":
        return dest.is_symlink() and str(dest.readlink()) == record["source"]
    return (
        dest.is_file()
        and not dest.is_symlink()
        and hashlib.sha256(dest.read_bytes()).hexdigest() == record.get("sha256")
    )


def restore(args):
    transaction = Path(args.transaction).expanduser().resolve()
    journal = transaction / "journal.json"
    data = json.loads(journal.read_text())
    base = Path(data["base"])
    if not base.is_absolute() or base != base.resolve():
        raise RuntimeError("Unsafe journal base")
    records = list(reversed(data["files"]))
    seen = set()
    # Validate all paths and current files before mutating anything.
    for record in records:
        target = Path(record["target"])
        if target.is_absolute() or ".." in target.parts or str(target) in ("", "."):
            raise RuntimeError("Unsafe journal target")
        if target in seen or any(
            target in other.parents or other in target.parents for other in seen
        ):
            raise RuntimeError("Duplicate or overlapping journal target")
        seen.add(target)
        dest = base / target
        safe_parent(dest, base)
        if record.get("restored"):
            continue
        saved = None
        if record["backup"]:
            backup = Path(record["backup"])
            if backup != Path("files") / target:
                raise RuntimeError("Unsafe journal backup")
            saved = transaction / backup
            if not saved.parent.resolve().is_relative_to(transaction):
                raise RuntimeError("Unsafe journal backup parent")
        original_here = exists(dest) and record.get("original_identity") == identity(
            dest
        )
        # Covers interruption before backup rename and after restoring the original.
        if saved is not None and not exists(saved):
            if not original_here:
                raise RuntimeError(f"Missing transaction backup: {saved}")
            continue
        if exists(dest) and not replacement_matches(record, dest):
            raise RuntimeError(
                f"Inspect and move the current file before restoring it: {dest}"
            )
        temporary = dest.with_name(dest.name + ".dotfiles-new")
        if exists(temporary) and not replacement_matches(record, temporary):
            raise RuntimeError(f"Inspect interrupted temporary file: {temporary}")
    if args.dry_run:
        for record in records:
            if not record.get("restored"):
                print("Would restore", base / record["target"])
        return
    for record in records:
        if record.get("restored"):
            continue
        dest = base / record["target"]
        saved = transaction / record["backup"] if record["backup"] else None
        if saved is None or exists(saved):
            if exists(dest):
                dest.unlink()
            if saved is not None:
                saved.rename(dest)
                sync_directory(saved.parent)
            temporary = dest.with_name(dest.name + ".dotfiles-new")
            if exists(temporary):
                temporary.unlink()
            sync_directory(dest.parent)
        record["restored"] = True
        write_journal(journal, data)
        print("Restored", dest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser(
        "plan", help="validate and print the complete native file inventory"
    )
    p.set_defaults(func=lambda _: print(json.dumps(manifest(), indent=2)))
    p = sub.add_parser("user", help="install home files and enable user units")
    p.add_argument(
        "--home",
        default=str(Path.home()),
        help="alternate home for an offline installation test",
    )
    p.add_argument("--backup", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=user_install)
    p = sub.add_parser(
        "system", help="install common system settings, rebuild initramfs and enable services"
    )
    p.add_argument("--user", required=True)
    p.add_argument("--backup", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=system_install)
    p = sub.add_parser(
        "laptop", help="add laptop charge, lid and sleep policy after the system stage"
    )
    p.add_argument("--backup", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=laptop_install)
    p = sub.add_parser("packages", help="full system upgrade and official packages")
    p.add_argument(
        "groups",
        nargs="*",
        default=["base", "desktop", "apps", "development", "virtualisation"],
    )
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=official_packages)
    p = sub.add_parser(
        "apps", help="install/update official and AUR packages together, then local/Flatpak"
    )
    p.add_argument("groups", nargs="*", default=list(OFFICIAL_GROUPS))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--keep-going", action="store_true", help="let Paru try independent AUR builds after failures")
    p.add_argument(
        "--unattended", action="store_true",
        help="skip recipe review and accept package-tool defaults for this run",
    )
    p.set_defaults(func=apps_install)
    p = sub.add_parser(
        "package-status", help="read-only installed and repository package inventory"
    )
    p.set_defaults(func=package_status)
    p = sub.add_parser(
        "aur", help="install missing AUR targets using Paru with recipe review"
    )
    p.add_argument("--group", choices=["aur", "aur-database"], default="aur")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--build", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--keep-going",
        action="store_true",
        help="try independent targets; report all failures",
    )
    p.set_defaults(func=aur)
    p = sub.add_parser(
        "local-packages", help="build versioned recipes committed in packages/local"
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--keep-going", action="store_true")
    p.set_defaults(func=local_packages)
    p = sub.add_parser("flatpak", help="install per-user TickTick")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=flatpak_install)
    p = sub.add_parser("doctor", help="verify packages, files and service definitions")
    p.add_argument("--laptop", action="store_true", help="also verify laptop files and battery-threshold service enablement")
    p.set_defaults(func=doctor)
    p = sub.add_parser("restore", help="restore one file-install transaction")
    p.add_argument("transaction")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=restore)
    args = parser.parse_args()
    if args.command in ("plan", "doctor", "package-status"):
        args.func(args)
        return
    # Serialize installers without storing a lock in the checkout or requiring root.
    lock_root = Path("/tmp")
    lock_path = lock_root / f"dotfiles-install-{os.getuid()}.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(
            "dotfiles: interrupted; rerun the package stage or inspect the printed file recovery transaction."
        )
    except (
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        subprocess.CalledProcessError,
    ) as error:
        sys.exit(f"dotfiles: {error}")

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
    for group in ("home", "system"):
        seen = set()
        for item in data.get(group, []):
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
            dest.rename(saved)
            record["backup"] = str(saved.relative_to(transaction))
        records.append(record)
        # Journal before creating the replacement, so an interrupted install can be restored.
        (transaction / "journal.json").write_text(
            json.dumps({"base": str(base), "files": records}, indent=2) + "\n"
        )
        if mode == "link":
            temporary.symlink_to(ROOT / item["source"])
        else:
            temporary.write_bytes(payload)
            temporary.chmod(int(item.get("permissions", "644"), 8))
        temporary.replace(dest)
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
        "Dictionary/Longman",
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
        "--dictionary",
        base / "Dictionary/Longman",
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
    items = manifest()["system"]
    install_files(items, Path("/"), backup=args.backup, dry_run=args.dry_run)
    if args.dry_run:
        return
    groups = []
    for group in ("wheel", "libvirt", "kvm"):
        try:
            __import__("grp").getgrnam(group)
        except KeyError:
            continue
        groups.append(group)
    run("usermod", "-aG", ",".join(groups), args.user)
    run("systemctl", "daemon-reload")
    # Switch ownership at the next boot without interrupting the current link.
    for unit in (
        "NetworkManager.service",
        "NetworkManager-wait-online.service",
        "wpa_supplicant.service",
    ):
        result = subprocess.run(
            ["systemctl", "is-enabled", "--quiet", unit],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            run("systemctl", "disable", unit)
    run(
        "systemctl",
        "enable",
        "iwd.service",
        "systemd-resolved.service",
        "systemd-timesyncd.service",
        "bluetooth.service",
        "power-profiles-daemon.service",
        "keyd.service",
        "earlyoom.service",
        "fstrim.timer",
        "nftables.service",
        "greetd.service",
        "battery-threshold.service",
    )
    # Do not restart networking, the login manager, key mappings or suspend services during installation.
    run("systemctl", "enable", f"fcitx5-lotus-server@{args.user}.service")
    print(
        "System files installed. Reboot after checking ./install doctor. MySQL and libvirt remain on demand."
    )


def official_packages(args):
    require_arch()
    names = list(
        dict.fromkeys(name for group in args.groups for name in packages(group))
    )
    # An Arch full upgrade avoids partial upgrades. Pacman retains its normal review prompts.
    run("sudo", "pacman", "-Syu", "--needed", *names)


def aur(args):
    require_arch()
    if os.geteuid() == 0:
        raise RuntimeError("AUR/makepkg must run as your normal user, without sudo.")
    cache = (
        Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        / "dotfiles/build"
    )
    cache.mkdir(parents=True, exist_ok=True)
    for name in packages(args.group):
        path = cache / name
        if args.prepare:
            if not path.exists():
                run(
                    "git",
                    "clone",
                    "--depth=1",
                    f"https://aur.archlinux.org/{name}.git",
                    path,
                )
            else:
                dirty = subprocess.check_output(
                    [
                        "git",
                        "-C",
                        str(path),
                        "status",
                        "--porcelain",
                        "--untracked-files=no",
                    ],
                    text=True,
                )
                if dirty:
                    raise RuntimeError(
                        f"{path} has edited recipes; inspect or move it before preparing again."
                    )
                run("git", "-C", path, "pull", "--ff-only")
            revision = subprocess.check_output(
                ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
            ).strip()
            (path / ".git/dotfiles-prepared").write_text(revision + "\n")
            print(f"Review {path}/PKGBUILD, .install files and patches ({revision}).")
        else:
            marker = path / ".git/dotfiles-prepared"
            if not marker.is_file():
                raise RuntimeError(
                    f"Prepare and review {name} first: ./install aur --prepare"
                )
            revision = subprocess.check_output(
                ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
            ).strip()
            dirty = subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(path),
                    "status",
                    "--porcelain",
                    "--untracked-files=no",
                ],
                text=True,
            )
            if revision != marker.read_text().strip() or dirty:
                raise RuntimeError(
                    f"{name} changed after preparation. Prepare and review the recipe again."
                )
            run(
                "makepkg",
                "--syncdeps",
                "--install",
                "--needed",
                "--cleanbuild",
                "--pkg",
                name,
                cwd=path,
            )
    if args.prepare:
        print(
            "After reviewing every recipe, run ./install aur --build. This builds these exact checkouts."
        )


def local_packages(args):
    require_arch()
    if os.geteuid() == 0:
        raise RuntimeError("Run makepkg as your normal login user.")
    cache = (
        Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        / "dotfiles/local"
    )
    for recipe in sorted((ROOT / "packages/local").glob("*/PKGBUILD")):
        path = cache / recipe.parent.name
        path.mkdir(parents=True, exist_ok=True)
        for source in recipe.parent.iterdir():
            if source.is_file():
                shutil.copy2(source, path / source.name)
        run("makepkg", "--syncdeps", "--install", "--needed", "--cleanbuild", cwd=path)


def flatpak_install(args):
    require_arch()
    if os.geteuid() == 0:
        raise RuntimeError("Flatpaks belong to your login user; run without sudo.")
    run(
        "flatpak",
        "remote-add",
        "--user",
        "--if-not-exists",
        "flathub",
        "https://dl.flathub.org/repo/flathub.flatpakrepo",
    )
    run("flatpak", "install", "--user", "flathub", *packages("flatpak"))


def doctor(args):
    require_arch()
    failures = []
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
        "paplay",
        "brightnessctl",
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
        "google-chrome-stable",
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
    for item in manifest()["system"]:
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
    run(
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
        result = subprocess.check_output(
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
        )
        if result.strip():
            print(result)
            failures.append("failed user units" if scope else "failed system units")
    run("findmnt", "/boot")
    run("swapon", "--show")
    run(
        "systemctl", "is-enabled", "--quiet", "iwd.service", "systemd-resolved.service"
    )
    print(
        "Check resume=UUID= and disk swap, then test lock, suspend and hibernate on the laptop: docs/installation.md."
    )
    if failures:
        raise RuntimeError(
            f"{len(failures)} check(s) failed; resolve them before relying on the desktop."
        )


def restore(args):
    transaction = Path(args.transaction).expanduser().resolve()
    data = json.loads((transaction / "journal.json").read_text())
    base = Path(data["base"])
    records = list(reversed(data["files"]))
    # Preflight the whole restore before mutating anything.
    for record in records:
        dest = base / record["target"]
        safe_parent(dest, base)
        if ".." in Path(record["target"]).parts or Path(record["target"]).is_absolute():
            raise RuntimeError("Unsafe journal target")
        if exists(dest):
            expected_link = (
                record["mode"] == "link"
                and dest.is_symlink()
                and str(dest.readlink()) == record["source"]
            )
            expected_file = (
                record["mode"] != "link"
                and dest.is_file()
                and not dest.is_symlink()
                and hashlib.sha256(dest.read_bytes()).hexdigest()
                == record.get("sha256")
            )
            if not (expected_link or expected_file):
                raise RuntimeError(
                    f"Inspect and move the current file before restoring it: {dest}"
                )
        if record["backup"]:
            saved = transaction / record["backup"]
            if not saved.parent.resolve().is_relative_to(transaction):
                raise RuntimeError("Unsafe journal backup")
            if not exists(saved):
                raise RuntimeError(f"Missing transaction backup: {saved}")
    for record in records:
        dest = base / record["target"]
        if exists(dest):
            dest.unlink()
        if record["backup"]:
            saved = transaction / record["backup"]
            saved.rename(dest)
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
        "system", help="copy system settings; enable services for next boot"
    )
    p.add_argument("--user", required=True)
    p.add_argument("--backup", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=system_install)
    p = sub.add_parser("packages", help="full system upgrade and official packages")
    p.add_argument(
        "groups",
        nargs="*",
        default=["base", "desktop", "apps", "development", "virtualisation"],
    )
    p.set_defaults(func=official_packages)
    p = sub.add_parser(
        "aur", help="prepare recipes for review, then build the reviewed checkouts"
    )
    p.add_argument("--group", choices=["aur", "aur-database"], default="aur")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--build", action="store_true")
    p.set_defaults(func=aur)
    p = sub.add_parser(
        "local-packages", help="build versioned recipes committed in packages/local"
    )
    p.set_defaults(func=local_packages)
    p = sub.add_parser("flatpak", help="install per-user TickTick")
    p.set_defaults(func=flatpak_install)
    p = sub.add_parser("doctor", help="verify packages, files and service definitions")
    p.set_defaults(func=doctor)
    p = sub.add_parser("restore", help="restore one file-install transaction")
    p.add_argument("transaction")
    p.set_defaults(func=restore)
    args = parser.parse_args()
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
    except (
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        subprocess.CalledProcessError,
    ) as error:
        sys.exit(f"dotfiles: {error}")

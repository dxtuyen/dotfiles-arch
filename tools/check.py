#!/usr/bin/env python3
"""Check the native configuration without touching the running desktop."""

import configparser
import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import xml.etree.ElementTree as ET
from itertools import chain
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "dotfiles_install", ROOT / "tools/install.py"
)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def run(*args, **kwargs):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), check=True, **kwargs)


def static_checks():
    data = installer.manifest()
    for group in (
        "base",
        "desktop",
        "apps",
        "development",
        "virtualisation",
        "aur",
        "aur-database",
        "flatpak",
    ):
        installer.packages(group)
    for path in chain.from_iterable(
        (ROOT / tree).rglob("*")
        for tree in ("config", "bin", "lib", "share", "shell", "systemd", "system")
    ):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix in (".toml", ".json"):
            if path.suffix == ".toml":
                tomllib.loads(path.read_text())
            else:
                json.loads(path.read_text())
        if path.suffix == ".svg":
            ET.parse(path)
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        if re.search(
            r"/nix/store/|/run/current-system|nixos-rebuild|nix-collect-garbage|@(?:flock|jq|timeout|alarmSound|sleepAction|ovmf|popupToggle|qtPlugins)@",
            text,
        ):
            raise RuntimeError(
                f"Nix runtime dependency remains: {path.relative_to(ROOT)}"
            )
    for item in data["home"]:
        if item["target"].startswith(".local/bin/") and not os.access(
            ROOT / item["source"], os.X_OK
        ):
            raise RuntimeError(f"Command is not executable: {item['source']}")
    units = {
        Path(i["target"]).name: ROOT / i["source"]
        for i in data["home"]
        if i["target"].startswith(".config/systemd/user/")
    }
    for name in data["enable_user_units"]:
        if name not in units or "[Install]" not in units[name].read_text():
            raise RuntimeError(f"Cannot enable user unit: {name}")
    # Qt configurations refer to a shared palette; validate that it is shipped.
    targets = {item["target"] for item in data["home"]}
    for toolkit in ("qt5ct", "qt6ct"):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(ROOT / f"config/{toolkit}/{toolkit}.conf")
        palette = parser.get("Appearance", "color_scheme_path")
        if (
            not palette.startswith("@@HOME@@/")
            or palette.removeprefix("@@HOME@@/") not in targets
        ):
            raise RuntimeError(f"Unmanaged Qt palette: {palette}")
    for path in units.values():
        parser = configparser.ConfigParser(strict=False, interpolation=None)
        parser.read(path)
        for directive in ("After", "Before", "BindsTo", "PartOf", "Wants", "Requires"):
            if parser.has_option("Unit", directive):
                for dependency in parser.get("Unit", directive).split():
                    if (
                        dependency.endswith((".service", ".timer"))
                        and dependency not in units
                    ):
                        raise RuntimeError(
                            f"Unknown user unit dependency in {path}: {dependency}"
                        )
    for path in ROOT.rglob("*.nix"):
        raise RuntimeError(f"Unexpected Nix file: {path}")
    for path in (ROOT / "share/applications").glob("*.desktop"):
        run("desktop-file-validate", path)
    scripts = [
        *(ROOT / "bin").glob("*"),
        *(ROOT / "lib").rglob("*.sh"),
        *(ROOT / "shell").glob("*.sh"),
    ]
    scripts.extend((ROOT / "system/bin").glob("*"))
    scripts.append(ROOT / "install")
    run("shellcheck", "--external-sources", "-P", "SCRIPTDIR", *scripts)
    run(
        "shellcheck",
        "-s",
        "bash",
        "--external-sources",
        "-P",
        "SCRIPTDIR",
        ROOT / "shell/bashrc",
        ROOT / "shell/bash_profile",
        ROOT / "shell/profile",
    )
    return data


def session_units(data):
    with tempfile.TemporaryDirectory(prefix="arch-unit-check-") as directory:
        home = Path(directory)
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install_files(data["home"], home)
        units = home / ".config/systemd/user"
        for name in data["enable_user_units"]:
            parser = configparser.ConfigParser(strict=False, interpolation=None)
            parser.read(units / name)
            for target in parser.get("Install", "WantedBy").split():
                wants = units / (target + ".wants")
                wants.mkdir(exist_ok=True)
                (wants / name).symlink_to("../" + name)
        # HOME and SYSTEMD_UNIT_PATH isolate verification from the live user manager.
        standard = "/usr/lib/systemd/user"
        env = dict(
            os.environ,
            HOME=directory,
            XDG_CONFIG_HOME=str(home / ".config"),
            XDG_RUNTIME_DIR=directory,
            SYSTEMD_UNIT_PATH=f"{units}:{standard}",
        )
        run(
            "systemd-analyze",
            "--user",
            "verify",
            "--man=no",
            "--generators=no",
            *sorted(units.glob("*.service")),
            *sorted(units.glob("*.timer")),
            *sorted(units.glob("*.target")),
            env=env,
        )
        run(
            "foot",
            "--check-config",
            "--config",
            ROOT / "config/foot/foot.ini",
            env=env,
        )
        run(
            "sway",
            "--validate",
            "--config",
            ROOT / "config/sway/config",
            env=dict(
                env,
                WLR_BACKENDS="headless",
                WLR_RENDERER="pixman",
                WLR_LIBINPUT_NO_DEVICES="1",
            ),
        )


def main():
    os.chdir(ROOT)
    data = static_checks()
    session_units(data)
    if (ROOT / "tests").is_dir():
        run(sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v")
    print("Native configuration and unit checks passed.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))

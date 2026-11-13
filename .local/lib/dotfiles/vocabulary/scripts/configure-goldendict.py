#!/usr/bin/env python3
"""Set GoldenDict appearance, offline defaults, and Longman/Anki preferences."""

import argparse
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def goldendict_running():
    result = subprocess.run(
        ["pgrep", "-u", str(os.getuid()), "-x", "goldendict|goldendict-ng"],
        stdout=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError("Could not check whether GoldenDict is running.")
    return result.returncode == 0


def configure(config_file, dictionary_dir=None, *, check=False):
    if config_file.is_symlink():
        raise RuntimeError(f"Expected an app-managed file, not a symlink: {config_file}")
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root = ET.parse(config_file, parser=parser).getroot() if config_file.exists() else ET.Element("config")
    if root.tag != "config":
        raise RuntimeError(f"Unexpected GoldenDict config root: {root.tag}")
    changed = False

    def ensure(parent, tag):
        nonlocal changed
        node = parent.find(tag)
        if node is None:
            node = ET.SubElement(parent, tag)
            changed = True
        return node

    def value(parent, tag, text):
        nonlocal changed
        node = ensure(parent, tag)
        if node.text != text:
            node.text = text
            changed = True

    preferences = ensure(root, "preferences")
    for tag, text in {"displayStyle": "modern", "darkMode": "1", "darkReaderMode": "0"}.items():
        value(preferences, tag, text)
    anki = ensure(preferences, "ankiConnectServer")
    if anki.get("enabled") != "1":
        anki.set("enabled", "1")
        changed = True
    for tag, text in {
        "host": "127.0.0.1",
        "port": "8765",
        "deck": "LongMan",
        "model": "Longman",
        "word": "Word",
        "text": "selected_text",
        "sentence": "marked_sentence",
        "addAudio": "1",
    }.items():
        value(anki, tag, text)

    # Explicit empty sections prevent GoldenDict from restoring demo sources
    # (notably the enabled dict.org server) when it first reads this file.
    for section in ("mediawikis", "websites", "dictservers", "programs", "voiceEngines"):
        for source in ensure(root, section):
            if source.get("enabled") != "0":
                source.set("enabled", "0")
                changed = True
    value(ensure(root, "forvo"), "enable", "0")

    paths = ensure(root, "paths")
    if dictionary_dir is not None and not any(
        node.text == str(dictionary_dir) for node in paths.findall("path")
    ):
        ET.SubElement(paths, "path", recursive="0").text = str(dictionary_dir)
        changed = True
    if check or not changed:
        return changed

    config_file.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(config_file.stat().st_mode) if config_file.exists() else 0o600
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=config_file.parent, delete=False) as output:
            temporary = Path(output.name)
            ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)
        temporary.chmod(mode)
        temporary.replace(config_file)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, help="Explicitly add this dictionary directory.")
    parser.add_argument("--check", action="store_true", help="Check preferences without writing files.")
    parser.add_argument("--skip-running", action="store_true")
    args = parser.parse_args()
    if args.check:
        if configure(args.config, args.dictionary, check=True):
            raise RuntimeError("Preferences need updating. Quit GoldenDict, then run goldendict-anki-config.")
        print("GoldenDict preferences match; no files changed.")
        return
    if goldendict_running():
        message = "Quit GoldenDict (including its tray icon), then run goldendict-anki-config."
        if args.skip_running:
            print(f"GoldenDict configuration deferred. {message}")
            return
        raise RuntimeError(message)
    changed = configure(args.config, args.dictionary)
    print("Configured GoldenDict for Longman/Anki." if changed else "GoldenDict is already configured.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ET.ParseError) as error:
        sys.exit(f"Could not configure GoldenDict: {error}")

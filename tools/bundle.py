#!/usr/bin/env python3
"""Create a portable source bundle without Git metadata, caches, or local secrets."""

import argparse
import hashlib
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = (
    "README.md",
    ".gitignore",
    "config",
    "bin",
    "lib",
    "share",
    "shell",
    "systemd",
    "system",
    "packages",
    "tools",
    "tests",
    "docs",
    "install",
    "install-manifest.json",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.is_relative_to(ROOT):
        parser.error(
            "Place the bundle outside the checkout (prefer an external backup device)."
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    checksum = output.with_name(output.name + ".sha256")
    if (
        output.exists()
        or output.is_symlink()
        or checksum.exists()
        or checksum.is_symlink()
    ):
        parser.error(f"Output already exists: {output}")

    def include(info):
        path = Path(info.name)
        if any(p in ("__pycache__", ".venv", ".git") for p in path.parts):
            return None
        if path.suffix in (".pyc", ".key", ".pem", ".log") or path.name == ".env":
            return None
        if info.issym() or info.islnk():
            raise RuntimeError(f"Unexpected source symlink: {path}")
        return info

    with tarfile.open(output, "w:gz") as bundle:
        for name in ALLOWED:
            bundle.add(ROOT / name, arcname="dotfiles-arch/" + name, filter=include)
    with output.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    checksum.write_text(f"{digest}  {output.name}\n")
    print(output)
    print(f"SHA256: {digest}")
    print("Copy both files to storage outside the SSD before formatting it.")


if __name__ == "__main__":
    main()

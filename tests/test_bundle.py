"""Portable bundle includes regressions and refuses to overwrite backup artifacts."""

import contextlib
import importlib.util
import io
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "bundle", Path(__file__).resolve().parents[1] / "tools/bundle.py"
)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class Bundle(unittest.TestCase):
    def test_includes_tests_and_excludes_secrets(self):
        self.assertIn("tests", b.ALLOWED)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            (root / "tests").mkdir(parents=True)
            (root / "tests/test_example.py").write_text("# regression\n")
            (root / "tests/private.key").write_text("secret")
            output = Path(tmp) / "backup.tar.gz"
            with (
                patch.object(b, "ROOT", root),
                patch.object(b, "ALLOWED", ("tests",)),
                patch.object(sys, "argv", ["bundle.py", str(output)]),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                b.main()
            with tarfile.open(output) as archive:
                self.assertIn("dotfiles-arch/tests/test_example.py", archive.getnames())
                self.assertNotIn("dotfiles-arch/tests/private.key", archive.getnames())

    def test_preserves_existing_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "backup.tar.gz"
            checksum = Path(str(output) + ".sha256")
            checksum.write_text("keep")
            with (
                patch.object(sys, "argv", ["bundle.py", str(output)]),
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                b.main()
            self.assertEqual(checksum.read_text(), "keep")
            self.assertFalse(output.exists())

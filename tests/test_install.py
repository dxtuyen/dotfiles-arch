"""Installer regression tests: temporary homes and mocked package/service commands only."""

import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "installer", Path(__file__).resolve().parents[1] / "tools/install.py"
)
i = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i)


class Files(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.source = self.root / "source"
        self.source.write_text("new\n")
        self.item = {"source": "source", "target": "config", "mode": "copy"}
        self.patch = patch.object(i, "ROOT", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def install(self, **kwargs):
        return i.install_files([self.item], self.home, **kwargs)

    def restore(self, tx, dry_run=False):
        i.restore(SimpleNamespace(transaction=str(tx), dry_run=dry_run))

    def transaction(self):
        return next((self.home / ".local/state/dotfiles/backups").iterdir())

    def test_repeat_install_no_backup(self):
        self.install()
        self.assertIsNone(self.install())

    def test_conflict_preserved(self):
        dest = self.home / "config"
        dest.write_text("original")
        with self.assertRaisesRegex(RuntimeError, "unmanaged"):
            self.install()
        self.assertEqual(dest.read_text(), "original")

    def test_backup_restore_and_repeat(self):
        dest = self.home / "config"
        dest.write_text("original")
        tx = self.install(backup=True)
        self.restore(tx, dry_run=True)
        self.assertEqual(dest.read_text(), "new\n")
        self.restore(tx)
        self.restore(tx)
        self.assertEqual(dest.read_text(), "original")

    def test_directory_backup_restore(self):
        dest = self.home / "config"
        dest.mkdir()
        (dest / "data").write_text("keep")
        tx = self.install(backup=True)
        self.restore(tx)
        self.assertEqual((dest / "data").read_text(), "keep")

    def test_restore_refuses_modified_file(self):
        tx = self.install()
        (self.home / "config").write_text("edited")
        with self.assertRaisesRegex(RuntimeError, "current file"):
            self.restore(tx)

    def test_restore_removes_new_file(self):
        tx = self.install()
        self.restore(tx)
        self.restore(tx)
        self.assertFalse((self.home / "config").exists())

    def test_dry_run_creates_nothing(self):
        self.install(dry_run=True)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_seed_preserves_user_edits(self):
        self.item["mode"] = "seed"
        dest = self.home / "config"
        dest.write_text("user preference")
        self.assertIsNone(self.install())
        self.assertEqual(dest.read_text(), "user preference")

    def test_parent_symlink_escape(self):
        (self.home / "outside").symlink_to(self.root, target_is_directory=True)
        self.item["target"] = "outside/config"
        with self.assertRaisesRegex(RuntimeError, "escapes"):
            self.install()

    def test_restore_rejects_traversal(self):
        tx = self.install()
        journal = tx / "journal.json"
        data = json.loads(journal.read_text())
        data["files"][0]["target"] = "../source"
        journal.write_text(json.dumps(data))
        with self.assertRaisesRegex(RuntimeError, "Unsafe"):
            self.restore(tx)
        self.assertEqual(self.source.read_text(), "new\n")

    def test_restore_rejects_unsafe_backup(self):
        (self.home / "config").write_text("original")
        tx = self.install(backup=True)
        journal = tx / "journal.json"
        data = json.loads(journal.read_text())
        data["files"][0]["backup"] = "../source"
        journal.write_text(json.dumps(data))
        with self.assertRaisesRegex(RuntimeError, "Unsafe"):
            self.restore(tx)

    def test_interrupt_before_backup_rename(self):
        dest = self.home / "config"
        dest.write_text("original")
        rename = Path.rename

        def interrupt(path, target):
            if path == dest:
                raise KeyboardInterrupt()
            return rename(path, target)

        with (
            patch.object(Path, "rename", interrupt),
            self.assertRaises(KeyboardInterrupt),
        ):
            self.install(backup=True)
        self.restore(self.transaction())
        self.assertEqual(dest.read_text(), "original")

    def test_interrupt_after_backup_rename(self):
        dest = self.home / "config"
        dest.write_text("original")
        with (
            patch.object(Path, "write_bytes", side_effect=KeyboardInterrupt),
            self.assertRaises(KeyboardInterrupt),
        ):
            self.install(backup=True)
        self.assertFalse(dest.exists())
        self.restore(self.transaction())
        self.assertEqual(dest.read_text(), "original")

    def test_interrupt_restore_after_original_rename(self):
        dest = self.home / "config"
        dest.write_text("original")
        tx = self.install(backup=True)
        with (
            patch.object(i, "write_journal", side_effect=KeyboardInterrupt),
            self.assertRaises(KeyboardInterrupt),
        ):
            self.restore(tx)
        self.restore(tx)
        self.assertEqual(dest.read_text(), "original")

    def test_failed_journal_write_never_moves_original(self):
        dest = self.home / "config"
        dest.write_text("original")
        with (
            patch.object(i, "write_journal", side_effect=OSError("disk full")),
            self.assertRaises(OSError),
        ):
            self.install(backup=True)
        self.assertEqual(dest.read_text(), "original")

    def test_symlink_install_and_restore(self):
        self.item["mode"] = "link"
        dest = self.home / "config"
        dest.symlink_to("missing-original")
        tx = self.install(backup=True)
        self.assertIsNone(self.install())
        self.restore(tx)
        self.assertEqual(str(dest.readlink()), "missing-original")

    def test_restore_preflights_all_files(self):
        second = dict(self.item, target="second")
        tx = i.install_files([self.item, second], self.home)
        (self.home / "config").write_text("edited")
        with self.assertRaisesRegex(RuntimeError, "current file"):
            self.restore(tx)
        self.assertEqual((self.home / "second").read_text(), "new\n")

    def test_partial_temporary_file_is_preserved_for_inspection(self):
        dest = self.home / "config"
        dest.write_text("original")
        write = Path.write_bytes

        def interrupt(path, payload):
            write(path, b"partial")
            raise KeyboardInterrupt()

        with (
            patch.object(Path, "write_bytes", interrupt),
            self.assertRaises(KeyboardInterrupt),
        ):
            self.install(backup=True)
        tx = self.transaction()
        with self.assertRaisesRegex(RuntimeError, "temporary"):
            self.restore(tx)
        self.assertEqual((tx / "files/config").read_text(), "original")

    def test_cross_filesystem_backup_failure_preserves_original(self):
        dest = self.home / "config"
        dest.write_text("original")
        with (
            patch.object(Path, "rename", side_effect=OSError("cross-device link")),
            self.assertRaises(OSError),
        ):
            self.install(backup=True)
        self.restore(self.transaction())
        self.assertEqual(dest.read_text(), "original")


class SystemInstall(unittest.TestCase):
    def setUp(self):
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        stack.enter_context(patch.object(i, "require_arch"))
        stack.enter_context(patch.object(i.os, "geteuid", return_value=0))
        stack.enter_context(
            patch.object(
                i.pwd,
                "getpwnam",
                return_value=SimpleNamespace(pw_uid=1000, pw_dir="/tmp"),
            )
        )
        stack.enter_context(
            patch.object(
                i.subprocess, "run", return_value=SimpleNamespace(returncode=1)
            )
        )
        self.files = stack.enter_context(patch.object(i, "install_files"))
        self.run = stack.enter_context(patch.object(i, "run"))
        self.args = SimpleNamespace(user="test", backup=True, dry_run=False)

    def test_rebuild_after_install_even_when_files_already_match(self):
        # A retry must rebuild an image even if the previous run copied the theme.
        self.files.return_value = None
        events = []
        self.files.side_effect = lambda *a, **kw: events.append("files")
        self.run.side_effect = lambda *command: events.append(command)
        i.system_install(self.args)
        self.assertEqual(events[:2], ["files", ("mkinitcpio", "-P")])

    def test_dry_run_never_rebuilds_or_enables_services(self):
        self.args.dry_run = True
        i.system_install(self.args)
        self.assertTrue(self.files.call_args.kwargs["dry_run"])
        self.run.assert_not_called()

    def test_failed_rebuild_stops_before_service_setup(self):
        self.run.side_effect = subprocess.CalledProcessError(1, "mkinitcpio")
        with self.assertRaises(subprocess.CalledProcessError):
            i.system_install(self.args)
        self.run.assert_called_once_with("mkinitcpio", "-P")


class Packages(unittest.TestCase):
    def setUp(self):
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)
        self.args = SimpleNamespace(
            group="aur", prepare=False, dry_run=False, keep_going=True
        )

    def test_installed_targets_skipped(self):
        action = unittest.mock.Mock()
        with patch.object(i, "installed", return_value=True):
            i.package_jobs(["already"], action)
        action.assert_not_called()

    def test_dependency_failure_keeps_going_and_reports(self):
        action = unittest.mock.Mock(
            side_effect=[subprocess.CalledProcessError(1, "paru"), None]
        )
        with (
            patch.object(i, "installed", return_value=False),
            self.assertRaisesRegex(RuntimeError, "broken"),
        ):
            i.package_jobs(["broken", "independent"], action, keep_going=True)
        self.assertEqual(action.call_count, 2)

    def test_fail_fast(self):
        action = unittest.mock.Mock(side_effect=RuntimeError("missing dependency"))
        with (
            patch.object(i, "installed", return_value=False),
            self.assertRaises(RuntimeError),
        ):
            i.package_jobs(["broken", "later"], action)
        self.assertEqual(action.call_count, 1)

    def test_interruption_stops_jobs(self):
        action = unittest.mock.Mock(side_effect=KeyboardInterrupt)
        with (
            patch.object(i, "installed", return_value=False),
            self.assertRaises(KeyboardInterrupt),
        ):
            i.package_jobs(["first", "later"], action, keep_going=True)
        self.assertEqual(action.call_count, 1)

    def test_dry_run_does_not_execute(self):
        action = unittest.mock.Mock()
        with patch.object(i, "installed", return_value=False):
            i.package_jobs(["missing"], action, dry_run=True)
        action.assert_not_called()

    def test_aur_root_refused(self):
        with (
            patch.object(i, "require_arch"),
            patch.object(i.os, "geteuid", return_value=0),
            patch.object(i, "run") as run,
        ):
            with self.assertRaisesRegex(RuntimeError, "normal user"):
                i.aur(self.args)
            run.assert_not_called()

    def test_local_makepkg_root_refused(self):
        with (
            patch.object(i, "require_arch"),
            patch.object(i.os, "geteuid", return_value=0),
            patch.object(i, "run") as run,
        ):
            with self.assertRaisesRegex(RuntimeError, "normal login user"):
                i.local_packages(SimpleNamespace(dry_run=False, keep_going=False))
            run.assert_not_called()

    def test_aur_uses_dependency_helper_and_review(self):
        with (
            patch.object(i, "require_arch"),
            patch.object(i.os, "geteuid", return_value=1000),
            patch.object(i.shutil, "which", return_value="/usr/bin/paru"),
            patch.object(i, "installed", return_value=False),
            patch.object(i, "packages", return_value=["goldendict-ng"]),
            patch.object(i, "run") as run,
        ):
            i.aur(self.args)
        run.assert_called_once_with(
            "paru",
            "-S",
            "--needed",
            "--review",
            "--noremovemake",
            "--sudoloop",
            "--",
            "goldendict-ng",
        )

    def test_aur_prepare_only_reads_recipe_without_sudo_loop(self):
        with (
            patch.object(i, "require_arch"),
            patch.object(i.os, "geteuid", return_value=1000),
            patch.object(i.shutil, "which", return_value="/usr/bin/paru"),
            patch.object(i, "installed", return_value=False),
            patch.object(i, "packages", return_value=["goldendict-ng"]),
            patch.object(i, "run") as run,
        ):
            args = SimpleNamespace(**vars(self.args))
            args.prepare = True
            i.aur(args)
        run.assert_called_once_with("paru", "-Gp", "--", "goldendict-ng")

    def test_repeat_after_partial_install_skips_success(self):
        present = set()
        calls = []

        def action(name):
            calls.append(name)
            if name == "broken" and len(calls) == 2:
                raise RuntimeError("dependency")
            present.add(name)

        with patch.object(i, "installed", side_effect=lambda name: name in present):
            with self.assertRaises(RuntimeError):
                i.package_jobs(["good", "broken", "later"], action, keep_going=True)
            i.package_jobs(["good", "broken", "later"], action, keep_going=True)
        self.assertEqual(calls, ["good", "broken", "later", "broken"])

    def test_official_stage_rejects_aur_group(self):
        with patch.object(i, "require_arch"), patch.object(i, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "official groups"):
                i.official_packages(SimpleNamespace(groups=["aur"], dry_run=False))
            run.assert_not_called()

    def test_system_network_conflict_precedes_file_writes(self):
        with (
            patch.object(i, "require_arch"),
            patch.object(i.os, "geteuid", return_value=0),
            patch.object(
                i.pwd,
                "getpwnam",
                return_value=SimpleNamespace(pw_uid=1000, pw_dir="/tmp"),
            ),
            patch.object(
                i.subprocess, "run", return_value=SimpleNamespace(returncode=0)
            ),
            patch.object(i, "install_files") as files,
        ):
            with self.assertRaisesRegex(RuntimeError, "Network ownership conflict"):
                i.system_install(
                    SimpleNamespace(user="test", backup=True, dry_run=False)
                )
            files.assert_not_called()


if __name__ == "__main__":
    unittest.main()

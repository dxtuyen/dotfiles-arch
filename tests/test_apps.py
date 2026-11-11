"""Combined package installation delegates automation to native package tools."""

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "apps_installer", Path(__file__).resolve().parents[1] / "tools/install.py"
)
i = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i)


class Apps(unittest.TestCase):
    def setUp(self):
        self.args = SimpleNamespace(
            groups=["base", "desktop"], dry_run=False,
            unattended=True, keep_going=True,
        )
        self.addCleanup(patch.stopall)
        patch.object(i, "require_arch").start()
        patch.object(i.os, "geteuid", return_value=1000).start()
        patch.object(i.shutil, "which", return_value="/usr/bin/paru").start()
        patch.object(
            i, "packages",
            side_effect=lambda group: {
                "base": ["git", "shared"], "desktop": ["foot", "shared"],
                "aur": ["tofi"],
            }[group],
        ).start()
        self.run = patch.object(i, "run").start()
        self.local = patch.object(i, "local_packages").start()
        self.flatpak = patch.object(i, "flatpak_install").start()

    def test_one_transaction_deduplicates_and_automates_only_when_requested(self):
        i.apps_install(self.args)
        self.run.assert_called_once()
        command = self.run.call_args.args
        self.assertEqual(command[:2], ("paru", "-Syu"))
        self.assertEqual(command[command.index("--") + 1:], ("git", "shared", "foot", "tofi"))
        for option in ("--sudoloop", "--batchinstall", "--skipreview", "--noconfirm", "--nofailfast"):
            self.assertIn(option, command)
        self.assertNotIn("--review", command)
        self.assertEqual(self.run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.local.assert_called_once_with(self.args)
        self.flatpak.assert_called_once_with(self.args)

    def test_interactive_mode_keeps_review_and_terminal_input(self):
        self.args.unattended = False
        i.apps_install(self.args)
        command = self.run.call_args.args
        self.assertIn("--review", command)
        self.assertNotIn("--skipreview", command)
        self.assertNotIn("--noconfirm", command)
        self.assertEqual(self.run.call_args.kwargs, {})

    def test_failed_upgrade_stops_later_stages_even_with_keep_going(self):
        self.run.side_effect = subprocess.CalledProcessError(1, "paru")
        with self.assertRaises(subprocess.CalledProcessError):
            i.apps_install(self.args)
        self.local.assert_not_called()
        self.flatpak.assert_not_called()

    def test_missing_paru_stops_before_any_package_change(self):
        i.shutil.which.return_value = None
        with self.assertRaisesRegex(RuntimeError, "Bootstrap Paru"):
            i.apps_install(self.args)
        self.run.assert_not_called()
        self.local.assert_not_called()
        self.flatpak.assert_not_called()

    def test_root_is_refused(self):
        i.os.geteuid.return_value = 0
        with self.assertRaisesRegex(RuntimeError, "normal login user"):
            i.apps_install(self.args)
        self.run.assert_not_called()

    def test_dry_run_never_authenticates_or_installs(self):
        self.args.dry_run = True
        i.shutil.which.return_value = None
        self.local.side_effect = lambda args: self.assertTrue(args.dry_run)
        self.flatpak.side_effect = lambda args: self.assertTrue(args.dry_run)
        i.apps_install(self.args)
        self.run.assert_not_called()


class NativeStages(unittest.TestCase):
    def test_unattended_local_recipe_uses_paru_and_does_not_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recipe = root / "packages/local/theme"
            recipe.mkdir(parents=True)
            (recipe / "PKGBUILD").write_text("pkgname=lab-theme\n")
            args = SimpleNamespace(unattended=True, dry_run=False, keep_going=False)
            with (
                patch.object(i, "ROOT", root), patch.object(i, "require_arch"),
                patch.object(i.os, "geteuid", return_value=1000),
                patch.dict(i.os.environ, {"XDG_CACHE_HOME": str(root / "cache")}),
                patch.object(i, "installed", return_value=False),
                patch.object(i, "run") as run,
                patch("builtins.input", side_effect=AssertionError("must not prompt")),
            ):
                i.local_packages(args)
            command = run.call_args.args
            self.assertEqual(command[:2], ("paru", "-Bi"))
            self.assertIn("--sudoloop", command)
            self.assertIn("--noconfirm", command)
            self.assertEqual(command[-1], root / "cache/dotfiles/local/theme")

    def test_flatpak_automation_options_only_apply_to_install(self):
        with (
            patch.object(i, "require_arch"),
            patch.object(i.os, "geteuid", return_value=1000),
            patch.object(i.subprocess, "check_output", return_value=""),
            patch.object(i, "packages", return_value=["com.ticktick.TickTick"]),
            patch.object(i, "run") as run,
        ):
            i.flatpak_install(SimpleNamespace(unattended=True, dry_run=False))
        remote, install = run.call_args_list
        self.assertEqual(remote.args[:2], ("flatpak", "remote-add"))
        self.assertNotIn("--assumeyes", remote.args)
        self.assertEqual(install.args[:2], ("flatpak", "install"))
        self.assertIn("--assumeyes", install.args)
        self.assertIn("--noninteractive", install.args)

    def test_dry_run_without_flatpak_does_not_query_or_install(self):
        with (
            patch.object(i, "require_arch"),
            patch.object(i.os, "geteuid", return_value=1000),
            patch.object(i.shutil, "which", return_value=None),
            patch.object(i, "packages", return_value=["com.ticktick.TickTick"]),
            patch.object(i.subprocess, "check_output") as query,
            patch.object(i, "run") as run,
        ):
            i.flatpak_install(SimpleNamespace(unattended=True, dry_run=True))
        query.assert_not_called()
        run.assert_not_called()

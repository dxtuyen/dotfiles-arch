"""Exercise popup recovery against an isolated headless Sway, with Foot clients."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("sway") and shutil.which("foot"), "needs Sway and Foot")
class Popup(unittest.TestCase):
    APP_ID = "md.obsidian.Obsidian"
    MARK = "popup-obsidian"
    MENU_TITLE_PREFIX = ""
    MATCHES = (
        'app_id="(?i)^(md\\.obsidian\\.)?obsidian$"',
        'class="(?i)^(md\\.obsidian\\.)?obsidian$"',
    )

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="popup-regression-")
        self.addCleanup(self.tmp.cleanup)
        self.runtime = Path(self.tmp.name)
        self.env = dict(os.environ)
        for name in ("SWAYSOCK", "WAYLAND_DISPLAY", "DISPLAY"):
            self.env.pop(name, None)
        self.env.update(
            XDG_RUNTIME_DIR=str(self.runtime),
            WLR_BACKENDS="headless",
            WLR_RENDERER="pixman",
            WLR_LIBINPUT_NO_DEVICES="1",
        )
        config = self.runtime / "config"
        config.write_text(
            "xwayland disable\n"
            "focus_follows_mouse no\n"
            "output * mode 1280x800\n"
            f'for_window [app_id="{self.APP_ID}"] floating enable, '
            f"move scratchpad, scratchpad show, mark --add {self.MARK}\n"
        )
        self.log = (self.runtime / "sway.log").open("w+")
        self.addCleanup(self.log.close)
        self.sway = subprocess.Popen(
            ["sway", "--config", str(config)],
            env=self.env,
            stdout=self.log,
            stderr=self.log,
        )
        self.addCleanup(self.stop_process, self.sway)
        self.wait_for(lambda: list(self.runtime.glob("sway-ipc.*.sock")))
        self.env["SWAYSOCK"] = str(next(self.runtime.glob("sway-ipc.*.sock")))
        self.wait_for(lambda: [p for p in self.runtime.glob("wayland-*") if p.is_socket()])
        self.env["WAYLAND_DISPLAY"] = next(
            p.name for p in self.runtime.glob("wayland-*") if p.is_socket()
        )

    @staticmethod
    def stop_process(process):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)

    def wait_for(self, predicate):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            result = predicate()
            if result:
                return result
            if self.sway.poll() is not None:
                self.log.seek(0)
                self.fail(self.log.read())
            time.sleep(0.03)
        self.fail("Timed out waiting for isolated Sway/client state")

    def windows(self):
        result = subprocess.run(
            ["swaymsg", "-r", "-t", "get_tree"],
            env=self.env,
            capture_output=True,
            text=True,
            check=True,
        )
        windows = {}

        def walk(node, workspace=None):
            if node.get("type") == "workspace":
                workspace = node["name"]
            if node.get("app_id") == self.APP_ID:
                windows[node["id"]] = dict(node, workspace=workspace)
            for child in node.get("nodes", []) + node.get("floating_nodes", []):
                walk(child, workspace)

        walk(json.loads(result.stdout))
        return windows

    def open_window(self, title="foot"):
        old_ids = set(self.windows())
        client = subprocess.Popen(
            ["foot", "--config=/dev/null", f"--app-id={self.APP_ID}", f"--title={title}", "cat"],
            env=self.env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.addCleanup(self.stop_process, client)
        new_id = self.wait_for(lambda: next(iter(set(self.windows()) - old_ids), None))
        self.wait_for(lambda: self.MARK in self.windows()[new_id]["marks"])
        return client, new_id

    def toggle(self, *matches):
        marker = self.runtime / "unexpected launch"
        args = [str(ROOT / "bin/sway-popup"), self.MARK]
        for match in matches:
            args.extend(("--match", match))
        args.extend(("--", "touch", str(marker)))
        result = subprocess.run(
            args, env=self.env, capture_output=True, text=True, check=False
        )
        return result, marker

    def test_closed_picker_reclaims_original(self):
        _, original = self.open_window()
        picker, picker_id = self.open_window()
        self.assertNotIn(self.MARK, self.windows()[original]["marks"])
        self.stop_process(picker)
        self.wait_for(lambda: picker_id not in self.windows())
        subprocess.run(
            ["swaymsg", "-q", "workspace number 2"],
            env=self.env,
            capture_output=True,
            check=True,
        )
        result, launched = self.toggle(*self.MATCHES)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(self.windows()), {original})
        self.assertIn(self.MARK, self.windows()[original]["marks"])
        self.assertTrue(self.windows()[original]["focused"])
        self.assertFalse(launched.exists())

    def test_existing_mark_still_hides_and_recalls_without_fallback(self):
        _, original = self.open_window()
        result, launched = self.toggle()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.windows()[original]["workspace"], "__i3_scratch")
        result, _ = self.toggle()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.windows()[original]["focused"])
        self.assertFalse(launched.exists())

    def test_absent_application_launches(self):
        result, launched = self.toggle(f'app_id="{self.APP_ID}"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.wait_for(launched.exists)

    def test_invalid_criteria_does_not_launch(self):
        result, launched = self.toggle('not_a_sway_criterion="x"')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr)
        self.assertFalse(launched.exists())

    def menu_environment(self):
        library = self.runtime / ".local/lib/dotfiles"
        library.mkdir(parents=True)
        (library / "tofi-menu.sh").symlink_to(ROOT / "lib/tofi-menu.sh")
        tofi = self.runtime / "tofi"
        tofi.write_text(
            f"#!{sys.executable}\n"
            "import json, os, pathlib, subprocess, sys\n"
            "choices = sys.stdin.read()\n"
            "pathlib.Path(os.environ['TEST_MENU_INPUT']).write_text(choices)\n"
            "pathlib.Path(os.environ['TEST_MENU_INPUT'] + '.args').write_text(json.dumps(sys.argv[1:]))\n"
            "if os.environ.get('TEST_MENU_CANCEL') != '1':\n"
            "    identifier = os.environ.get('TEST_MENU_SHOW_ID')\n"
            "    if identifier:\n"
            "        subprocess.run(['swaymsg', '-q', f'[con_id={identifier}] scratchpad show'], check=True)\n"
            "    print(choices.splitlines()[int(os.environ.get('TEST_MENU_ROW', '0'))])\n"
        )
        notify = self.runtime / "notify-send"
        notify.write_text("#!/bin/sh\nexit 0\n")
        for command in (tofi, notify):
            command.chmod(0o755)
        return dict(
            self.env, HOME=str(self.runtime),
            PATH=str(self.runtime) + os.pathsep + self.env["PATH"],
            TEST_MENU_INPUT=str(self.runtime / "menu-input"),
        )

    def test_scratchpad_menu_lists_only_hidden_windows_and_tracks_recall(self):
        _, first = self.open_window("Same title")
        _, second = self.open_window("Same title")
        for identifier in (first, second):
            subprocess.run(
                ["swaymsg", "-q", f"[con_id={identifier}] move scratchpad"],
                env=self.env, check=True,
            )
        subprocess.run(["swaymsg", "-q", "workspace number 2"], env=self.env, check=True)
        env = dict(self.menu_environment(), TEST_MENU_ROW="1")

        def select():
            subprocess.run([ROOT / "bin/scratchpad-menu"], env=env,
                           capture_output=True, text=True, check=True, timeout=5)

        select()
        rows = Path(env["TEST_MENU_INPUT"]).read_text().splitlines()
        self.assertEqual(rows, [f"1. {self.MENU_TITLE_PREFIX}Same title",
                                f"2. {self.MENU_TITLE_PREFIX}Same title"])
        arguments = json.loads(Path(env["TEST_MENU_INPUT"] + ".args").read_text())
        self.assertIn("--width=720", arguments)
        self.assertEqual(self.windows()[first]["workspace"], "__i3_scratch")
        self.assertEqual(self.windows()[second]["workspace"], "2")
        self.assertTrue(self.windows()[second]["focused"])
        # The recalled window is omitted; only the remaining hidden one is listed.
        env["TEST_MENU_ROW"] = "0"
        select()
        self.assertEqual(Path(env["TEST_MENU_INPUT"]).read_text().splitlines(),
                         [f"1. {self.MENU_TITLE_PREFIX}Same title"])
        self.assertEqual(self.windows()[first]["workspace"], "2")
        # Once hidden again, it returns to the list, even from another workspace.
        subprocess.run(["swaymsg", "-q", f"[con_id={second}] move scratchpad"],
                       env=self.env, check=True)
        subprocess.run(["swaymsg", "-q", "workspace number 3"], env=self.env, check=True)
        select()
        self.assertEqual(self.windows()[second]["workspace"], "3")
        self.assertTrue(self.windows()[second]["focused"])
        self.assertEqual(self.windows()[first]["workspace"], "2")
        subprocess.run(["swaymsg", "-q", f"[con_id={second}] move scratchpad"],
                       env=self.env, check=True)
        env["TEST_MENU_CANCEL"] = "1"
        select()
        self.assertEqual(self.windows()[first]["workspace"], "2")
        self.assertEqual(self.windows()[second]["workspace"], "__i3_scratch")
        # If the window becomes visible during selection, selecting it must not hide it.
        env["TEST_MENU_CANCEL"] = "0"
        env["TEST_MENU_SHOW_ID"] = str(second)
        select()
        self.assertEqual(self.windows()[second]["workspace"], "3")
        self.assertTrue(self.windows()[second]["focused"])

    def test_empty_scratchpad_menu_does_not_open_selector(self):
        env = self.menu_environment()
        subprocess.run([ROOT / "bin/scratchpad-menu"], env=env,
                       capture_output=True, text=True, check=True, timeout=5)
        self.assertFalse(Path(env["TEST_MENU_INPUT"]).exists())
        self.open_window()
        subprocess.run([ROOT / "bin/scratchpad-menu"], env=env,
                       capture_output=True, text=True, check=True, timeout=5)
        self.assertFalse(Path(env["TEST_MENU_INPUT"]).exists())


class TickTickPopup(Popup):
    APP_ID = "com.ticktick.TickTick"
    MARK = "popup-ticktick"
    MATCHES = (
        'app_id="(?i)^(com\\.ticktick\\.)?ticktick$"',
        'class="(?i)^(com\\.ticktick\\.)?ticktick$"',
    )


class TerminalPopup(Popup):
    APP_ID = "scratchpad-terminal"
    MARK = "popup-terminal"
    MENU_TITLE_PREFIX = "T · "
    MATCHES = ('app_id="scratchpad-terminal"',)

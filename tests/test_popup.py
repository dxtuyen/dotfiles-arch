"""Exercise popup recovery against an isolated headless Sway, with Foot clients."""

import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("sway") and shutil.which("foot"), "needs Sway and Foot")
class Popup(unittest.TestCase):
    APP_ID = "md.obsidian.Obsidian"
    MARK = "popup-obsidian"
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

    def open_window(self):
        old_ids = set(self.windows())
        client = subprocess.Popen(
            ["foot", "--config=/dev/null", f"--app-id={self.APP_ID}", "cat"],
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


class TickTickPopup(Popup):
    APP_ID = "com.ticktick.TickTick"
    MARK = "popup-ticktick"
    MATCHES = (
        'app_id="(?i)^(com\\.ticktick\\.)?ticktick$"',
        'class="(?i)^(com\\.ticktick\\.)?ticktick$"',
    )

"""Check countdown notifications against real processes without signalling the desktop."""

import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHILD = r'''
import ctypes, signal, sys
ctypes.CDLL(None).prctl(15, sys.argv[1].encode(), 0, 0, 0)
print("started", flush=True)
sys.stdin.readline()
for offset in (7, 8, 10):
    signal.signal(signal.SIGRTMIN + offset,
                  lambda number, frame: print(number - signal.SIGRTMIN, flush=True))
print("ready", flush=True)
while True:
    signal.pause()
'''


@unittest.skipUnless(sys.platform == "linux" and shutil.which("pkill"), "needs Linux/procps")
class CountdownSignals(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="countdown-signals-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.env = dict(os.environ)
        self.env["REAL_PKILL"] = shutil.which("pkill")
        # Keep the real pkill matching/handler checks, but constrain all signals
        # to this test's child so an existing Waybar can never receive them.
        wrapper = self.directory / "pkill"
        wrapper.write_text(
            f"#!{sys.executable}\n"
            "import os, sys\n"
            "os.execv(os.environ['REAL_PKILL'], [os.environ['REAL_PKILL'], "
            "'--pid', os.environ['TEST_SIGNAL_PID'], *sys.argv[1:]])\n"
        )
        wrapper.chmod(0o755)
        self.env["PATH"] = str(self.directory) + os.pathsep + self.env["PATH"]
        source = (ROOT / "bin/countdown-engine").read_text()
        self.functions = "\n".join(
            re.search(r"^" + name + r"\(\) \{\n.*?^\}", source, re.M | re.S).group()
            for name in ("notify_waybar", "notify_clock")
        )

    def start_child(self, name="waybar"):
        process = subprocess.Popen(
            [sys.executable, "-u", "-c", CHILD, name],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=0,
        )
        self.addCleanup(self.stop_child, process)
        self.env["TEST_SIGNAL_PID"] = str(process.pid)
        self.assertEqual(self.read_line(process), "started")
        return process

    @staticmethod
    def stop_child(process):
        if process.poll() is None:
            process.terminate()
        process.communicate(timeout=3)

    def read_line(self, process):
        self.assertTrue(select.select([process.stdout], [], [], 3)[0], "child response timed out")
        return process.stdout.readline().decode().strip()

    def enable_handlers(self, process):
        process.stdin.write(b"ready\n")
        process.stdin.flush()
        self.assertEqual(self.read_line(process), "ready")

    def notify(self, function):
        subprocess.run(["bash", "-c", self.functions + "\n" + function],
                       env=self.env, check=True, timeout=5)

    def test_early_update_does_not_terminate_unready_waybar(self):
        process = self.start_child()
        self.notify("notify_waybar")
        self.notify("notify_clock")
        self.assertIsNone(process.poll())
        self.enable_handlers(process)

    def test_ready_waybar_receives_full_update_and_clock_tick(self):
        process = self.start_child()
        self.enable_handlers(process)
        self.notify("notify_waybar")
        self.assertEqual(sorted(self.read_line(process) for _ in range(3)), ["10", "7", "8"])
        self.notify("notify_clock")
        self.assertEqual(self.read_line(process), "8")
        self.assertIsNone(process.poll())

    def test_similarly_named_process_receives_no_update(self):
        process = self.start_child("waybar-helper")
        self.enable_handlers(process)
        self.notify("notify_waybar")
        self.assertFalse(select.select([process.stdout], [], [], 0.1)[0])
        self.assertIsNone(process.poll())

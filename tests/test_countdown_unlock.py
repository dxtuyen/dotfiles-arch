"""Exercise lock/wake reminders without locking or notifying the real desktop."""

import configparser
import json
import os
import select
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CountdownUnlock(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="countdown-unlock-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        commands = self.directory / "bin"
        commands.mkdir()
        self.events = self.directory / "events.jsonl"
        stub = commands / "stub"
        stub.write_text(
            f"#!{sys.executable}\n"
            "import json, os, pathlib, sys\n"
            "name = pathlib.Path(sys.argv[0]).name\n"
            "with open(os.environ['TEST_EVENTS'], 'a') as output:\n"
            "    output.write(json.dumps([name, *sys.argv[1:]]) + '\\n')\n"
            "if name == 'systemctl' and 'is-active' in sys.argv:\n"
            "    sys.exit(int(os.environ.get('TEST_SESSION_INACTIVE', '0')))\n"
        )
        stub.chmod(0o755)
        for name in ("notify-send", "systemctl", "pkill"):
            (commands / name).symlink_to(stub)
        self.env = dict(
            os.environ,
            HOME=str(self.directory),
            XDG_RUNTIME_DIR=str(self.directory),
            XDG_STATE_HOME=str(self.directory),
            PATH=str(commands) + os.pathsep + os.environ["PATH"],
            TEST_EVENTS=str(self.events),
            SERVICE_RESULT="success", EXIT_CODE="exited", EXIT_STATUS="0",
        )
        self.state = self.directory / "countdown-state"

    def engine(self, command, **environment):
        subprocess.run(
            [ROOT / "bin/countdown-engine", command],
            env=dict(self.env, **environment), check=True, timeout=5,
            capture_output=True, text=True,
        )

    def write_state(self, running=False, remaining=1470, duration=25):
        self.state.write_text(
            f'DURATION="{duration}"\nINITIAL_DURATION="25"\n'
            f'RUNNING="{str(running).lower()}"\n'
            f'END_TIME="{4102444800 if running else ""}"\n'
            f'REMAINING="{remaining}"\nTASK="Study"\n'
        )

    def notifications(self):
        if not self.events.exists():
            return []
        return [event for line in self.events.read_text().splitlines()
                if (event := json.loads(line))[0] == "notify-send"]

    def test_unlock_reminds_manually_paused_timer_without_changing_state(self):
        self.write_state()
        before = self.state.read_bytes()
        self.engine("unlock-notify")
        messages = self.notifications()
        self.assertEqual(len(messages), 1)
        self.assertIn("24:30 remaining", messages[0][-1])
        self.assertEqual(self.state.read_bytes(), before)

    def test_unlock_is_silent_without_a_paused_session(self):
        self.engine("unlock-notify")
        for settings in ({"running": True}, {"remaining": 0}, {"duration": ""}):
            with self.subTest(settings=settings):
                self.write_state(**settings)
                self.engine("unlock-notify")
                self.assertEqual(self.notifications(), [])

    def test_failure_forced_stop_and_logout_are_silent(self):
        self.write_state()
        for environment in (
            {"SERVICE_RESULT": "exit-code", "EXIT_STATUS": "2"},
            {"SERVICE_RESULT": "timeout"},
            {"EXIT_CODE": "killed", "EXIT_STATUS": "TERM"},
            {"SERVICE_RESULT": "signal", "EXIT_CODE": "killed", "EXIT_STATUS": "KILL"},
            {"SERVICE_RESULT": "", "EXIT_CODE": "", "EXIT_STATUS": ""},
            {"TEST_SESSION_INACTIVE": "1"},
        ):
            with self.subTest(environment=environment):
                self.engine("unlock-notify", **environment)
                self.assertEqual(self.notifications(), [])

    def test_lock_and_wake_are_silent_then_unlock_reminds_once(self):
        for pause_commands in (("lock-pause",), ("sleep-pause", "lock-pause"),
                               ("lock-pause", "sleep-pause")):
            with self.subTest(pause_commands=pause_commands):
                self.events.write_text("")
                self.write_state(running=True)
                manual = self.directory / "inhibit-manual"
                manual.touch()
                for command in pause_commands:
                    self.engine(command)
                self.assertFalse(manual.exists())
                before = self.state.read_bytes()
                # Also consume a marker left by the old engine version.
                marker = self.directory / "countdown-sleep-paused"
                marker.touch()
                self.engine("sleep-resume")
                self.assertFalse(marker.exists())
                self.assertEqual(self.notifications(), [])
                self.engine("unlock-notify")
                self.assertEqual(len(self.notifications()), 1)
                self.assertEqual(self.state.read_bytes(), before)


class SwaylockReadiness(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="swaylock-readiness-")
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        locker = directory / "locker"
        locker.write_text(
            f"#!{sys.executable}\n"
            "import os, sys\n"
            "print(os.getpid(), flush=True)\n"
            "if sys.stdin.readline().strip() != 'lock':\n"
            "    sys.exit(2)\n"
            "os.write(3, b'\\n')\n"
            "os.close(3)\n"
            "sys.exit(int(sys.stdin.readline()))\n"
        )
        notifier = directory / "notifier"
        notifier.write_text(f"#!{sys.executable}\nprint('ready', flush=True)\n")
        for path in (locker, notifier):
            path.chmod(0o755)
        parser = configparser.ConfigParser(strict=False, interpolation=None)
        parser.read(ROOT / "systemd/user/swaylock.service")
        self.assertEqual(parser["Service"]["Type"], "notify")
        self.assertEqual(parser["Service"]["NotifyAccess"], "all")
        self.command = shlex.split(parser["Service"]["ExecStart"])
        self.command[-1] = self.command[-1].replace("/usr/bin/swaylock", str(locker))
        self.command[-1] = self.command[-1].replace("/usr/bin/systemd-notify", str(notifier))

    def start(self):
        process = subprocess.Popen(
            self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0,
        )
        self.addCleanup(self.stop, process)
        self.assertTrue(select.select([process.stdout], [], [], 3)[0])
        # The locker itself is the tracked main process, not a shell/daemon parent.
        self.assertEqual(int(process.stdout.readline()), process.pid)
        self.assertFalse(select.select([process.stdout], [], [], 0.1)[0])
        return process

    @staticmethod
    def stop(process):
        if process.poll() is None:
            process.terminate()
        process.communicate(timeout=3)

    def test_readiness_waits_for_lock_and_preserves_exit_status(self):
        process = self.start()
        process.stdin.write(b"lock\n")
        process.stdin.flush()
        self.assertTrue(select.select([process.stdout], [], [], 3)[0])
        self.assertEqual(process.stdout.readline(), b"ready\n")
        process.stdin.write(b"0\n")
        process.stdin.flush()
        self.assertEqual(process.wait(timeout=3), 0)

    def test_failed_lock_never_sends_ready(self):
        process = self.start()
        output, error = process.communicate(b"fail\n", timeout=3)
        self.assertEqual(process.returncode, 2, error)
        self.assertEqual(output, b"")

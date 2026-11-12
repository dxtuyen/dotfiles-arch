"""Power actions use explicitly installed laptop policy; no real sleep or D-Bus."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PowerPolicy(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.policy = self.root / "laptop.conf"
        self.supplies = self.root / "power_supply"
        self.supplies.mkdir()
        self.log = self.root / "commands"
        self.env = dict(os.environ, HOME=str(self.root), POWER_LOG=str(self.log),
                        PATH=f"{self.bin}:{os.environ['PATH']}")
        self.command("systemctl", 'printf "%s\\n" "$*" >> "$POWER_LOG"\n')
        self.command("busctl", 'printf \'s "%s"\\n\' "${TEST_INHIBITED:-}"\n')

    def command(self, name, body):
        path = self.bin / name
        path.write_text("#!/usr/bin/env bash\nset -eu\n" + body)
        path.chmod(0o755)

    def supply(self, name, **properties):
        directory = self.supplies / name
        directory.mkdir()
        for key, value in properties.items():
            (directory / key).write_text(value + "\n")

    def run_script(self, name, *args):
        source = (ROOT / "bin" / name).read_text()
        source = source.replace("/etc/systemd/sleep.conf.d/10-laptop.conf", str(self.policy))
        source = source.replace("/sys/class/power_supply", str(self.supplies))
        script = self.root / name
        script.write_text(source)
        subprocess.run(["bash", str(script), *args], env=self.env, check=True,
                       text=True, capture_output=True)
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_common_install_never_sleeps_even_with_battery(self):
        self.supply("BAT0", type="Battery", status="Discharging", scope="System")
        self.assertEqual(self.run_script("idle-suspend"), [])

    def test_laptop_on_battery_uses_suspend_then_hibernate(self):
        self.policy.touch()
        self.supply("BAT0", type="Battery", status="Discharging", scope="System")
        self.assertEqual(self.run_script("idle-suspend"), ["suspend-then-hibernate"])

    def test_laptop_on_ac_or_without_battery_stays_awake(self):
        self.policy.touch()
        self.assertEqual(self.run_script("idle-suspend"), [])
        self.supply("BAT0", type="Battery", status="Discharging", scope="System")
        self.supply("AC", type="Mains", online="1")
        self.assertEqual(self.run_script("idle-suspend"), [])

    def test_laptop_respects_idle_inhibitor(self):
        self.policy.touch()
        self.supply("BAT0", type="Battery", status="Discharging", scope="System")
        self.env["TEST_INHIBITED"] = "idle:sleep"
        self.assertEqual(self.run_script("idle-suspend"), [])

    def test_peripheral_battery_does_not_suspend_pc(self):
        self.policy.touch()
        self.supply("mouse", type="Battery", status="Discharging", scope="Device")
        self.assertEqual(self.run_script("idle-suspend"), [])

    def test_suspend_menu_uses_selected_policy(self):
        library = self.root / ".local/lib/dotfiles"
        library.mkdir(parents=True)
        (library / "tofi-menu.sh").write_text(
            'menu_item() { printf "%s\\n" "$1"; }\n'
            'menu_pick() { cat >/dev/null; printf "1\\n"; }\n'
        )
        self.assertEqual(self.run_script("utilities", "--power"), ["suspend"])
        self.log.unlink()
        self.policy.touch()
        self.assertEqual(self.run_script("utilities", "--power"), ["suspend-then-hibernate"])

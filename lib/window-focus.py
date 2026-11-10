"""Focus Sway windows when they report urgency."""

import json
import subprocess
import sys


def focus(swaymsg, wid):
    # The window may have closed since the event arrived.
    subprocess.run([swaymsg, "-q", f"[con_id={wid}] focus"], check=False)


def watch(swaymsg):
    with subprocess.Popen(
        [swaymsg, "-r", "-m", "-t", "subscribe", '["window"]'],
        stdout=subprocess.PIPE,
        text=True,
    ) as events:
        for line in events.stdout:
            event = json.loads(line)
            node = event.get("container", {})
            wid = node.get("id")
            if wid is None:
                continue
            if event.get("change") == "urgent" and node.get("urgent"):
                focus(swaymsg, wid)
    raise RuntimeError("Sway window event subscription ended")


def main():
    if len(sys.argv) != 3 or sys.argv[2] != "--watch":
        raise SystemExit("Usage: window-focus.py SWAYMSG --watch")
    watch(sys.argv[1])


if __name__ == "__main__":
    main()

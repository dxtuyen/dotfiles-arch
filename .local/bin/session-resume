#!/usr/bin/env bash
set -euo pipefail

# Disarm the old idle deadline before refreshing it. Do not wait on a service
# whose systemctl suspend call may itself be returning from this wake event.
systemctl --user --no-block stop idle-suspend.timer idle-suspend.service

# Give unattended wake fresh idle/display periods. Swayidle checks inhibitors.
systemctl --user --no-block try-restart swayidle.service locked-display.service
swaymsg 'output * power on'

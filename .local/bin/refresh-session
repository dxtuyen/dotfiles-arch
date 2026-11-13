#!/usr/bin/env bash
set -euo pipefail

# Reload Sway even if the display mode cannot be restored; report either error.
status=0
"$HOME/.local/bin/wlsunset-apply" || status=1
swaymsg reload || status=1
exit "$status"

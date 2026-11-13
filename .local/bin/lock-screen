#!/usr/bin/env bash
set -euo pipefail

[ "$#" -eq 0 ] || { echo "Usage: lock-screen" >&2; exit 2; }

# Concurrent callers join the same job. A failed lock must propagate to the caller.
exec systemctl --user start swaylock.service

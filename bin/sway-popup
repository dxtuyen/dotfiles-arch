#!/usr/bin/env bash
# Hide a focused popup, focus a visible one, recall it, or launch the app.
set -euo pipefail

mark=$1
shift
[ "${1:-}" != -- ] || shift

# Let Sway match the current workspace, including floating windows that have
# left the scratchpad. Read command responses only, never the window tree.
for action in \
  "[con_mark=\"^${mark}$\" workspace=__focused__ con_id=__focused__] fullscreen disable, move scratchpad" \
  "[con_mark=\"^${mark}$\" workspace=__focused__] focus" \
  "[con_mark=\"^${mark}$\"] move container to workspace current, move scratchpad, scratchpad show"; do
  if response=$(swaymsg -r "$action"); then
    exit 0
  else
    status=$?
  fi
  case "$response" in
    *'"error": "No matching node."'*) continue ;;
    *)
      printf '%s\n' "$response" >&2
      exit "$status"
      ;;
  esac
done

# Sway launches the app asynchronously, preserving argument boundaries.
printf -v launch '%q ' "$@"
exec swaymsg -q "exec $launch"

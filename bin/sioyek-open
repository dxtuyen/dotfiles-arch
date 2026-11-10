#!/usr/bin/env bash
# Always forward document arguments; a window title cannot identify a path.
set -u

if [ $# -eq 0 ]; then
  # Launching Sioyek from drun has no document argument. Raise an
  # existing window instead of asking Sioyek to reopen the last PDF.
  cid="$(swaymsg -t get_tree | jq -r '
    [.. | objects
     | select((.app_id? // "") == "sioyek"
              or ((.window_properties.class? // "") | test("^sioyek$"; "i")))]
     | .[0].id // empty')"
  if [ -n "$cid" ]; then
    swaymsg "[con_id=$cid] move container to workspace current"
    swaymsg "[con_id=$cid] focus"
    exit 0
  fi
fi

exec sioyek "$@"

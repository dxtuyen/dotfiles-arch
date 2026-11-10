#!/usr/bin/env bash
set -euo pipefail

start_threshold=85
end_threshold=90
configured=0
for battery in /sys/class/power_supply/BAT*; do
  [ -d "$battery" ] || continue
  if [ -e "$battery/charge_control_start_threshold" ]; then
    start_file="$battery/charge_control_start_threshold"
  elif [ -e "$battery/charge_start_threshold" ]; then
    start_file="$battery/charge_start_threshold"
  else continue; fi
  if [ -e "$battery/charge_control_end_threshold" ]; then
    end_file="$battery/charge_control_end_threshold"
  elif [ -e "$battery/charge_stop_threshold" ]; then
    end_file="$battery/charge_stop_threshold"
  else continue; fi
  printf '%s\n' "$start_threshold" > "$start_file"
  printf '%s\n' "$end_threshold" > "$end_file"
  configured=1
done
[ "$configured" -eq 1 ] || echo "Battery does not expose charge thresholds."

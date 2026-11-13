#!/usr/bin/env bash
set -u

commands=(sway swaylock swayidle foot waybar mako tofi jq wpctl fcitx5)
failed=0

for command in "${commands[@]}"; do
  if path=$(command -v "$command"); then
    printf 'OK      %-12s %s\n' "$command" "$path"
  else
    printf 'MISSING %-12s\n' "$command"
    failed=1
  fi
done

for scope in user system; do
  if [[ $scope == user ]]; then
    units=$(systemctl --user --no-legend --plain --failed 2>&1)
    status=$?
  else
    units=$(systemctl --no-legend --plain --failed 2>&1)
    status=$?
  fi
  if ((status != 0)); then
    printf 'Could not read %s systemd units: %s\n' "$scope" "$units" >&2
    failed=1
  elif [[ -n $units ]]; then
    printf 'FAILED %s systemd units:\n%s\n' "$scope" "$units"
    failed=1
  else
    printf 'OK      %s systemd units\n' "$scope"
  fi
done

if ((failed)); then
  exit 1
fi
printf 'Basic health checks passed.\n'

#!/usr/bin/env bash
set -euo pipefail

state="${XDG_STATE_HOME:-$HOME/.local/state}/wlsunset-mode"
requested=${1:-}

# Serialize the full stop/start/save operation, including concurrent reloads.
exec 9>"${XDG_RUNTIME_DIR:?}/wlsunset-apply.lock"
flock 9

mode=$requested
if [[ -z "$mode" && -r "$state" ]]; then
  IFS= read -r mode < "$state" || true
fi
case "$mode" in
  warm|white|natural) ;;
  *)
    if [[ -n "$requested" ]]; then
      printf 'Unknown display mode: %s\n' "$requested" >&2
      exit 2
    fi
    mode=natural
    ;;
esac

systemctl --user stop wlsunset@warm.service wlsunset@white.service wlsunset@natural.service
systemctl --user start "wlsunset@$mode.service"
# Type=exec confirms execution, then catch processes that exit during startup.
sleep 0.2
if ! systemctl --user is-active --quiet "wlsunset@$mode.service"; then
  printf 'Display mode failed. See: journalctl --user -u wlsunset@%s.service\n' "$mode" >&2
  exit 1
fi

# Commit the preference only after a successful start.
if [[ -n "$requested" ]]; then
  mkdir -p "${state%/*}"
  temporary=$(mktemp "${state}.XXXXXX")
  trap 'rm -f -- "$temporary"' EXIT
  printf '%s\n' "$mode" > "$temporary"
  mv -- "$temporary" "$state"
fi

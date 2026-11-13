#!/usr/bin/env bash
set -euo pipefail

notify_error() {
  notify-send -a toggle-touchpad -i input-touchpad -u critical -t 3000 \
    Touchpad "$1" 2>/dev/null || true
}

# Sway owns touchpad settings; this command only changes event delivery.
if ! current=$(swaymsg -t get_inputs | jq -er \
  '[.[] | select(.type == "touchpad") | .libinput.send_events][0] // empty'); then
  notify_error 'Could not read touchpad state from Sway.'
  exit 1
fi

case "$current" in
  enabled|disabled_on_external_mouse) next=disabled; label='Touchpad off' ;;
  disabled) next=enabled; label='Touchpad on' ;;
  *) notify_error "Unknown touchpad state: $current"; exit 1 ;;
esac

if ! swaymsg input type:touchpad events "$next" >/dev/null; then
  notify_error 'Could not change touchpad state.'
  exit 1
fi
notify-send -a toggle-touchpad -i input-touchpad -t 2000 Touchpad "$label"

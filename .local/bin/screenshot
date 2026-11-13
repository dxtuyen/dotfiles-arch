#!/usr/bin/env bash
# Check slurp's exit code so cancelling does not report a false error.
set -u
set -o pipefail

mode="${1:?missing mode}"

notify_error() {
  notify-send -a screenshot -i "dialog-error" -u critical -t 4000 \
    "Screenshot failed" "$1" 2>/dev/null || true
}

make_output_path() {
  local dir="$HOME/Pictures/Screenshots"
  mkdir -p "$dir" || return 1
  # mktemp reserves the name atomically, so concurrent captures cannot
  # overwrite each other even when they start in the same second.
  mktemp --tmpdir="$dir" --suffix=.png \
    "screenshot-$(date +%Y%m%d-%H%M%S)-XXXXXX"
}

case "$mode" in
  selection-clipboard)
    region="$(slurp)" || exit 1
    if ! grim -g "$region" - | wl-copy; then
      notify_error "Could not capture or copy the selection."
      exit 1
    fi
    notify-send -a screenshot -i "camera-photo" -t 2000 "Screenshot" "Selection copied to clipboard"
    ;;
  fullscreen-clipboard)
    if ! grim - | wl-copy; then
      notify_error "Could not capture or copy the screen."
      exit 1
    fi
    notify-send -a screenshot -i "camera-photo" -t 2000 "Screenshot" "Fullscreen copied to clipboard"
    ;;
  selection-save)
    region="$(slurp)" || exit 1
    f="$(make_output_path)" || { notify_error "Could not create the screenshots directory."; exit 1; }
    if ! grim -g "$region" "$f"; then
      rm -f -- "$f"
      notify_error "Could not save the selection."
      exit 1
    fi
    if wl-copy < "$f"; then
      notify-send -a screenshot -i "camera-photo" -t 2000 "Screenshot" "Selection saved and copied to clipboard"
    else
      notify-send -a screenshot -i "dialog-warning" -t 4000 "Screenshot saved" "Clipboard copy failed: $f"
      exit 1
    fi
    ;;
  fullscreen-save)
    f="$(make_output_path)" || { notify_error "Could not create the screenshots directory."; exit 1; }
    if ! grim "$f"; then
      rm -f -- "$f"
      notify_error "Could not save the fullscreen screenshot."
      exit 1
    fi
    if wl-copy < "$f"; then
      notify-send -a screenshot -i "camera-photo" -t 2000 "Screenshot" "Fullscreen saved and copied to clipboard"
    else
      notify-send -a screenshot -i "dialog-warning" -t 4000 "Screenshot saved" "Clipboard copy failed: $f"
      exit 1
    fi
    ;;
  *)
    echo "Unknown mode: $mode" >&2
    exit 1
    ;;
esac

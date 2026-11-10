# shellcheck shell=bash
# Shared presentation; each workflow owns its actions and input validation.
menu_item() {
  printf '%s  %s\n' "$2" "$1"
}

# Arguments: title, visible rows, selected row, optional detail.
# Tofi 0.9.1 returns labels, so map the selection to its original zero-based
# index. Show the selected row first because Tofi cannot preselect a row.
menu_pick() {
  local selected=${3:-0} detail=${4:-↑/↓ · Enter · Esc} choice i
  local -a items
  mapfile -t items
  ((${#items[@]})) || return 1
  detail=${detail//$'\n'/ · }
  choice=$(
    printf '%s\n' "${items[@]:selected}" "${items[@]:0:selected}" |
      tofi --history=false --require-match=true \
        --num-results="$2" --height="$((56 + 32 * $2))" \
        --prompt-text="$1 ❯ " --placeholder-text="$detail"
  ) || return 1
  for i in "${!items[@]}"; do
    if [[ "${items[i]}" == "$choice" ]]; then
      printf '%s\n' "$i"
      return 0
    fi
  done
  return 1
}

# Arguments: title, detail, placeholder. Enter accepts empty input; Esc cancels.
menu_input() {
  local input
  # Tofi 0.9.1 exits successfully on Esc too. Keep the trailing newline:
  # Enter prints one even for empty input, while cancellation prints nothing.
  input=$(
    tofi --history=false --require-match=false --num-results=0 --height=110 \
      --prompt-text="$1 ❯ " --placeholder-text="$3 · $2" < /dev/null && printf '.'
  ) || return 1
  [[ "$input" == *$'\n.' ]] || return 1
  printf '%s' "${input%.}"
}

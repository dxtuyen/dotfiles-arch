# shellcheck shell=bash
export PATH="$HOME/.local/bin:$PATH"

# OSC 7 sets the working directory; OSC 2 sets the terminal title.
__foot_escape_uri_path() {
  local LC_ALL=C
  local path="$1" escaped="" char hex
  while [ -n "$path" ]; do
    char="${path:0:1}"
    path="${path:1}"
    case "$char" in
      [a-zA-Z0-9/._~-]) escaped+="$char" ;;
      *) printf -v hex '%%%02X' "'$char"; escaped+="$hex" ;;
    esac
  done
  __foot_osc7_path="$escaped"
}

__set_window_title() {
  [[ "$PWD" != "${__foot_last_pwd:-}" ]] || return 0
  __foot_last_pwd=$PWD
  local dir="$PWD"
  case "$dir" in
    "$HOME"|"$HOME"/*) dir="~${dir#"$HOME"}" ;;
  esac
  printf '\033]2;%s\007' "$dir"
  __foot_escape_uri_path "$PWD"
  printf '\033]7;file://%s%s\033\x5c' "${HOSTNAME:-localhost}" "$__foot_osc7_path"
}
PROMPT_COMMAND="__set_window_title${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
# Show the directory before loading completion and prompt integrations.
__set_window_title

# Open a new tmux window or Foot terminal in the current directory.
nt() {
  if [ -n "${TMUX:-}" ]; then
    tmux new-window -c "$PWD"
  else
    foot --working-directory "$PWD" >/dev/null 2>&1 &
    disown
  fi
}

# Open Yazi and change to its last directory on exit.
# Keep the final directory in the calling shell.
function y() {
  local tmp cwd
  tmp="$(mktemp -t "yazi-cwd.XXXXXX")" || return
  yazi "$@" --cwd-file="$tmp"
  if cwd="$(command cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
    builtin cd -- "$cwd" || { rm -f -- "$tmp"; return 1; }
  fi
  rm -f -- "$tmp"
}

# shellcheck shell=bash
[[ $- == *i* ]] || return
HISTCONTROL=ignoreboth:erasedups
HISTSIZE=10000
HISTFILESIZE=20000
shopt -s histappend checkwinsize
alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias ll='ls -alF'
alias vi=nvim
alias vim=nvim
alias dotfiles='/usr/bin/git --git-dir="$HOME/.dotfiles.git" --work-tree="$HOME"'
export FZF_DEFAULT_OPTS='--color=bg:#282828,fg:#d4be98,bg+:#45403d,fg+:#ddc7a1,hl:#d8a657,hl+:#d8a657,info:#89b482,prompt:#7daea3,pointer:#e78a4e,marker:#a9b665,spinner:#d3869b,header:#928374,border:#5a524c'
# shellcheck source=interactive.sh
source "$HOME/.local/lib/dotfiles/interactive.sh"
# Separate command output from the native two-line Gruvbox prompt.
PS1='\n\[\e[1;38;2;125;174;163m\]\w\[\e[0m\]\n\[\e[1;38;2;169;182;101m\]❯\[\e[0m\] '
if [[ -r /usr/share/fzf/key-bindings.bash && -r /usr/share/fzf/completion.bash ]]; then
  # Use pacman's scripts directly instead of generating and reparsing them.
  # shellcheck source=/dev/null
  source /usr/share/fzf/key-bindings.bash
  # shellcheck source=/dev/null
  source /usr/share/fzf/completion.bash
else
  command -v fzf >/dev/null && eval "$(fzf --bash)"
fi
command -v direnv >/dev/null && eval "$(direnv hook bash)"
command -v zoxide >/dev/null && eval "$(zoxide init bash)"

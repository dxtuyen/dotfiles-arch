#!/usr/bin/env bash
set -euo pipefail

config_file=${1:?missing configuration path}
theme_file=${2:?missing theme path}

mkdir -p "$(dirname "$config_file")"
if [[ -f "$config_file" ]]; then
  if [[ ! -f "$config_file.before-gruvbox-material" ]]; then
    cp -p "$config_file" "$config_file.before-gruvbox-material"
  fi
  sed -i '/^color_theme = /d; /^theme_background = /d; /^truecolor = /d' "$config_file"
fi
cat >> "$config_file" <<EOF
color_theme = "$theme_file"
theme_background = True
truecolor = True
EOF

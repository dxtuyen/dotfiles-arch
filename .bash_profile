# Login shells and greetd's user session share these defaults.
# shellcheck disable=SC1091
if [ -f "$HOME/.profile" ]; then . "$HOME/.profile"; fi
# shellcheck disable=SC1091
if [ -f "$HOME/.bashrc" ]; then . "$HOME/.bashrc"; fi

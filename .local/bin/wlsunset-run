#!/usr/bin/env bash
set -euo pipefail

case "${1:-}" in
  warm) args=(-t 3900 -T 4000) ;;
  white) args=(-t 6400 -T 6500) ;;
  natural) args=(-t 4000 -T 6500) ;;
  *) printf 'Unknown display mode: %s\n' "${1:-}" >&2; exit 2 ;;
esac

exec wlsunset "${args[@]}" -l 21.0 -L 105.8

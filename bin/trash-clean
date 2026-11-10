#!/usr/bin/env bash
# Remove trash entries older than the retention period.
set -u

# Keep 30 days by default; pass a different retention period as an argument.
KEEP_DAYS="${1:-30}"
TRASH_DIR="$HOME/.local/share/Trash"
FILES_DIR="$TRASH_DIR/files"
INFO_DIR="$TRASH_DIR/info"

[ -d "$INFO_DIR" ] || exit 0

# ISO dates sort lexically, so no date conversion is needed.
CUTOFF="$(date -d "${KEEP_DAYS} days ago" +%Y-%m-%d)"

removed=0
kept=0
for info in "$INFO_DIR"/*.trashinfo; do
  [ -e "$info" ] || continue

  # DeletionDate in .trashinfo uses ISO format.
  date="$(sed -n 's/^DeletionDate=//p' "$info" | head -1 | cut -dT -f1)"
  [ -n "$date" ] || date="$(date +%Y-%m-%d)" # Treat missing dates as recent.

  if [[ "$date" < "$CUTOFF" ]]; then
    base="${info##*/}"
    base="${base%.trashinfo}"
    # Trash entries may be directories or may already be missing.
    rm -rf -- "${FILES_DIR:?}/${base:?}" "$info" 2>/dev/null || true
    removed=$((removed + 1))
  else
    kept=$((kept + 1))
  fi
done

echo "Trash: kept $kept entries (up to $KEEP_DAYS days), removed $removed entries (before $CUTOFF)."

# Report the remaining trash size.
size="$(du -sh "$FILES_DIR" 2>/dev/null | cut -f1)"
if [ "${size:-0}" != "0" ] && [ -n "${size:-}" ]; then
  echo "Remaining trash size: $size"
fi

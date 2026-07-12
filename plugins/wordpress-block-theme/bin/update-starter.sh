#!/usr/bin/env bash
# Refresh assets/starter/ from a source block theme.
#   Class A -> copy + rewrite source slug/name to the starter's, then write.
#   Class B/C -> print a unified diff (source vs bundled); never overwrite.
# Usage: bin/update-starter.sh --source /path/to/theme
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
manifest="$repo/bin/_manifest.tsv"
starter_dir="${STARTER_DIR:-$repo/assets/starter}"

source_dir=""
while [ $# -gt 0 ]; do
  case "$1" in
    --source) source_dir="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[ -n "$source_dir" ] || { echo "usage: update-starter.sh --source <theme-dir>" >&2; exit 2; }
[ -d "$source_dir" ] || { echo "source not found: $source_dir" >&2; exit 2; }

# Derive the source theme's slug/prefix/name from its directory + style.css.
src_slug="$(basename "$source_dir")"
src_prefix="${src_slug//-/_}"
src_name="$(sed -n 's/^Theme Name:[[:space:]]*//p' "$source_dir/style.css" 2>/dev/null | head -1 || true)"
if [ -z "$src_name" ]; then
  # No style.css (or no Theme Name header): title-case the slug, e.g.
  # "editorial-calm" -> "Editorial Calm".
  src_name="$(awk -v s="$src_slug" 'BEGIN {
    n = split(s, parts, "-"); out = "";
    for (i = 1; i <= n; i++) {
      w = parts[i];
      out = out (i > 1 ? " " : "") toupper(substr(w, 1, 1)) substr(w, 2);
    }
    print out;
  }')"
fi

TARGET_SLUG="starter"
TARGET_PREFIX="starter"
TARGET_NAME="Starter Block Theme"

synced=0; diffed=0
while IFS=$'\t' read -r class starter_rel source_rel; do
  [ -n "${class:-}" ] || continue
  case "$class" in \#*) continue ;; esac
  src_file="$source_dir/$source_rel"
  dst_file="$starter_dir/$starter_rel"
  if [ ! -f "$src_file" ]; then
    echo "skip (missing in source): $source_rel"; continue
  fi
  if [ "$class" = "A" ]; then
    mkdir -p "$(dirname "$dst_file")"
    sed -e "s/${src_name}/${TARGET_NAME}/g" \
        -e "s/${src_prefix}/${TARGET_PREFIX}/g" \
        -e "s/${src_slug}/${TARGET_SLUG}/g" \
        "$src_file" > "$dst_file"
    echo "synced A: $starter_rel"
    synced=$((synced+1))
  else
    echo "=== diff ($class, review by hand): $starter_rel ==="
    diff -u "$dst_file" "$src_file" || true
    diffed=$((diffed+1))
  fi
done < "$manifest"

echo "Done: $synced Class-A synced, $diffed Class-B/C diffs printed for review."

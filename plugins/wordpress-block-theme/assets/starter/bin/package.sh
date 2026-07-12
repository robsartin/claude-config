#!/usr/bin/env bash
# Build a clean, uploadable theme zip: <slug>.zip containing a single
# top-level <slug>/ folder, dev-only files excluded.
set -euo pipefail
cd "$(dirname "$0")/.."          # theme root
SLUG="$(basename "$PWD")"
PARENT="$(dirname "$PWD")"
OUT="${PARENT}/${SLUG}.zip"
rm -f "$OUT"

# Gate before packaging so we never ship a broken build.
./bin/check-all.sh >/dev/null

( cd "$PARENT" && zip -r -X "$OUT" "$SLUG" \
    -x "${SLUG}/bin/*" \
    -x "${SLUG}/node_modules/*" \
    -x "${SLUG}/.wp-env.json" \
    -x "${SLUG}/phpcs.xml" \
    -x '*/.DS_Store' -x '*.map' -x '__MACOSX/*' >/dev/null )

echo "Wrote $OUT ($(du -h "$OUT" | cut -f1))"
echo "style.css at theme root ->" \
  "$(unzip -l "$OUT" | grep -c "${SLUG}/style.css") (expect 1)"

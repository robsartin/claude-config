#!/usr/bin/env bash
#
# Best-effort homepage screenshot capture against a running wp-env site.
#
# Requires Docker (wp-env) and Google Chrome. Drives the system-installed
# Chrome in headless mode directly — no npm, no node_modules, no bundled
# Chromium download. The Chrome binary defaults to the standard macOS path
# but honours PUPPETEER_EXECUTABLE_PATH as an override, for consistency with
# the sibling check-a11y.sh script:
#   PUPPETEER_EXECUTABLE_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# Adjust PUPPETEER_EXECUTABLE_PATH if Chrome lives elsewhere on your machine.
#
# This captures the homepage with whatever minimal seeded content exists in
# the local wp-env database (real content if you've added it, a couple of
# generated placeholder posts otherwise). Treat the result as a BEST-EFFORT
# starting point only — review it and replace it with a curated, hand-picked
# 1200x900 capture before a real launch.
#
# What it does:
#   1. Starts wp-env if it isn't already running, and makes sure the theme
#      is the active theme.
#   2. Seeds a couple of posts if the site has none yet, so the homepage
#      isn't completely empty.
#   3. Runs headless Chrome against the homepage and writes a 1200x900 PNG
#      to screenshot.png at the theme root.
#
# Usage: ./bin/screenshot.sh
set -euo pipefail

CHROME="${PUPPETEER_EXECUTABLE_PATH:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"

cd "$(dirname "$0")/.."          # theme root
SLUG="$(basename "$PWD")"

base_url="http://localhost:8888"

echo "== Ensuring wp-env is running =="
if ! npx @wordpress/env run cli wp core is-installed >/dev/null 2>&1; then
  npx @wordpress/env start
fi

echo "== Ensuring the theme is the active theme =="
active_theme="$(npx @wordpress/env run cli wp theme list --status=active --field=name --format=csv 2>/dev/null | tail -1 | tr -d '\r')"
if [ "$active_theme" != "$SLUG" ]; then
  npx @wordpress/env run cli wp theme activate "$SLUG"
fi

echo "== Ensuring at least one published post exists =="
post_count="$(npx @wordpress/env run cli wp post list --post_type=post --post_status=publish --format=count 2>/dev/null | tail -1 | tr -d '\r')"
if [ "${post_count:-0}" -eq 0 ]; then
  npx @wordpress/env run cli wp post generate --post_type=post --post_status=publish --count=2
fi

echo "== Capturing homepage screenshot (1200x900) =="
out="$PWD/screenshot.png"
rm -f "$out"
"$CHROME" --headless=new --hide-scrollbars --force-device-scale-factor=1 \
  --window-size=1200,900 --virtual-time-budget=5000 \
  --run-all-compositor-stages-before-draw \
  --screenshot="$out" "$base_url/"

# Fail loudly if Chrome produced nothing usable.
if [ ! -s "$out" ]; then
  echo "screenshot.sh: capture failed — $out is missing or empty" >&2
  exit 1
fi

# Guard: if the capture isn't exactly 1200x900, crop to size with sips
# (macOS only; a no-op / skipped elsewhere). sips -c takes HEIGHT then WIDTH.
if ! file "$out" | grep -q '1200 x 900'; then
  if command -v sips >/dev/null 2>&1; then
    echo "screenshot.sh: capture not 1200x900 — cropping with sips"
    sips -c 900 1200 "$out" >/dev/null
  else
    echo "screenshot.sh: capture not 1200x900 and sips unavailable to crop" >&2
    exit 1
  fi
fi

echo "screenshot.sh: wrote $out"
file "$out"

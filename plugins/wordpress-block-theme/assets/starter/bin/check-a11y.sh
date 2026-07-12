#!/usr/bin/env bash
#
# Automated accessibility scan (pa11y, WCAG2AA) against a running wp-env site.
#
# Requires Docker (wp-env) and Node 20+. Uses the system-installed Google
# Chrome instead of downloading a bundled Chromium, via:
#   PUPPETEER_SKIP_DOWNLOAD=1
#   PUPPETEER_EXECUTABLE_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# Adjust PUPPETEER_EXECUTABLE_PATH if Chrome lives elsewhere on your machine.
#
# What it does:
#   1. Starts wp-env if it isn't already running, and makes sure the theme
#      is the active theme.
#   2. Seeds a couple of posts if the site has none yet, so the "single post"
#      scan has something to hit.
#   3. Runs `npx -y pa11y --standard WCAG2AA` against:
#        - the homepage (`/`)
#        - a single published post
#        - a bogus/nonexistent URL (exercises the 404 template)
#      pa11y itself exits non-zero when it finds issues, so `set -e` below is
#      enough to fail the script on the first URL with problems.
#
# This script only scans whichever style is currently baked into theme.json
# (the shipped default is theme.json's own base `styles`). To scan a style
# variation instead (e.g. styles/example.json):
#   1. Copy that variation's `settings.color.palette` and top-level `styles`
#      blocks into theme.json, temporarily overriding the base values.
#   2. `npx @wordpress/env run cli wp cache flush`
#   3. Re-run this script (or just the pa11y commands below).
#   4. Restore the original file: `git checkout theme.json`
#      (do NOT commit the temporary merge).
#
# Usage: ./bin/check-a11y.sh
set -euo pipefail

export PUPPETEER_SKIP_DOWNLOAD=1
export PUPPETEER_EXECUTABLE_PATH="${PUPPETEER_EXECUTABLE_PATH:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"

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

single_post_url="$(npx @wordpress/env run cli wp post list --post_type=post --post_status=publish --field=url --posts_per_page=1 2>/dev/null | tail -1 | tr -d '\r')"
if [ -z "$single_post_url" ]; then
  echo "check-a11y.sh: could not resolve a published post URL to scan" >&2
  exit 1
fi

echo "== Running pa11y (WCAG2AA) =="
echo "-- homepage --"
npx -y pa11y --standard WCAG2AA --timeout 60000 "$base_url/"

echo "-- single post: $single_post_url --"
npx -y pa11y --standard WCAG2AA --timeout 60000 "$single_post_url"

echo "-- 404: bogus URL --"
npx -y pa11y --standard WCAG2AA --timeout 60000 "$base_url/this-page-does-not-exist-xyz/"

echo "check-a11y.sh: pa11y found no issues on any scanned URL."

#!/usr/bin/env bash
# Run the Theme Check plugin against this theme, headlessly, inside wp-env.
# The Theme Check build ships no WP-CLI command, so we drive its engine via
# `wp eval-file` against bin/theme-check-run.php.
set -euo pipefail
cd "$(dirname "$0")/.."          # theme root
SLUG="$(basename "$PWD")"
PLUGIN_SLUG="theme-check.latest-stable"
HARNESS="wp-content/themes/${SLUG}/bin/theme-check-run.php"

echo "Ensuring wp-env is running..."
npx @wordpress/env start >/dev/null
if ! npx @wordpress/env run cli wp plugin is-active "$PLUGIN_SLUG" >/dev/null 2>&1; then
  npx @wordpress/env start --update
  npx @wordpress/env run cli wp plugin activate "$PLUGIN_SLUG" || true
fi
npx @wordpress/env run cli wp eval-file "$HARNESS"

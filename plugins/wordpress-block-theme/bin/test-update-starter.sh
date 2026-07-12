#!/usr/bin/env bash
# Smoke test for update-starter.sh using a tiny fake source theme.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(dirname "$here")"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Fake source theme named "editorial-calm" with one Class A file to sync.
src="$tmp/editorial-calm"
mkdir -p "$src/bin"
printf 'slug: editorial-calm\nfn: editorial_calm_x\nname: Editorial Calm\n' > "$src/bin/_wcag.py"

# Run sync into a throwaway starter dir.
dest="$tmp/starter"
mkdir -p "$dest/bin"
STARTER_DIR="$dest" bash "$here/update-starter.sh" --source "$src" >/dev/null

# Class A file must exist with the slug rewritten.
out="$dest/bin/_wcag.py"
grep -q 'slug: starter' "$out" || { echo "FAIL: slug not rewritten"; exit 1; }
grep -q 'fn: starter_x' "$out" || { echo "FAIL: php prefix not rewritten"; exit 1; }
grep -q 'name: Starter Block Theme' "$out" || { echo "FAIL: display name not rewritten"; exit 1; }
grep -q 'editorial' "$out" && { echo "FAIL: source slug leaked"; exit 1; }
echo "PASS: update-starter smoke test"

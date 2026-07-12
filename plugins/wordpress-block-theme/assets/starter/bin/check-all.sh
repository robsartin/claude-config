#!/usr/bin/env bash
# Aggregate static gates that need no Docker. Fails on the first failure.
set -euo pipefail
here="$(dirname "$0")"
python3 "$here/validate-theme-json.py"
python3 "$here/check-font-fallbacks.py"
python3 "$here/check-contrast.py"
python3 "$here/check-button-contrast.py"
for v in "$here/../styles/"*.json; do
  [ -e "$v" ] || continue
  python3 "$here/check-contrast.py" "$v"
  python3 "$here/check-button-contrast.py" "$v"
done
python3 "$here/check-templates.py"
python3 "$here/check-patterns.py"
python3 "$here/check-markup-consistency.py"
python3 "$here/check-frontpage.py"
echo "All static gates passed."

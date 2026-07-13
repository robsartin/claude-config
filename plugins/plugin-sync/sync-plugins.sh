#!/usr/bin/env bash
#
# sync-plugins.sh — keep this machine's installed plugins in sync with the
# claude-config marketplace.
#
#   - installs any plugin that is in the marketplace but not yet installed
#   - updates every claude-config plugin that IS installed
#   - reports plugins that are installed from claude-config but no longer in
#     the marketplace ("orphaned") — and, with --prune, uninstalls them
#
# The plugin list is read from the marketplace catalog itself (after a refresh),
# so new/removed plugins are picked up automatically — nothing is hard-coded.
#
# Usage:
#   sync-plugins.sh            # install new + update installed; report orphans
#   sync-plugins.sh --prune    # also uninstall orphaned claude-config plugins
#   sync-plugins.sh --dry-run  # print what would happen; change nothing
#
# Written for bash 3.2 (macOS system bash) — no arrays-under-set-u, no jq.

set -euo pipefail

MARKETPLACE="claude-config"
PRUNE=false
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --prune)   PRUNE=true ;;
    --dry-run) DRY_RUN=true ;;
    -h|--help)
      grep '^#' "$0" | grep -v '^#!' | sed 's/^# \{0,1\}//; s/^#//'
      exit 0 ;;
    *)
      echo "unknown argument: $arg (try --help)" >&2
      exit 2 ;;
  esac
done

CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
CATALOG="$CONFIG_DIR/plugins/marketplaces/$MARKETPLACE/.claude-plugin/marketplace.json"

# Echo a command, then run it unless --dry-run.
run() {
  echo "  \$ $*"
  if ! $DRY_RUN; then "$@"; fi
}

# --- 1. Refresh the catalog from its source (GitHub) -------------------------

echo "Refreshing marketplace '$MARKETPLACE'..."
if ! claude plugin marketplace update "$MARKETPLACE" >/dev/null 2>&1; then
  echo "ERROR: could not update marketplace '$MARKETPLACE'." >&2
  echo "Is it registered? Add it with:" >&2
  echo "  claude plugin marketplace add robsartin/$MARKETPLACE" >&2
  exit 1
fi

if [ ! -f "$CATALOG" ]; then
  echo "ERROR: marketplace catalog not found at:" >&2
  echo "  $CATALOG" >&2
  exit 1
fi

# --- 2. Desired (from catalog) vs installed (from the CLI) --------------------

# Desired: every plugin name declared in the marketplace catalog.
desired=$(python3 -c "
import json
with open('$CATALOG') as f:
    print('\n'.join(p['name'] for p in json.load(f).get('plugins', [])))
")

# Installed: names of plugins currently installed FROM this marketplace
# (claude plugin list --json ids look like 'name@marketplace').
installed=$(claude plugin list --json 2>/dev/null | python3 -c "
import json, sys
sfx = '@$MARKETPLACE'
data = json.load(sys.stdin)
print('\n'.join(p['id'][:-len(sfx)] for p in data if str(p.get('id','')).endswith(sfx)))
")

# --- 3. Diff the two sets ----------------------------------------------------

new_list=""       # desired, not installed
existing_list=""  # desired, installed
orphaned_list=""  # installed from this marketplace, no longer desired

while IFS= read -r name; do
  [ -z "$name" ] && continue
  if printf '%s\n' "$installed" | grep -qxF "$name"; then
    existing_list="${existing_list}${name}"$'\n'
  else
    new_list="${new_list}${name}"$'\n'
  fi
done <<< "$desired"

while IFS= read -r name; do
  [ -z "$name" ] && continue
  printf '%s\n' "$desired" | grep -qxF "$name" || orphaned_list="${orphaned_list}${name}"$'\n'
done <<< "$installed"

count() { printf '%s' "$1" | grep -c . || true; }

echo "Marketplace '$MARKETPLACE': $(count "$new_list") new, $(count "$existing_list") to update, $(count "$orphaned_list") orphaned."
$DRY_RUN && echo "(dry run — no changes will be made)"

# --- 4. Act ------------------------------------------------------------------

did_something=false

if [ -n "$(printf '%s' "$new_list" | tr -d '[:space:]')" ]; then
  echo "Installing new plugins:"
  while IFS= read -r name; do
    [ -z "$name" ] && continue
    run claude plugin install "$name@$MARKETPLACE"
    did_something=true
  done <<< "$new_list"
fi

if [ -n "$(printf '%s' "$existing_list" | tr -d '[:space:]')" ]; then
  echo "Updating installed plugins:"
  while IFS= read -r name; do
    [ -z "$name" ] && continue
    run claude plugin update "$name@$MARKETPLACE"
    did_something=true
  done <<< "$existing_list"
fi

if [ -n "$(printf '%s' "$orphaned_list" | tr -d '[:space:]')" ]; then
  if $PRUNE; then
    echo "Pruning orphaned plugins (no longer in '$MARKETPLACE'):"
    while IFS= read -r name; do
      [ -z "$name" ] && continue
      run claude plugin uninstall "$name@$MARKETPLACE"
      did_something=true
    done <<< "$orphaned_list"
  else
    echo "Orphaned — installed from '$MARKETPLACE' but no longer in its catalog:"
    while IFS= read -r name; do
      [ -z "$name" ] && continue
      echo "  ! $name — remove with: claude plugin uninstall $name@$MARKETPLACE   (or re-run with --prune)"
    done <<< "$orphaned_list"
  fi
fi

# --- 5. Wrap up --------------------------------------------------------------

if $DRY_RUN; then
  echo "Dry run complete."
elif $did_something; then
  echo "Done. Restart Claude Code to apply the changes."
else
  echo "Everything already in sync."
fi

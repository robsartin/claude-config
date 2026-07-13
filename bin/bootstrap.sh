#!/usr/bin/env bash
#
# bootstrap.sh — set up claude-config on a fresh machine.
#
#   1. adds the claude-config marketplace
#   2. installs / updates all of its plugins (delegates to plugin-sync's script,
#      which reads the marketplace catalog — so this stays current automatically)
#   3. runs the adr-toolkit Python engine bootstrap (best-effort)
#   4. with --extras, also re-adds the external marketplaces + plugins used
#      elsewhere (superpowers, frontend-design, claude-hud)
#
# Run it from a clone of the repo:
#   git clone https://github.com/robsartin/claude-config
#   claude-config/bin/bootstrap.sh [--extras] [--dry-run]
#
# What this does NOT set up (machine-local, not in the marketplace):
#   ~/.claude/settings.json, the claude-hud statusline config, keybindings,
#   and your memory (~/.claude/projects/.../memory/).
#
# Written for bash 3.2 (macOS system bash) — no jq.

set -euo pipefail

WITH_EXTRAS=false
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --extras)  WITH_EXTRAS=true ;;
    --dry-run) DRY_RUN=true ;;
    -h|--help)
      grep '^#' "$0" | grep -v '^#!' | sed 's/^# \{0,1\}//; s/^#//'
      exit 0 ;;
    *)
      echo "unknown argument: $arg (try --help)" >&2
      exit 2 ;;
  esac
done

# This script lives at <repo>/bin/bootstrap.sh
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(dirname "$here")"
SYNC="$repo/plugins/plugin-sync/sync-plugins.sh"
CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

command -v claude >/dev/null 2>&1 || {
  echo "ERROR: the 'claude' CLI was not found. Install Claude Code first." >&2
  exit 1
}

# add_marketplace <github-repo-slug>   — tolerant of an already-added marketplace
add_marketplace() {
  echo "  \$ claude plugin marketplace add $1"
  $DRY_RUN && return 0
  claude plugin marketplace add "$1" >/dev/null 2>&1 \
    || echo "    (already added or unavailable — continuing)"
}

# install_plugin <plugin@marketplace>
install_plugin() {
  echo "  \$ claude plugin install $1"
  $DRY_RUN && return 0
  claude plugin install "$1" || echo "    (install failed — continuing)"
}

echo "==> claude-config marketplace"
add_marketplace "robsartin/claude-config"

echo "==> installing / updating all claude-config plugins"
if [ ! -f "$SYNC" ]; then
  echo "ERROR: sync script not found at $SYNC — run bootstrap from a full clone of the repo." >&2
  exit 1
fi
if $DRY_RUN; then
  bash "$SYNC" --dry-run
else
  bash "$SYNC"
fi

echo "==> adr-toolkit Python engine"
adr_install=$(ls -d "$CONFIG_DIR"/plugins/cache/claude-config/adr-toolkit/*/bin/install.sh 2>/dev/null | tail -1 || true)
if [ -z "$adr_install" ]; then
  echo "  adr-toolkit not installed yet — skipping (re-run after the plugins install)."
elif ! command -v python3 >/dev/null 2>&1; then
  echo "  python3 not found — skipping. Install python3, then run: $adr_install"
else
  echo "  \$ $adr_install"
  $DRY_RUN || bash "$adr_install" || echo "    (adr engine bootstrap failed — run it manually later)"
fi

if $WITH_EXTRAS; then
  echo "==> external marketplaces + plugins (--extras)"
  add_marketplace "anthropics/claude-plugins-official"
  add_marketplace "jarrodwatts/claude-hud"
  install_plugin "superpowers@claude-plugins-official"
  install_plugin "frontend-design@claude-plugins-official"
  install_plugin "claude-hud@claude-hud"
fi

echo ""
if $DRY_RUN; then
  echo "Dry run complete — nothing was changed."
else
  echo "Bootstrap complete. Restart Claude Code to load everything."
fi
$WITH_EXTRAS || echo "(Tip: re-run with --extras to also set up superpowers, frontend-design, and claude-hud.)"

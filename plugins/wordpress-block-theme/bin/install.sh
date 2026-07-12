#!/usr/bin/env bash
# Install this skill into the user's personal Claude skills directory.
#   Default: symlink DEST -> this repo (edits + `git pull` are live immediately).
#   --clone: `git clone` a fresh copy into DEST instead of symlinking.
# Idempotent: re-running with the same target reports "already installed".
# Usage: bin/install.sh [--clone] [--force] [--help]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
GIT_URL="https://github.com/robsartin/claude-wp-theme-skill.git"

mode="symlink"
force=0
while [ $# -gt 0 ]; do
  case "$1" in
    --clone) mode="clone"; shift ;;
    --force) force=1; shift ;;
    -h|--help)
      sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}/wordpress-block-theme"
SKILLS_DIR="$(dirname "$DEST")"

mkdir -p "$SKILLS_DIR"

# Already installed as a symlink pointing at this repo -> nothing to do.
# (We always create the symlink with an absolute target, so a plain
# `readlink` comparison is sufficient - no need to resolve relative links.)
if [ -L "$DEST" ] && [ "$(readlink "$DEST")" = "$REPO" ]; then
  echo "already installed: $DEST -> $REPO"
  exit 0
fi

if [ -e "$DEST" ] || [ -L "$DEST" ]; then
  if [ "$force" -ne 1 ]; then
    echo "refusing to overwrite existing path: $DEST" >&2
    echo "(it is not a symlink to this repo; pass --force to replace it)" >&2
    exit 1
  fi
  # Guard the rm: only ever remove a symlink or a real directory, never
  # anything else that might live at DEST.
  if [ -L "$DEST" ] || [ -d "$DEST" ]; then
    rm -rf "$DEST"
  else
    echo "refusing to remove unexpected non-directory, non-symlink path: $DEST" >&2
    exit 1
  fi
fi

if [ "$mode" = "clone" ]; then
  git clone "$GIT_URL" "$DEST"
else
  ln -s "$REPO" "$DEST"
fi

echo "installed: $DEST"
echo "Restart Claude Code; the skill triggers on WordPress/block-theme requests, or invoke it as /wordpress-block-theme."

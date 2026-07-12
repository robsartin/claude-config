#!/usr/bin/env bash
#
# Install the adr-toolkit engine and register it as a Claude skill.
# Idempotent: safe to re-run. Run from anywhere:
#
#     ./bin/install.sh
#
set -euo pipefail

SKILL_NAME="adr-toolkit"  # must match the `name:` in SKILL.md frontmatter
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="${HOME}/.claude/skills"
VENV="${REPO_ROOT}/.venv"

# --- 1. Python engine (editable install into the repo's venv) ------------------
PYTHON="$(command -v python3.12 || command -v python3 || true)"
if [ -z "${PYTHON}" ]; then
  echo "error: python3.12 (or python3) not found on PATH" >&2
  exit 1
fi

if [ ! -d "${VENV}" ]; then
  echo "creating venv at ${VENV}"
  "${PYTHON}" -m venv "${VENV}"
fi

echo "installing adr-toolkit (editable) ..."
"${VENV}/bin/pip" install --quiet --upgrade pip
"${VENV}/bin/pip" install --quiet -e "${REPO_ROOT}[dev]"

# --- 2. Register as a Claude skill (symlink) -----------------------------------
mkdir -p "${SKILLS_DIR}"
LINK="${SKILLS_DIR}/${SKILL_NAME}"

if [ -L "${LINK}" ]; then
  if [ "$(readlink "${LINK}")" = "${REPO_ROOT}" ]; then
    echo "skill already linked: ${LINK} -> ${REPO_ROOT}"
  else
    echo "warning: ${LINK} points elsewhere ($(readlink "${LINK}"))." >&2
    echo "         remove it and re-run to relink." >&2
  fi
elif [ -e "${LINK}" ]; then
  echo "warning: ${LINK} exists and is not a symlink; leaving it untouched." >&2
else
  ln -s "${REPO_ROOT}" "${LINK}"
  echo "linked skill: ${LINK} -> ${REPO_ROOT}"
fi

echo
echo "done."
echo "  CLI:   ${VENV}/bin/adr-toolkit"
echo "  skill: restart Claude Code to pick up '${SKILL_NAME}'."

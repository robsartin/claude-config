#!/usr/bin/env bash
#
# Install the adr-toolkit engine (venv + editable package install).
# Idempotent: safe to re-run. Run from anywhere:
#
#     ./bin/install.sh
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${REPO_ROOT}/.venv"

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

echo
echo "done."
echo "  CLI: ${VENV}/bin/adr-toolkit"

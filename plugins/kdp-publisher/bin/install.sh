#!/usr/bin/env bash
#
# Install the kdp-publisher engine (venv + editable package install).
# Idempotent: safe to re-run. Run from anywhere:
#
#     ./bin/install.sh
#
# NOTE: WeasyPrint (the interior re-render engine) needs native libraries.
#   macOS:  brew install pango gdk-pixbuf libffi
#   Debian: apt-get install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev
# If `python -m kdp_publisher` errors on a missing libpango/gobject, install those first.
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

echo "installing kdp-publisher (editable) ..."
"${VENV}/bin/pip" install --quiet --upgrade pip
"${VENV}/bin/pip" install --quiet -e "${REPO_ROOT}[dev]"

echo
echo "done."
echo "  CLI: ${VENV}/bin/kdp-publisher"
echo "  or:  ${VENV}/bin/python -m kdp_publisher"

#!/usr/bin/env bash
#
# Regenerate the sample ADR sets under examples/ from the current packs.
# Deterministic (fixed date), so re-running only changes files when the packs
# change. CI runs this and fails if examples/ is out of date.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ADR="$(command -v adr-toolkit || echo "${ROOT}/.venv/bin/adr-toolkit")"
DATE="2026-07-08"
EXAMPLES="${ROOT}/examples"

gen() {
  local name="$1"
  shift
  local args=()
  for p in "$@"; do args+=(--pack "$p"); done
  rm -rf "${EXAMPLES:?}/${name}"
  "${ADR}" \
    --manifest "${ROOT}/packs.yaml" --packs-dir "${ROOT}/packs" \
    --target "${EXAMPLES}/${name}/docs/adr" \
    --project "${name}" --date "${DATE}" \
    --pack universal "${args[@]}" >/dev/null
  echo "generated examples/${name}  ($*)"
}

# name                  packs (universal is always added)
gen orders-service      kotlin spring-boot service observability
gen recipes-web         react web-frontend d3 i18n
gen feed-cli            python cli
gen dashboard-web       plain-js d3
gen desktop-app         native-ui compose
gen ledger-service      java spring-boot service observability privacy

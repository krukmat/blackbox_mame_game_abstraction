#!/usr/bin/env bash
# T30.2 — Launch MAME with address_search.lua for guided RAM address discovery.
# Sets the private exchange file paths and launches MAME.
# Usage: ./scripts/launch_address_search.sh [run_id]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Load .env line-by-line (values may contain spaces, e.g. iCloud ROM paths, which a
# plain `source` mis-parses).
ENV_FILE="${REPO_ROOT}/.env"
if [[ -f "${ENV_FILE}" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    export "$line" 2>/dev/null || true
  done < "${ENV_FILE}"
fi

MAME_BINARY="${BLACKBOX_MAME_BINARY:-mame}"
ROM_PATH="${BLACKBOX_ROM_PATH:-}"
MAME_DRIVER="${BLACKBOX_MAME_DRIVER:-gngb}"
SAVESTATE_PATH="${BLACKBOX_SAVESTATE_PATH:-}"

if [[ -z "${ROM_PATH}" ]]; then
  echo "ERROR: BLACKBOX_ROM_PATH not set in .env" >&2
  exit 1
fi

# Deterministic start: if a controllable savestate anchor exists, install it as a MAME
# state slot ("anchor"). The Lua script loads it a few frames in (via machine:load),
# which avoids the -state flag's reset-notifier loop (ADR-028 savestate anchor).
if [[ -n "${SAVESTATE_PATH}" && -f "${REPO_ROOT}/${SAVESTATE_PATH}" ]]; then
  SLOT_DIR="${REPO_ROOT}/sta/${MAME_DRIVER}"
  mkdir -p "${SLOT_DIR}"
  cp "${REPO_ROOT}/${SAVESTATE_PATH}" "${SLOT_DIR}/anchor.sta"
  export BLACKBOX_ADDR_ANCHOR_SLOT="anchor"
  echo "Savestate anchor installed from ${SAVESTATE_PATH} (slot: anchor, loaded by Lua)"
fi

RUN_ID="${1:-addr_search_01}"
PRIVATE_DIR="${REPO_ROOT}/evidence/private/addr_search/${RUN_ID}"
mkdir -p "${PRIVATE_DIR}"

SNAPSHOT_PATH="${PRIVATE_DIR}/ram_snapshot.bin"
CMD_PATH="${PRIVATE_DIR}/cmd.txt"
touch "${CMD_PATH}"

export BLACKBOX_ADDR_SNAPSHOT_PATH="${SNAPSHOT_PATH}"
export BLACKBOX_ADDR_CMD_PATH="${CMD_PATH}"

echo "Address search session: ${RUN_ID}"
echo "Snapshot: ${SNAPSHOT_PATH}"
echo "CMD:      ${CMD_PATH}"
echo ""
echo "In a separate terminal, run:"
echo "  apps/mame-harness/.venv/bin/python apps/mame-harness/address_search.py \\"
echo "    --snapshot ${SNAPSHOT_PATH} \\"
echo "    --cmd ${CMD_PATH} \\"
echo "    --out evidence/private/gng_address_candidates.json"
echo ""
echo "Launching MAME..."

"${MAME_BINARY}" "${MAME_DRIVER}" \
  -rompath "${ROM_PATH}" \
  -autoboot_script "${SCRIPT_DIR}/address_search.lua" \
  "$@" || true

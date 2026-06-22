#!/usr/bin/env bash
# create_savestate.sh
#
# Launch MAME with autosave enabled. When the user closes MAME (at any point
# after Arthur is controllable), MAME writes ./sta/gngb/gngb.sta automatically.
# This script then copies that file to the canonical private savestate path.
#
# USAGE:
#   ./scripts/create_savestate.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "${ROOT}/.env" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    # Skip comments and empty lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    export "$line" 2>/dev/null || true
  done < "${ROOT}/.env"
fi

VENV="${ROOT}/apps/mame-harness/.venv/bin/python"
MAME_BINARY="${BLACKBOX_MAME_BINARY:-mame}"
ROM_PATH="${BLACKBOX_ROM_PATH:-}"
MAME_DRIVER="${BLACKBOX_MAME_DRIVER:-gngb}"
BOOT_PLAN="${BLACKBOX_BOOT_PLAN:-plans/generated/gng_boot_only.yaml}"
SAVESTATE_DIR="${ROOT}/sta/${MAME_DRIVER}"
SAVESTATE_SRC="${SAVESTATE_DIR}/auto.sta"
SAVESTATE_DST="${ROOT}/evidence/private/savestates/gng_controllable.sta"
LOGS_DIR="${ROOT}/evidence/private/savestates"

# Temp input plan for boot injection
TMP_PLAN_JSON="$(mktemp /tmp/savestate_input_plan_XXXXXX.json)"
trap 'rm -f "${TMP_PLAN_JSON}"' EXIT

if [ -z "${ROM_PATH}" ]; then
  echo "ERROR: BLACKBOX_ROM_PATH not set. Copy .env.example to .env and fill in ROM path."
  exit 1
fi

mkdir -p "${LOGS_DIR}"
mkdir -p "${SAVESTATE_DIR}"

echo "Exporting boot plan to JSON for autoboot..."
"${VENV}" - <<EOF
import sys
sys.path.insert(0, '${ROOT}/apps/mame-harness')
from pathlib import Path
from input_planner import load_input_plan
plan = load_input_plan(Path('${ROOT}/${BOOT_PLAN}'))
plan.export_to_json(Path('${TMP_PLAN_JSON}'))
print("  Boot plan exported.")
print("  Arthur controllable from frame ~1505 (~25 seconds).")
EOF

echo ""
echo "Launching MAME with autosave enabled."
echo ""
echo "  Boot is automatic (~25 seconds)."
echo "  When Arthur appears: play a few seconds, then CLOSE the window."
echo "  MAME will save state automatically on close."
echo ""

export BLACKBOX_INPUT_PLAN_PATH="${TMP_PLAN_JSON}"

"${MAME_BINARY}" "${MAME_DRIVER}" \
  -rompath "${ROM_PATH}" \
  -autosave \
  -autoboot_script "${ROOT}/scripts/mame_autoboot.lua"

echo ""
echo "MAME closed. Checking for autosave..."

if [ ! -f "${SAVESTATE_SRC}" ]; then
  echo "ERROR: Savestate not found at ${SAVESTATE_SRC}"
  echo "MAME may not have written it. Try again and close MAME after Arthur appears."
  exit 1
fi

cp "${SAVESTATE_SRC}" "${SAVESTATE_DST}"
echo "Savestate copied to: evidence/private/savestates/gng_controllable.sta"
ls -lh "${SAVESTATE_DST}"

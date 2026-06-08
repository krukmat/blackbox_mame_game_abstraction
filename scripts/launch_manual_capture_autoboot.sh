#!/usr/bin/env bash
# launch_manual_capture_autoboot.sh
#
# PURPOSE:
#   Launch MAME with automated boot (coin insert + start) via Lua input injection.
#   After frame ~1505 Arthur is controllable — the user plays freely from there.
#   MAME records an AVI for the entire session. No time limit — user closes when done.
#
# USAGE:
#   ./scripts/launch_manual_capture_autoboot.sh [run_id]
#   Default run_id: manual_01
#
# WHAT THIS DOES:
#   1. Exports plans/generated/gng_boot_only.yaml to a temporary JSON (Lua reads this)
#   2. Creates evidence/private/run_<id>/ directory layout
#   3. Launches MAME with -autoboot_script pointing to mame_autoboot.lua
#   4. The Lua script injects coin + start inputs at the correct frames
#   5. After frame 1505, noop frames mean the user's keyboard takes over
#   6. MAME records everything to capture.avi — blocks until user closes window
#
# AFTER THIS SCRIPT RETURNS:
#   Run: ./scripts/extract_frames.sh [run_id]
#
# CONTROLS (once Arthur is controllable, ~25s after launch):
#   ← →        Move left / right
#   Option      Jump
#   Control     Fire / attack
#   Esc         Quit MAME (ends recording)
#
set -euo pipefail

RUN_ID="${1:-manual_01}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "${ROOT}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "${ROOT}/.env"
  set +a
fi

VENV="${ROOT}/apps/mame-harness/.venv/bin/python"
MAME_BINARY="${BLACKBOX_MAME_BINARY:-mame}"
ROM_PATH="${BLACKBOX_ROM_PATH:-}"
MAME_DRIVER="${BLACKBOX_MAME_DRIVER:-gngb}"
BOOT_PLAN="${BLACKBOX_BOOT_PLAN:-plans/generated/gng_boot_only.yaml}"
REL_EVIDENCE_ROOT="${BLACKBOX_EVIDENCE_ROOT:-evidence/private}"
REL_EVIDENCE_ROOT="${REL_EVIDENCE_ROOT#./}"

case "${REL_EVIDENCE_ROOT}" in
  evidence/private|evidence/private/*) ;;
  *)
    echo "ERROR: BLACKBOX_EVIDENCE_ROOT must stay under evidence/private."
    exit 1
    ;;
esac

if [ -z "${ROM_PATH}" ]; then
  echo "ERROR: BLACKBOX_ROM_PATH is not configured. Copy .env.example to .env and set your private ROM directory first."
  exit 1
fi

EVIDENCE_DIR="${ROOT}/${REL_EVIDENCE_ROOT}/run_${RUN_ID}"
AVI_PATH="${EVIDENCE_DIR}/video/capture.avi"
FRAMES_DIR="${EVIDENCE_DIR}/frames"
LOGS_DIR="${EVIDENCE_DIR}/logs"
INPUT_PLAN_JSON="${LOGS_DIR}/input_plan.json"
INPUT_TIMELINE_JSON="${LOGS_DIR}/input_timeline.json"  # T20.1: ground-truth input timeline (ADR-023)
# T20.5 / ADR-026: optional RAM memory tap. Local YAML address map (gitignored) → private JSON.
MEMORY_MAP_YAML="${BLACKBOX_MEMORY_MAP_YAML:-${ROOT}/blackbox.local.memory_map.yaml}"
MEMORY_MAP_JSON="${LOGS_DIR}/memory_map.json"
STATE_TIMELINE_JSON="${LOGS_DIR}/state_timeline.json"
DISPLAY_AVI_PATH="${REL_EVIDENCE_ROOT}/run_${RUN_ID}/video/capture.avi"

# --- Setup ---
mkdir -p "${EVIDENCE_DIR}/video"
mkdir -p "${FRAMES_DIR}/extracted_png"
mkdir -p "${LOGS_DIR}"

# --- Export boot plan to JSON for Lua ---
echo "Exporting boot plan to JSON..."
"${VENV}" - <<EOF
import sys
sys.path.insert(0, '${ROOT}/apps/mame-harness')
from pathlib import Path
from input_planner import load_input_plan
plan = load_input_plan(Path('${ROOT}/${BOOT_PLAN}'))
plan.export_to_json(Path('${INPUT_PLAN_JSON}'))
print(f"  Input plan exported: ${INPUT_PLAN_JSON}")
frames = plan.expand_to_frames()
coin_frame = next((f.frame_index for f in frames if f.action == 'insert_coin'), None)
start_frame = next((f.frame_index for f in frames if f.action == 'press_start'), None)
print(f"  Coin insert at frame: {coin_frame}")
print(f"  Press start at frame: {start_frame}")
print(f"  Arthur controllable from frame: ~1505 (~25s)")
EOF

# --- Launch MAME ---
echo ""
echo "Launching MAME — run_id: ${RUN_ID}"
echo ""
echo "  The boot sequence runs automatically (~25 seconds):"
echo "    Frame    0: MAME starts, RAM/ROM check begins"
echo "    Frame  950: coin inserted automatically"
echo "    Frame 1025: 1P start pressed automatically"
echo "    Frame 1505: Arthur is controllable — YOU play from here"
echo ""
echo "  Controls:"
echo "    ← →        Move"
echo "    Option      Jump"
echo "    Control     Fire"
echo "    Esc         Quit (ends recording)"
echo ""
echo "  Recording to: ${DISPLAY_AVI_PATH}"
echo ""

# T20.5 / ADR-026: convert the local YAML address map to a private JSON the Lua reads.
# Absent file = no memory tap (graceful; vision fallback). Addresses stay private.
export BLACKBOX_INPUT_PLAN_PATH="${INPUT_PLAN_JSON}"
export BLACKBOX_INPUT_TIMELINE_PATH="${INPUT_TIMELINE_JSON}"
if [ -f "${MEMORY_MAP_YAML}" ]; then
  "${VENV}" "${ROOT}/apps/mame-harness/memory_map.py" --yaml "${MEMORY_MAP_YAML}" --json "${MEMORY_MAP_JSON}"
  export BLACKBOX_MEMORY_MAP_PATH="${MEMORY_MAP_JSON}"
  export BLACKBOX_STATE_TIMELINE_PATH="${STATE_TIMELINE_JSON}"
  echo "  RAM memory tap: enabled (state_timeline.json will be written)"
fi

"${MAME_BINARY}" "${MAME_DRIVER}" \
  -rompath "${ROM_PATH}" \
  -aviwrite "${AVI_PATH}" \
  -snapshot_directory "${FRAMES_DIR}" \
  -autoboot_script "${ROOT}/scripts/mame_autoboot.lua"

# --- Done ---
echo ""
echo "MAME closed. AVI saved to: ${DISPLAY_AVI_PATH}"
echo ""
echo "Next step — extract frames and regenerate trace:"
echo "  ./scripts/extract_frames.sh ${RUN_ID}"

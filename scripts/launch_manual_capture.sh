#!/usr/bin/env bash
# Manual gameplay capture — user plays, MAME records AVI.
# Usage: ./scripts/launch_manual_capture.sh [run_id]
# Default run_id: manual_01
#
# After the user closes MAME, run:
#   ./scripts/extract_frames.sh [run_id]

set -euo pipefail

RUN_ID="${1:-manual_01}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "${ROOT}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "${ROOT}/.env"
  set +a
fi

MAME_BINARY="${BLACKBOX_MAME_BINARY:-mame}"
ROM_PATH="${BLACKBOX_ROM_PATH:-}"
MAME_DRIVER="${BLACKBOX_MAME_DRIVER:-gngb}"
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
DISPLAY_AVI_PATH="${REL_EVIDENCE_ROOT}/run_${RUN_ID}/video/capture.avi"

mkdir -p "${EVIDENCE_DIR}/video"
mkdir -p "${FRAMES_DIR}/extracted_png"

echo "Launching MAME for manual capture — run_id: ${RUN_ID}"
echo ""
echo "Controls:"
echo "  ← →       Move"
echo "  Left Alt   Jump"
echo "  Left Ctrl  Fire"
echo "  5          Insert coin"
echo "  1          Start 1P"
echo "  Esc        Quit"
echo ""
echo "Close the MAME window when done. AVI will be at:"
echo "  ${DISPLAY_AVI_PATH}"
echo ""

"${MAME_BINARY}" "${MAME_DRIVER}" \
  -rompath "${ROM_PATH}" \
  -aviwrite "${AVI_PATH}" \
  -snapshot_directory "${FRAMES_DIR}"

echo ""
echo "MAME closed. Run the following to extract frames and regenerate trace:"
echo "  ./scripts/extract_frames.sh ${RUN_ID}"

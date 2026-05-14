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
EVIDENCE_DIR="${ROOT}/evidence/private/run_${RUN_ID}"
AVI_PATH="${EVIDENCE_DIR}/video/capture.avi"
FRAMES_DIR="${EVIDENCE_DIR}/frames"

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
echo "  ${AVI_PATH}"
echo ""

/opt/homebrew/bin/mame gngb \
  -rompath /Users/matiasleandrokruk/Documents/gng/local/roms \
  -aviwrite "${AVI_PATH}" \
  -snapshot_directory "${FRAMES_DIR}"

echo ""
echo "MAME closed. Run the following to extract frames and regenerate trace:"
echo "  ./scripts/extract_frames.sh ${RUN_ID}"

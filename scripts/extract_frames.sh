#!/usr/bin/env bash
# Extract PNG frames from a capture AVI and regenerate the public trace.
# Usage: ./scripts/extract_frames.sh [run_id]
# Default run_id: manual_01

set -euo pipefail

RUN_ID="${1:-manual_01}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "${ROOT}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "${ROOT}/.env"
  set +a
fi

FFMPEG_BINARY="${BLACKBOX_FFMPEG_BINARY:-ffmpeg}"
TRACE_INPUT_PLAN="${BLACKBOX_TRACE_INPUT_PLAN:-plans/generated/gng_gameplay.yaml}"
TRACE_OUTPUT="${BLACKBOX_TRACE_OUTPUT:-specs/traces/gng_trace.json}"
REL_EVIDENCE_ROOT="${BLACKBOX_EVIDENCE_ROOT:-evidence/private}"
REL_EVIDENCE_ROOT="${REL_EVIDENCE_ROOT#./}"

case "${REL_EVIDENCE_ROOT}" in
  evidence/private|evidence/private/*) ;;
  *)
    echo "ERROR: BLACKBOX_EVIDENCE_ROOT must stay under evidence/private."
    exit 1
    ;;
esac

case "${TRACE_OUTPUT}" in
  /*)
    echo "ERROR: BLACKBOX_TRACE_OUTPUT must be repo-relative."
    exit 1
    ;;
esac

AVI_PATH="${ROOT}/${REL_EVIDENCE_ROOT}/run_${RUN_ID}/video/capture.avi"
OUT_DIR="${ROOT}/${REL_EVIDENCE_ROOT}/run_${RUN_ID}/frames/extracted_png"
VENV="${ROOT}/apps/mame-harness/.venv/bin/python"
DISPLAY_AVI_PATH="${REL_EVIDENCE_ROOT}/run_${RUN_ID}/video/capture.avi"

if [ ! -f "${AVI_PATH}" ]; then
  echo "ERROR: AVI not found at ${DISPLAY_AVI_PATH}"
  exit 1
fi

mkdir -p "${OUT_DIR}"

echo "Extracting frames from ${DISPLAY_AVI_PATH}..."
"${FFMPEG_BINARY}" -i "${AVI_PATH}" "${OUT_DIR}/%04d.png" -y -loglevel error
FRAME_COUNT=$(ls "${OUT_DIR}" | wc -l | tr -d ' ')
echo "Extracted: ${FRAME_COUNT} frames"

echo ""
echo "Regenerating ${TRACE_OUTPUT}..."
cd "${ROOT}"
"${VENV}" - <<EOF
import sys
sys.path.insert(0, 'apps/mame-harness')
sys.path.insert(0, 'packages/vision')
sys.path.insert(0, 'packages/validation')
from pathlib import Path
from guardrails import ensure_public_output_path
from vision_pipeline import extract_run_trace
import json

trace_output = Path('${TRACE_OUTPUT}')
ensure_public_output_path(trace_output)
output = extract_run_trace(
    '${RUN_ID}',
    Path('${TRACE_INPUT_PLAN}'),
    trace_output,
)
payload = json.loads(output.read_text())
entries = payload['trace']
from collections import Counter
states = Counter(e['state'] for e in entries)
events = Counter(ev for e in entries for ev in e['events'])
print(f"Trace entries: {len(entries)}")
print(f"States: {dict(states)}")
print(f"Events: {dict(events)}")
EOF

echo ""
echo "Done. Public trace at: ${TRACE_OUTPUT}"

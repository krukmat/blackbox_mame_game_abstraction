#!/usr/bin/env bash
# Extract PNG frames from a capture AVI and regenerate the public trace.
# Usage: ./scripts/extract_frames.sh [run_id]
# Default run_id: manual_01

set -euo pipefail

RUN_ID="${1:-manual_01}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AVI_PATH="${ROOT}/evidence/private/run_${RUN_ID}/video/capture.avi"
OUT_DIR="${ROOT}/evidence/private/run_${RUN_ID}/frames/extracted_png"
VENV="${ROOT}/apps/mame-harness/.venv/bin/python"

if [ ! -f "${AVI_PATH}" ]; then
  echo "ERROR: AVI not found at ${AVI_PATH}"
  exit 1
fi

mkdir -p "${OUT_DIR}"

echo "Extracting frames from ${AVI_PATH}..."
ffmpeg -i "${AVI_PATH}" "${OUT_DIR}/%04d.png" -y -loglevel error
FRAME_COUNT=$(ls "${OUT_DIR}" | wc -l | tr -d ' ')
echo "Extracted: ${FRAME_COUNT} frames"

echo ""
echo "Regenerating specs/traces/gng_trace.json..."
cd "${ROOT}"
"${VENV}" - <<EOF
import sys
sys.path.insert(0, 'apps/mame-harness')
sys.path.insert(0, 'packages/vision')
sys.path.insert(0, 'packages/validation')
from pathlib import Path
from vision_pipeline import extract_run_trace
import json

output = extract_run_trace(
    '${RUN_ID}',
    Path('plans/gng_gameplay.yaml'),
    Path('specs/traces/gng_trace.json'),
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
echo "Done. Public trace at: specs/traces/gng_trace.json"

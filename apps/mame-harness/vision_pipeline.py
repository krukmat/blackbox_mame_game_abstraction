from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
VISION_DIR = ROOT / "packages" / "vision"
if str(VISION_DIR) not in sys.path:
    sys.path.insert(0, str(VISION_DIR))

from entity_candidate_builder import EntityCandidateBuilder
from frame_differ import FrameDiffer
from frame_manifest import FrameManifest


def analyze_run_frames(run_id: str, output_path: Path) -> Path:
    frames_dir = ROOT / "evidence" / "private" / f"run_{run_id}" / "frames"
    manifest = FrameManifest.from_run(run_id=run_id, frames_dir=frames_dir)
    differ = FrameDiffer()
    diff_stats = differ.diff_manifest(manifest)
    builder = EntityCandidateBuilder()
    candidates = builder.build(diff_stats)
    return builder.write_public_output(candidates, output_path)

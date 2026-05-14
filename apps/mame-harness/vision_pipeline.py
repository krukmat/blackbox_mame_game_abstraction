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
from input_planner import load_input_plan
from trace_extractor import extract_trace
from behavioral_diff import write_trace_output


def _resolve_frames_dir(run_id: str) -> Path:
    base_frames_dir = ROOT / "evidence" / "private" / f"run_{run_id}" / "frames"
    extracted_png_dir = base_frames_dir / "extracted_png"
    if extracted_png_dir.exists():
        return extracted_png_dir
    return base_frames_dir


def analyze_run_frames(run_id: str, output_path: Path) -> Path:
    frames_dir = _resolve_frames_dir(run_id)
    manifest = FrameManifest.from_run(run_id=run_id, frames_dir=frames_dir)
    differ = FrameDiffer()
    diff_stats = differ.diff_manifest(manifest)
    builder = EntityCandidateBuilder()
    candidates = builder.build(diff_stats)
    return builder.write_public_output(candidates, output_path)


def extract_run_trace(run_id: str, input_plan_path: Path, output_path: Path) -> Path:
    frames_dir = _resolve_frames_dir(run_id)
    manifest = FrameManifest.from_run(run_id=run_id, frames_dir=frames_dir)
    diff_stats = FrameDiffer().diff_manifest(manifest)
    input_plan = load_input_plan(input_plan_path)
    entries = extract_trace(diff_stats, input_plan)
    return write_trace_output(entries, output_path)

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
VISION_DIR = ROOT / "packages" / "vision"
if str(VISION_DIR) not in sys.path:
    sys.path.insert(0, str(VISION_DIR))

from entity_candidate_builder import EntityCandidateBuilder
from frame_differ import FrameDiffer, OpenCVBackend
from frame_manifest import FrameManifest
from fps_calibration import GNG_MS_PER_FRAME, ms_per_frame_from_fps, read_avi_fps  # T10.3
from gng_vision_config import GNGVisionConfig
from input_planner import load_input_plan
from input_timeline import buttons_by_frame, load_input_timeline  # T20.2 / ADR-023
from trace_extractor import extract_trace
from behavioral_diff import write_trace_output

_GNG_CONFIG = GNGVisionConfig()  # T10.6-C: game-specific vision config for production runs


def _resolve_frames_dir(run_id: str) -> Path:
    base_frames_dir = ROOT / "evidence" / "private" / f"run_{run_id}" / "frames"
    extracted_png_dir = base_frames_dir / "extracted_png"
    if extracted_png_dir.exists():
        return extracted_png_dir
    return base_frames_dir


def _resolve_ms_per_frame(run_id: str) -> float:
    # T10.3 — if the run has a real capture AVI, derive ms/frame from it;
    # otherwise fall back to the calibrated GNG constant.
    avi_path = ROOT / "evidence" / "private" / f"run_{run_id}" / "video" / "capture.avi"
    if avi_path.exists():
        try:
            fps = read_avi_fps(avi_path)
            return ms_per_frame_from_fps(fps)
        except (ValueError, OSError):
            pass
    return GNG_MS_PER_FRAME


def analyze_run_frames(run_id: str, output_path: Path) -> Path:
    frames_dir = _resolve_frames_dir(run_id)
    ms_per_frame = _resolve_ms_per_frame(run_id)  # T10.3
    manifest = FrameManifest.from_run(run_id=run_id, frames_dir=frames_dir, ms_per_frame=ms_per_frame)
    differ = FrameDiffer(backend=OpenCVBackend(_GNG_CONFIG))  # T10.6-C
    diff_stats = differ.diff_manifest(manifest)
    builder = EntityCandidateBuilder()
    candidates = builder.build(diff_stats)
    return builder.write_public_output(candidates, output_path)


def _resolve_input_timeline(run_id: str) -> "dict[int, frozenset[str]] | None":
    """T20.2 / ADR-023: load the private ground-truth input timeline if present.

    Returns None when the run predates timeline capture, so the trace falls back to
    the legacy plan/CV event sourcing without error.
    """
    timeline_path = (
        ROOT / "evidence" / "private" / f"run_{run_id}" / "logs" / "input_timeline.json"
    )
    if not timeline_path.exists():
        return None
    return buttons_by_frame(load_input_timeline(timeline_path))


def extract_run_trace(run_id: str, input_plan_path: Path, output_path: Path) -> Path:
    frames_dir = _resolve_frames_dir(run_id)
    ms_per_frame = _resolve_ms_per_frame(run_id)  # T10.3
    manifest = FrameManifest.from_run(run_id=run_id, frames_dir=frames_dir, ms_per_frame=ms_per_frame)
    diff_stats = FrameDiffer(backend=OpenCVBackend(_GNG_CONFIG)).diff_manifest(manifest)  # T10.6-C
    input_plan = load_input_plan(input_plan_path)
    input_timeline = _resolve_input_timeline(run_id)  # T20.2 / ADR-023
    entries = extract_trace(
        diff_stats, input_plan, config=_GNG_CONFIG, input_timeline=input_timeline
    )  # T10.6-E: gap tolerance
    return write_trace_output(entries, output_path)

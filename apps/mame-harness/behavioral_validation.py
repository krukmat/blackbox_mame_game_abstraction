from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
VALIDATION_DIR = ROOT / "packages" / "validation"
if str(VALIDATION_DIR) not in sys.path:
    sys.path.insert(0, str(VALIDATION_DIR))

from behavioral_diff import BehavioralDiff, TraceEntry, load_trace_entries, write_validation_reports


def validate_behavior(
    observed_trace_path: Path | None,
    simulated_trace_path: Path | None,
    json_output: Path,
    markdown_output: Path,
) -> dict[str, object]:
    observed = (
        load_trace_entries(observed_trace_path)
        if observed_trace_path is not None
        else _sample_trace()
    )
    simulated = (
        load_trace_entries(simulated_trace_path)
        if simulated_trace_path is not None
        else _sample_trace()
    )
    result = BehavioralDiff().compare(observed, simulated)
    return write_validation_reports(result, json_output, markdown_output)


def _sample_trace() -> list[TraceEntry]:
    return [
        TraceEntry(
            frame=0,
            entity_id="player",
            entity_type="player",
            x=0.0,
            y=0.0,
            velocity_x=1.0,
            velocity_y=0.0,
            state="grounded",
            events=["spawn"],
        ),
        TraceEntry(
            frame=1,
            entity_id="player",
            entity_type="player",
            x=1.0,
            y=0.0,
            velocity_x=1.0,
            velocity_y=0.0,
            state="grounded",
            events=[],
        ),
    ]

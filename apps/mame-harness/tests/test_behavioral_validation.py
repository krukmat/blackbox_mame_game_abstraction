from __future__ import annotations

from pathlib import Path
import json

from behavioral_diff import BehavioralDiff, TraceEntry, write_validation_reports


def test_matching_traces_pass() -> None:
    trace = [
        TraceEntry(
            frame=0,
            entity_id="player",
            entity_type="player",
            x=1.0,
            y=2.0,
            velocity_x=1.0,
            velocity_y=0.0,
            state="grounded",
            events=["spawn"],
        )
    ]
    result = BehavioralDiff().compare(trace, trace)
    assert result.passed is True
    assert result.confidence == 1.0


def test_traces_outside_tolerance_fail() -> None:
    observed = [
        TraceEntry(0, "player", "player", 0.0, 0.0, 1.0, 0.0, "grounded", [], 0),
    ]
    simulated = [
        TraceEntry(0, "player", "player", 5.0, 0.0, 1.0, 0.0, "grounded", [], 0),
    ]
    result = BehavioralDiff().compare(observed, simulated, movement_tolerance=1.0)
    assert result.passed is False
    assert any("x mismatch" in item for item in result.mismatches)


def test_reports_do_not_include_private_paths(tmp_path: Path) -> None:
    report = write_validation_reports(
        BehavioralDiff().compare([], []),
        tmp_path / "specs" / "report.json",
        tmp_path / "specs" / "report.md",
    )
    serialized = json.dumps(report)
    assert "evidence/private" not in serialized

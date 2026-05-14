from __future__ import annotations

from pathlib import Path
import json

import pytest

from behavioral_diff import BehavioralDiff, TraceEntry, load_trace_entries, write_trace_output, write_validation_reports


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


def test_write_trace_output_round_trips_entries(tmp_path: Path) -> None:
    output = tmp_path / "specs" / "traces" / "trace.json"
    entries = [
        TraceEntry(
            frame=0,
            entity_id="player",
            entity_type="player",
            x=0.25,
            y=0.5,
            velocity_x=0.1,
            velocity_y=0.0,
            state="idle",
            events=["spawn"],
            score_delta=0,
        )
    ]

    written = write_trace_output(entries, output)
    loaded = load_trace_entries(written)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert written == output
    assert loaded == entries
    assert list(payload) == ["trace"]
    assert set(payload["trace"][0]) == {
        "frame",
        "entity_id",
        "entity_type",
        "x",
        "y",
        "velocity_x",
        "velocity_y",
        "state",
        "events",
        "score_delta",
    }


def test_write_trace_output_rejects_blocked_suffix(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="blocked public output suffix"):
        write_trace_output([], tmp_path / "specs" / "traces" / "trace.png")


def test_write_trace_output_rejects_private_path_leak(tmp_path: Path) -> None:
    entries = [
        TraceEntry(
            frame=0,
            entity_id="player",
            entity_type="player",
            x=0.0,
            y=0.0,
            velocity_x=0.0,
            velocity_y=0.0,
            state="evidence/private/run_demo/frames/0001.png",
            events=[],
            score_delta=0,
        )
    ]

    with pytest.raises(ValueError, match="private path leaked"):
        write_trace_output(entries, tmp_path / "specs" / "traces" / "trace.json")

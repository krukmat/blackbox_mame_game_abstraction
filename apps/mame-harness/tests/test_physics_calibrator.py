"""T11.3 — Tests for physics_calibrator.

Uses synthetic trace data so tests are independent of the real trace quality.
Synthetic data exercises both direct in_flight samples and ADR-020
human-validated trajectory samples.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from guardrails import ensure_no_private_paths
from physics_calibrator import (
    MIN_SAMPLE_COUNT,
    CalibrationResult,
    calibrate,
    write_calibration_yaml,
)

# ─────────────────────────────────────────────────────────────────────────────
# Synthetic trace builders
# ─────────────────────────────────────────────────────────────────────────────

PLAYER_VX = 0.15
PLAYER_VY_JUMP = 0.18
GRAVITY_DELTA = 0.02
PROJ_VX = 0.30


def _player_entry(frame: int, **kwargs) -> dict:
    base = {
        "frame": frame,
        "entity_id": "player",
        "entity_type": "player",
        "x": 0.5,
        "y": 0.5,
        "velocity_x": 0.0,
        "velocity_y": 0.0,
        "state": "idle",
        "events": [],
        "score_delta": 0,
    }
    base.update(kwargs)
    return base


def _projectile_entry(frame: int, state: str = "in_flight", vx: float = PROJ_VX) -> dict:
    return {
        "frame": frame,
        "entity_id": f"projectile_{frame}",
        "entity_type": "projectile",
        "x": 0.6,
        "y": 0.5,
        "velocity_x": vx,
        "velocity_y": 0.0,
        "state": state,
        "events": [],
        "score_delta": 0,
    }


def _build_synthetic_trace() -> dict:
    """Minimal synthetic trace with >= 10 samples for all 4 constants."""
    entries: list[dict] = []

    # 15 walking frames (locomotion_velocity_x)
    for i in range(15):
        entries.append(
            _player_entry(100 + i, state="walking_right", velocity_x=PLAYER_VX)
        )

    # 12 jump_start events with non-zero velocity_y (jump_velocity_y)
    for i in range(12):
        entries.append(
            _player_entry(
                200 + i,
                state="ascending",
                velocity_y=-PLAYER_VY_JUMP,
                events=["jump_start"],
            )
        )

    # 15 consecutive ascending→ascending pairs for gravity
    # Frame 300+i → 300+i+1: delta_vy = GRAVITY_DELTA
    for i in range(15):
        entries.append(
            _player_entry(
                300 + i,
                state="ascending",
                velocity_y=-(PLAYER_VY_JUMP - i * GRAVITY_DELTA),
            )
        )

    # 12 in_flight projectile entries with non-zero velocity_x
    for i in range(12):
        entries.append(_projectile_entry(400 + i))

    return {"trace": entries}


def _write_trace(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "test_trace.json"
    p.write_text(json.dumps(data))
    return p


def _write_projectile_candidates(tmp_path: Path) -> Path:
    candidates = []
    for candidate_id, start_frame, start_x in (
        (1, 700, 0.20),
        (2, 720, 0.30),
        (3, 740, 0.40),
    ):
        points = [
            {"frame": start_frame + i, "x": start_x + 0.03 * i, "y": 0.70}
            for i in range(4)
        ]
        candidates.append({
            "id": candidate_id,
            "start_frame": points[0]["frame"],
            "end_frame": points[-1]["frame"],
            "valid_for_review": True,
            "points": points,
        })
    p = tmp_path / "projectile_trajectory_candidates.json"
    p.write_text(json.dumps({"candidates": candidates}))
    return p


# ─────────────────────────────────────────────────────────────────────────────
# ST5: Python tests — calibrator behaviour
# ─────────────────────────────────────────────────────────────────────────────

def test_calibrate_returns_four_constants(tmp_path: Path) -> None:
    trace = _write_trace(tmp_path, _build_synthetic_trace())
    result = calibrate(trace)
    assert isinstance(result, CalibrationResult)
    assert result.locomotion_velocity_x is not None
    assert result.jump_velocity_y is not None
    assert result.gravity_units_per_frame is not None
    assert result.projectile_velocity_x is not None


def test_sample_counts_meet_minimum(tmp_path: Path) -> None:
    trace = _write_trace(tmp_path, _build_synthetic_trace())
    result = calibrate(trace)
    for attr in (
        "locomotion_velocity_x",
        "jump_velocity_y",
        "gravity_units_per_frame",
        "projectile_velocity_x",
    ):
        const = getattr(result, attr)
        assert const.sample_count >= MIN_SAMPLE_COUNT, (
            f"{attr}: sample_count={const.sample_count} < {MIN_SAMPLE_COUNT}"
        )


def test_values_are_positive(tmp_path: Path) -> None:
    trace = _write_trace(tmp_path, _build_synthetic_trace())
    result = calibrate(trace)
    for attr in (
        "locomotion_velocity_x",
        "jump_velocity_y",
        "gravity_units_per_frame",
        "projectile_velocity_x",
    ):
        const = getattr(result, attr)
        assert const.value_per_second > 0, f"{attr}: value_per_second must be > 0"


def test_per_second_conversion(tmp_path: Path) -> None:
    """value_per_second == value_per_frame / (16.768 / 1000)."""
    trace = _write_trace(tmp_path, _build_synthetic_trace())
    result = calibrate(trace)
    for attr in (
        "locomotion_velocity_x",
        "jump_velocity_y",
        "gravity_units_per_frame",
        "projectile_velocity_x",
    ):
        const = getattr(result, attr)
        expected = const.value_per_frame / (16.768 / 1000)
        assert abs(const.value_per_second - expected) < 0.01, (
            f"{attr}: per_second mismatch — got {const.value_per_second}, expected {expected}"
        )


def test_insufficient_samples_raise_value_error(tmp_path: Path) -> None:
    """Trace with only 5 locomotion samples must raise ValueError."""
    data: dict = {
        "trace": [
            _player_entry(i, state="walking_right", velocity_x=PLAYER_VX)
            for i in range(5)
        ]
    }
    trace = _write_trace(tmp_path, data)
    with pytest.raises(ValueError, match="locomotion_velocity_x"):
        calibrate(trace)


# ─────────────────────────────────────────────────────────────────────────────
# ST5: Python tests — YAML output and guardrails
# ─────────────────────────────────────────────────────────────────────────────

def test_calibration_yaml_exists_after_write(tmp_path: Path) -> None:
    trace = _write_trace(tmp_path, _build_synthetic_trace())
    out = tmp_path / "specs" / "calibration" / "test_calibration.yaml"
    result = calibrate(trace)
    write_calibration_yaml(result, out)
    assert out.exists()


def test_calibration_yaml_contains_four_constants(tmp_path: Path) -> None:
    trace = _write_trace(tmp_path, _build_synthetic_trace())
    out = tmp_path / "specs" / "calibration" / "test_calibration.yaml"
    result = calibrate(trace)
    write_calibration_yaml(result, out)
    data = yaml.safe_load(out.read_text())
    constants = data["constants"]
    assert "locomotion_velocity_x" in constants
    assert "jump_velocity_y" in constants
    assert "gravity_units_per_frame" in constants
    assert "projectile_velocity_x" in constants


def test_calibration_yaml_passes_guardrails(tmp_path: Path) -> None:
    """ensure_no_private_paths must not raise on the written payload."""
    trace = _write_trace(tmp_path, _build_synthetic_trace())
    out = tmp_path / "specs" / "calibration" / "test_calibration.yaml"
    result = calibrate(trace)
    write_calibration_yaml(result, out)
    data = yaml.safe_load(out.read_text())
    ensure_no_private_paths(data)


def test_write_blocked_for_private_output_path(tmp_path: Path) -> None:
    """Writing to evidence/private/ must be rejected by guardrails."""
    trace = _write_trace(tmp_path, _build_synthetic_trace())
    result = calibrate(trace)
    bad_path = Path("evidence/private/should_not_write.yaml")
    with pytest.raises(Exception):
        write_calibration_yaml(result, bad_path)


def test_projectile_surrogate_is_not_used_for_missing_projectile_motion(tmp_path: Path) -> None:
    """When no real projectile motion exists, player fire velocity is rejected."""
    data = _build_synthetic_trace()
    # Remove all in_flight projectile entries, add player fire events instead.
    trace_entries = [e for e in data["trace"] if e["entity_type"] != "projectile"]
    for i in range(12):
        trace_entries.append(
            _player_entry(
                500 + i,
                state="walking_right",
                velocity_x=PLAYER_VX,
                events=["fire"],
            )
        )
    trace = _write_trace(tmp_path, {"trace": trace_entries})
    with pytest.raises(ValueError, match="projectile_velocity_x"):
        calibrate(trace)


def test_projectile_velocity_uses_accepted_trajectory_candidates(tmp_path: Path) -> None:
    data = _build_synthetic_trace()
    trace_entries = [e for e in data["trace"] if e["entity_type"] != "projectile"]
    trace = _write_trace(tmp_path, {"trace": trace_entries})
    candidate_path = _write_projectile_candidates(tmp_path)

    result = calibrate(
        trace,
        projectile_candidate_path=candidate_path,
        accepted_projectile_ids=[1, 2, 3],
    )

    assert result.projectile_velocity_x.source_method == "human_validated_projectile_trajectory"
    assert result.projectile_velocity_x.sample_count == 9
    assert result.projectile_velocity_x.value_per_frame == pytest.approx(0.03)


def test_projectile_trajectory_calibration_requires_three_accepted_ids(tmp_path: Path) -> None:
    data = _build_synthetic_trace()
    trace_entries = [e for e in data["trace"] if e["entity_type"] != "projectile"]
    trace = _write_trace(tmp_path, {"trace": trace_entries})
    candidate_path = _write_projectile_candidates(tmp_path)

    with pytest.raises(ValueError, match="accepted trajectory count=2"):
        calibrate(
            trace,
            projectile_candidate_path=candidate_path,
            accepted_projectile_ids=[1, 2],
        )


# ─────────────────────────────────────────────────────────────────────────────
# Integration: real trace
# ─────────────────────────────────────────────────────────────────────────────

REAL_TRACE = Path("specs/traces/gng_trace.json")


@pytest.mark.skipif(
    not REAL_TRACE.exists(),
    reason="Real trace not available",
)
def test_real_trace_requires_projectile_trajectory_review() -> None:
    """Real trace must not silently use a player-motion projectile surrogate."""
    with pytest.raises(ValueError, match="projectile_velocity_x"):
        calibrate(REAL_TRACE)

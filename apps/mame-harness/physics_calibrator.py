"""T11.3 — Physics calibration from trace.

Measures 4 physics constants from specs/traces/gng_trace.json and writes
specs/calibration/gng_physics_calibration.yaml.

Constants measured:
  locomotion_velocity_x : mean |velocity_x| for player frames where state != idle
  jump_velocity_y       : mean |velocity_y| at jump_start events
  gravity_units_per_frame: mean Δvelocity_y between consecutive airborne frames
  projectile_velocity_x : mean |velocity_x| for projectile in_flight entries,
                          or human-validated trajectory displacement samples
                          from projectile_trajectory_picker.py (ADR-020)

All raw values are per-frame normalized fractions (0.0–1.0 per frame).
value_per_second = value_per_frame / (ms_per_frame / 1000).
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from guardrails import ensure_no_private_paths, ensure_public_output_path

MS_PER_FRAME: float = 16.768  # T10.3 calibrated value — 59.6374 fps
MIN_SAMPLE_COUNT: int = 10
MIN_ACCEPTED_PROJECTILE_TRAJECTORIES: int = 3


# ─────────────────────────────────────────────────────────────────────────────
# Data types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(slots=True)
class CalibrationConstant:
    value_per_frame: float
    value_per_second: float
    sample_count: int
    std_dev: float
    source_method: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "value_per_frame": round(self.value_per_frame, 6),
            "value_per_second": round(self.value_per_second, 4),
            "sample_count": self.sample_count,
            "std_dev": round(self.std_dev, 6),
            "source_method": self.source_method,
        }
        if self.note:
            d["note"] = self.note
        return d


@dataclass(slots=True)
class CalibrationResult:
    locomotion_velocity_x: CalibrationConstant
    jump_velocity_y: CalibrationConstant
    gravity_units_per_frame: CalibrationConstant
    projectile_velocity_x: CalibrationConstant
    ms_per_frame: float
    source_trace: str


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _to_per_second(value_per_frame: float) -> float:
    return value_per_frame / (MS_PER_FRAME / 1000)


def _build_constant(
    samples: list[float],
    source_method: str,
    name: str,
    note: str = "",
) -> CalibrationConstant:
    if len(samples) < MIN_SAMPLE_COUNT:
        raise ValueError(
            f"{name}: sample_count={len(samples)} < required minimum {MIN_SAMPLE_COUNT}"
        )
    mean_val = statistics.mean(samples)
    std_val = statistics.stdev(samples) if len(samples) >= 2 else 0.0
    return CalibrationConstant(
        value_per_frame=mean_val,
        value_per_second=_to_per_second(mean_val),
        sample_count=len(samples),
        std_dev=std_val,
        source_method=source_method,
        note=note,
    )


def _build_projectile_trajectory_constant(
    samples: list[float],
    accepted_ids: list[int],
) -> CalibrationConstant:
    if len(accepted_ids) < MIN_ACCEPTED_PROJECTILE_TRAJECTORIES:
        raise ValueError(
            f"projectile_velocity_x: accepted trajectory count={len(accepted_ids)} "
            f"< required minimum {MIN_ACCEPTED_PROJECTILE_TRAJECTORIES}"
        )
    if not samples:
        raise ValueError("projectile_velocity_x: no displacement samples in accepted trajectories")

    median_val = statistics.median(samples)
    std_val = statistics.stdev(samples) if len(samples) >= 2 else 0.0
    return CalibrationConstant(
        value_per_frame=median_val,
        value_per_second=_to_per_second(median_val),
        sample_count=len(samples),
        std_dev=std_val,
        source_method="human_validated_projectile_trajectory",
        note=(
            "Derived from human-validated projectile trajectory candidates "
            f"(IDs {accepted_ids}) via ADR-019/ADR-020 workflow. "
            "Each sample is absolute x displacement per frame between "
            "consecutive trajectory points."
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Measurement functions
# ─────────────────────────────────────────────────────────────────────────────

def _measure_locomotion_velocity_x(player: list[dict]) -> CalibrationConstant:
    samples = [
        abs(e["velocity_x"])
        for e in player
        if e["state"] != "idle" and e["velocity_x"] != 0
    ]
    return _build_constant(samples, "direct", "locomotion_velocity_x")


def _measure_jump_velocity_y(player: list[dict]) -> CalibrationConstant:
    samples = [
        abs(e["velocity_y"])
        for e in player
        if "jump_start" in e.get("events", []) and e["velocity_y"] != 0
    ]
    return _build_constant(samples, "direct", "jump_velocity_y")


def _measure_gravity(player: list[dict]) -> CalibrationConstant:
    airborne = [e for e in player if e["state"] in ("ascending", "descending")]
    airborne_by_frame: dict[int, dict] = {e["frame"]: e for e in airborne}
    deltas: list[float] = []
    for entry in airborne:
        next_frame = entry["frame"] + 1
        if next_frame in airborne_by_frame:
            delta_vy = airborne_by_frame[next_frame]["velocity_y"] - entry["velocity_y"]
            if delta_vy > 0:
                deltas.append(delta_vy)
    return _build_constant(deltas, "direct", "gravity_units_per_frame")


def _measure_projectile_velocity_x(
    projectiles: list[dict],
) -> CalibrationConstant:
    # Primary: in_flight entries with non-zero velocity_x
    in_flight_samples = [
        abs(e["velocity_x"])
        for e in projectiles
        if e["state"] == "in_flight" and e["velocity_x"] != 0
    ]
    if len(in_flight_samples) >= MIN_SAMPLE_COUNT:
        return _build_constant(in_flight_samples, "direct", "projectile_velocity_x")

    # Secondary: any projectile with non-zero velocity_x regardless of state
    any_state_samples = [
        abs(e["velocity_x"]) for e in projectiles if e["velocity_x"] != 0
    ]
    if len(any_state_samples) >= MIN_SAMPLE_COUNT:
        return _build_constant(
            any_state_samples,
            "any_state_fallback",
            "projectile_velocity_x",
        )

    raise ValueError(
        f"projectile_velocity_x: insufficient samples — "
        f"in_flight={len(in_flight_samples)}, "
        f"any_state={len(any_state_samples)}; need >= {MIN_SAMPLE_COUNT}. "
        f"Provide human-validated projectile trajectory candidates or ensure "
        f"the trace includes in-flight projectile entries."
    )


def _measure_projectile_velocity_x_from_candidates(
    candidate_path: Path,
    accepted_ids: list[int],
) -> CalibrationConstant:
    payload = json.loads(candidate_path.read_text())
    candidates = payload.get("candidates", [])
    by_id = {int(candidate["id"]): candidate for candidate in candidates}

    missing = [candidate_id for candidate_id in accepted_ids if candidate_id not in by_id]
    if missing:
        raise ValueError(f"projectile_velocity_x: unknown accepted candidate IDs {missing}")

    samples: list[float] = []
    for candidate_id in accepted_ids:
        candidate = by_id[candidate_id]
        if not candidate.get("valid_for_review", False):
            raise ValueError(
                f"projectile_velocity_x: accepted candidate {candidate_id} "
                f"failed deterministic validation flags"
            )
        points = candidate.get("points", [])
        if len(points) < 2:
            raise ValueError(
                f"projectile_velocity_x: accepted candidate {candidate_id} "
                f"has fewer than 2 points"
            )
        for prev, curr in zip(points, points[1:]):
            frame_gap = int(curr["frame"]) - int(prev["frame"])
            if frame_gap <= 0:
                continue
            samples.append(abs(float(curr["x"]) - float(prev["x"])) / frame_gap)

    return _build_projectile_trajectory_constant(samples, accepted_ids)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def calibrate(
    trace_path: Path,
    projectile_candidate_path: Path | None = None,
    accepted_projectile_ids: list[int] | None = None,
) -> CalibrationResult:
    """Measure 4 physics constants from trace_path.

    Raises ValueError if any constant has sample_count < MIN_SAMPLE_COUNT.
    """
    raw = json.loads(trace_path.read_text())
    entries: list[dict] = raw["trace"]

    player = [e for e in entries if e["entity_type"] == "player"]
    projectiles = [e for e in entries if e["entity_type"] == "projectile"]

    locomotion_velocity_x = _measure_locomotion_velocity_x(player)
    jump_velocity_y = _measure_jump_velocity_y(player)
    gravity_units_per_frame = _measure_gravity(player)

    if projectile_candidate_path is not None:
        projectile_velocity_x = _measure_projectile_velocity_x_from_candidates(
            projectile_candidate_path,
            accepted_projectile_ids or [],
        )
    else:
        projectile_velocity_x = _measure_projectile_velocity_x(projectiles)

    return CalibrationResult(
        locomotion_velocity_x=locomotion_velocity_x,
        jump_velocity_y=jump_velocity_y,
        gravity_units_per_frame=gravity_units_per_frame,
        projectile_velocity_x=projectile_velocity_x,
        ms_per_frame=MS_PER_FRAME,
        source_trace=str(trace_path),
    )


def write_calibration_yaml(result: CalibrationResult, output_path: Path) -> None:
    """Write calibration result to a public YAML artifact.

    Validates the output path and payload against guardrails before writing.
    """
    ensure_public_output_path(output_path)

    # Normalize to a relative path so guardrails never reject an absolute tmp dir.
    # Try CWD-relative first; fall back to just the filename.
    try:
        source_trace_label = str(Path(result.source_trace).relative_to(Path.cwd()))
    except ValueError:
        source_trace_label = Path(result.source_trace).name

    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "source_trace": source_trace_label,
        "ms_per_frame": result.ms_per_frame,
        "generated_by": "T11.3 physics_calibrator.py",
        "constants": {
            "locomotion_velocity_x": result.locomotion_velocity_x.to_dict(),
            "jump_velocity_y": result.jump_velocity_y.to_dict(),
            "gravity_units_per_frame": result.gravity_units_per_frame.to_dict(),
            "projectile_velocity_x": result.projectile_velocity_x.to_dict(),
        },
    }

    ensure_no_private_paths(payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.dump(payload, default_flow_style=False, sort_keys=False))


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def _parse_ids(raw: str) -> list[int]:
    if raw.strip() == "":
        return []
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Calibrate physics constants from trace data.")
    parser.add_argument("--trace", default="specs/traces/gng_trace.json")
    parser.add_argument("--output", default="specs/calibration/gng_physics_calibration.yaml")
    parser.add_argument(
        "--projectile-candidates",
        default="",
        help="Private projectile_trajectory_candidates.json from ADR-019 review",
    )
    parser.add_argument(
        "--accepted-projectile-ids",
        default="",
        help="Comma-separated human-accepted projectile trajectory candidate IDs",
    )
    args = parser.parse_args()

    trace_path = Path(args.trace)
    output_path = Path(args.output)
    projectile_candidate_path = (
        Path(args.projectile_candidates)
        if args.projectile_candidates
        else None
    )
    accepted_projectile_ids = _parse_ids(args.accepted_projectile_ids)

    print(f"Calibrating from: {trace_path}")
    result = calibrate(
        trace_path,
        projectile_candidate_path=projectile_candidate_path,
        accepted_projectile_ids=accepted_projectile_ids,
    )

    print("Constants measured:")
    for name, const in [
        ("locomotion_velocity_x ", result.locomotion_velocity_x),
        ("jump_velocity_y       ", result.jump_velocity_y),
        ("gravity_units_per_frame", result.gravity_units_per_frame),
        ("projectile_velocity_x ", result.projectile_velocity_x),
    ]:
        print(
            f"  {name}: {const.value_per_second:.4f}/s  "
            f"(n={const.sample_count}, method={const.source_method})"
        )

    write_calibration_yaml(result, output_path)
    print(f"\nCalibration YAML written to: {output_path}")


if __name__ == "__main__":
    main()

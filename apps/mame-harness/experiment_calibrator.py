"""T20.4 / ADR-024 — deterministic auto-calibrator from isolation experiments.

Reads an experiment input plan (which declares the isolated variable and the
measurement window) and the public trace of that run, then measures the physics
constant(s) by closed-form / least-squares fit over the window — with NO human
candidate selection.

Sources only the public trace (numeric positions per frame) and the public plan;
never reads frames, video, or any private visual content. Output is the public
artifact specs/calibration/gng_experiment_calibration.yaml (numbers only).

Replaces, as the default method, the per-constant human picker workflow (ADR-019),
which is retained as the fallback when a fit is low-quality.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from guardrails import ensure_no_private_paths, ensure_public_output_path
from input_planner import InputPlan, load_input_plan
from physics_calibrator import MS_PER_FRAME

# Quality / consistency gates (source-visible per ADR-024).
FIT_QUALITY_THRESHOLD: float = 0.95   # r² below this -> needs_human_review (ADR-019 fallback)
T_PEAK_TOLERANCE_FRAMES: float = 3.0  # |t_peak_predicted - t_peak_observed| must be within this
MIN_LINEAR_SAMPLES: int = 3
MIN_QUADRATIC_SAMPLES: int = 4

_AIRBORNE_STATES = frozenset({"ascending", "descending"})


# ─────────────────────────────────────────────────────────────────────────────
# Result type
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(slots=True)
class ExperimentConstant:
    value_per_frame: float
    unit: str                       # "norm_units_per_frame" | "norm_units_per_frame2" | "frames" | "norm_units"
    sample_count: int
    experiment_id: str
    measurement_window: tuple[int, int]
    source_method: str
    fit_quality: float | None = None       # r² where applicable
    value_per_second: float | None = None
    needs_human_review: bool = False
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "value_per_frame": round(self.value_per_frame, 6),
            "unit": self.unit,
            "sample_count": self.sample_count,
            "experiment_id": self.experiment_id,
            "measurement_window": list(self.measurement_window),
            "source_method": self.source_method,
            "needs_human_review": self.needs_human_review,
        }
        if self.value_per_second is not None:
            d["value_per_second"] = round(self.value_per_second, 4)
        if self.fit_quality is not None:
            d["fit_quality_r2"] = round(self.fit_quality, 6)
        if self.note:
            d["note"] = self.note
        return d


# ─────────────────────────────────────────────────────────────────────────────
# Fit helpers
# ─────────────────────────────────────────────────────────────────────────────


def _to_per_second(value_per_frame: float) -> float:
    return value_per_frame / (MS_PER_FRAME / 1000)


def _r_squared(y: np.ndarray, predicted: np.ndarray) -> float:
    ss_res = float(np.sum((y - predicted) ** 2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    if ss_tot == 0.0:
        return 1.0  # constant signal — a perfectly flat line fits exactly
    return 1.0 - ss_res / ss_tot


def _fit_linear(t: list[float], y: list[float]) -> tuple[float, float, float]:
    """Return (slope, intercept, r2) for a least-squares line."""
    ta = np.asarray(t, dtype=float)
    ya = np.asarray(y, dtype=float)
    slope, intercept = np.polyfit(ta, ya, 1)
    r2 = _r_squared(ya, np.polyval([slope, intercept], ta))
    return float(slope), float(intercept), r2


def _fit_quadratic(t: list[float], y: list[float]) -> tuple[float, float, float, float]:
    """Return (a, b, c, r2) for y = a*t^2 + b*t + c (t relative to first sample)."""
    ta = np.asarray(t, dtype=float)
    ya = np.asarray(y, dtype=float)
    a, b, c = np.polyfit(ta, ya, 2)
    r2 = _r_squared(ya, np.polyval([a, b, c], ta))
    return float(a), float(b), float(c), r2


# ─────────────────────────────────────────────────────────────────────────────
# Per-variable measurement
# ─────────────────────────────────────────────────────────────────────────────


def _window_entries(entries: list[dict], entity_type: str, window: tuple[int, int]) -> list[dict]:
    start, end = window
    selected = [
        e for e in entries
        if e["entity_type"] == entity_type and start <= e["frame"] <= end
    ]
    selected.sort(key=lambda e: e["frame"])
    return selected


def _measure_locomotion(entries: list[dict], exp_id: str, window: tuple[int, int]) -> dict[str, ExperimentConstant]:
    player = _window_entries(entries, "player", window)
    if len(player) < MIN_LINEAR_SAMPLES:
        raise ValueError(f"locomotion_velocity_x: only {len(player)} player samples in window {window}")
    t = [e["frame"] for e in player]
    x = [e["x"] for e in player]
    slope, _intercept, r2 = _fit_linear(t, x)
    value = abs(slope)
    return {
        "locomotion_velocity_x": ExperimentConstant(
            value_per_frame=value,
            unit="norm_units_per_frame",
            value_per_second=_to_per_second(value),
            sample_count=len(player),
            experiment_id=exp_id,
            measurement_window=window,
            source_method="experiment_linear_fit",
            fit_quality=r2,
            needs_human_review=r2 < FIT_QUALITY_THRESHOLD,
            note="Slope of player x(t) over an isolated walk segment.",
        )
    }


def _measure_jump_arc(entries: list[dict], exp_id: str, window: tuple[int, int]) -> dict[str, ExperimentConstant]:
    player = _window_entries(entries, "player", window)
    airborne = [e for e in player if e["state"] in _AIRBORNE_STATES]
    if len(airborne) < MIN_QUADRATIC_SAMPLES:
        raise ValueError(f"jump_arc: only {len(airborne)} airborne samples in window {window}")

    first_frame = airborne[0]["frame"]
    t = [e["frame"] - first_frame for e in airborne]   # relative time → v0 = b at t=0
    y = [e["y"] for e in airborne]
    a, b, _c, r2 = _fit_quadratic(t, y)

    # Screen y increases downward: ascending lowers y, so the parabola opens upward (a > 0).
    gravity = 2.0 * abs(a)                 # per frame²
    jump_velocity = abs(b)                 # |initial vertical velocity| per frame
    low_fit = r2 < FIT_QUALITY_THRESHOLD

    # Physical consistency: predicted t_peak vs observed extremum (closes ADR-019 t_peak failure).
    t_peak_pred = jump_velocity / gravity if gravity > 0 else float("inf")
    y_arr = np.asarray(y, dtype=float)
    t_peak_obs = float(t[int(np.argmin(y_arr))])  # min y == highest point on screen
    t_peak_consistent = abs(t_peak_pred - t_peak_obs) <= T_PEAK_TOLERANCE_FRAMES
    needs_review = low_fit or not t_peak_consistent
    consistency_note = (
        f"t_peak predicted={t_peak_pred:.2f}f observed={t_peak_obs:.2f}f "
        f"({'consistent' if t_peak_consistent else 'INCONSISTENT'})."
    )

    common = dict(
        sample_count=len(airborne),
        experiment_id=exp_id,
        measurement_window=window,
        source_method="experiment_quadratic_fit",
        fit_quality=r2,
        needs_human_review=needs_review,
    )
    return {
        "jump_velocity_y": ExperimentConstant(
            value_per_frame=jump_velocity,
            unit="norm_units_per_frame",
            value_per_second=_to_per_second(jump_velocity),
            note="|initial vertical velocity| from quadratic y(t). " + consistency_note,
            **common,
        ),
        "gravity_units_per_frame": ExperimentConstant(
            value_per_frame=gravity,
            unit="norm_units_per_frame2",
            value_per_second=None,
            note="2*a from quadratic y(t). " + consistency_note,
            **common,
        ),
    }


def _measure_projectile(entries: list[dict], exp_id: str, window: tuple[int, int]) -> dict[str, ExperimentConstant]:
    projectile = _window_entries(entries, "projectile", window)
    if len(projectile) < MIN_LINEAR_SAMPLES:
        # ADR-020: do not fall back to a player-motion surrogate.
        raise ValueError(
            f"projectile_velocity_x: only {len(projectile)} projectile samples in window "
            f"{window}; no player-motion surrogate is allowed (ADR-020)."
        )
    t = [e["frame"] for e in projectile]
    x = [e["x"] for e in projectile]
    slope, _intercept, r2 = _fit_linear(t, x)
    value = abs(slope)
    results: dict[str, ExperimentConstant] = {
        "projectile_velocity_x": ExperimentConstant(
            value_per_frame=value,
            unit="norm_units_per_frame",
            value_per_second=_to_per_second(value),
            sample_count=len(projectile),
            experiment_id=exp_id,
            measurement_window=window,
            source_method="experiment_linear_fit",
            fit_quality=r2,
            needs_human_review=r2 < FIT_QUALITY_THRESHOLD,
            note="Slope of projectile x(t) over an isolated shot (ADR-020).",
        )
    }

    # spawn_delay = first projectile frame - fire-event frame (ground-truth input, ADR-023).
    player = _window_entries(entries, "player", window)
    fire_frames = [e["frame"] for e in player if "fire" in e.get("events", [])]
    if fire_frames:
        spawn_delay = projectile[0]["frame"] - min(fire_frames)
        results["spawn_delay_frames"] = ExperimentConstant(
            value_per_frame=float(spawn_delay),
            unit="frames",
            sample_count=1,
            experiment_id=exp_id,
            measurement_window=window,
            source_method="experiment_fire_to_spawn",
            needs_human_review=spawn_delay < 0,
            note="First projectile frame minus the fire-event frame.",
        )
    return results


def _measure_baseline(entries: list[dict], exp_id: str, window: tuple[int, int]) -> dict[str, ExperimentConstant]:
    player = _window_entries(entries, "player", window)
    if len(player) < MIN_LINEAR_SAMPLES:
        raise ValueError(f"baseline: only {len(player)} player samples in window {window}")
    x = np.asarray([e["x"] for e in player], dtype=float)
    y = np.asarray([e["y"] for e in player], dtype=float)
    noise = float(max(np.std(x), np.std(y)))
    return {
        "baseline_position_noise": ExperimentConstant(
            value_per_frame=noise,
            unit="norm_units",
            sample_count=len(player),
            experiment_id=exp_id,
            measurement_window=window,
            source_method="experiment_idle_std",
            note="max(std(x), std(y)) of the idle player — detection noise floor.",
        )
    }


_MEASURERS = {
    "baseline": _measure_baseline,
    "locomotion_velocity_x": _measure_locomotion,
    "jump_arc": _measure_jump_arc,
    "projectile": _measure_projectile,
}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def calibrate_experiment(
    plan: InputPlan,
    trace_entries: list[dict],
    window_override: tuple[int, int] | None = None,
) -> dict[str, ExperimentConstant]:
    """Measure the constant(s) for a single isolation experiment.

    Deterministic: identical (plan, trace, window) inputs yield identical constants.
    ``window_override`` lets the orchestrator (T20.4b) calibrate on an auto-detected
    stable sub-window instead of the declared one, making the run robust to timing jitter.
    """
    if plan.experiment is None:
        raise ValueError(f"plan '{plan.plan_name}' has no experiment block")
    exp = plan.experiment
    if window_override is not None:
        window = window_override
    else:
        window = (exp.measurement_window.start_frame, exp.measurement_window.end_frame)
    measurer = _MEASURERS[exp.isolated_variable]
    return measurer(trace_entries, exp.experiment_id, window)


def calibrate_experiment_files(plan_path: Path, trace_path: Path) -> dict[str, ExperimentConstant]:
    plan = load_input_plan(plan_path)
    raw = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    entries: list[dict] = raw["trace"]
    return calibrate_experiment(plan, entries)


def write_experiment_calibration_yaml(
    results: dict[str, ExperimentConstant],
    output_path: Path,
    merge: bool = True,
) -> None:
    """Write (or merge into) the public experiment-calibration YAML."""
    ensure_public_output_path(output_path)

    constants: dict[str, Any] = {}
    if merge and output_path.exists():
        existing = yaml.safe_load(output_path.read_text(encoding="utf-8")) or {}
        constants = existing.get("constants", {})

    for name, const in results.items():
        constants[name] = const.to_dict()

    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "ms_per_frame": MS_PER_FRAME,
        "generated_by": "T20.4 experiment_calibrator.py (ADR-024)",
        "constants": constants,
    }
    ensure_no_private_paths(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.dump(payload, default_flow_style=False, sort_keys=False))


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Deterministic calibration from one isolation experiment.")
    parser.add_argument("--plan", required=True, type=Path, help="experiment input plan YAML")
    parser.add_argument("--trace", required=True, type=Path, help="public trace JSON for that run")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("specs/calibration/gng_experiment_calibration.yaml"),
    )
    args = parser.parse_args()

    results = calibrate_experiment_files(args.plan, args.trace)
    write_experiment_calibration_yaml(results, args.output)
    for name, const in results.items():
        flag = " [needs_human_review]" if const.needs_human_review else ""
        q = f", r2={const.fit_quality:.4f}" if const.fit_quality is not None else ""
        print(f"  {name}: {const.value_per_frame:.6f}/frame (n={const.sample_count}{q}){flag}")


if __name__ == "__main__":
    main()

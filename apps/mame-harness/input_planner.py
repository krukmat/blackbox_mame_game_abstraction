from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import yaml

VALID_ACTIONS = {
    "insert_coin",
    "press_start",
    "move_left",
    "move_right",
    "move_up",
    "move_down",
    "jump",
    "fire",
    "pause",
    "noop",
}

# T20.3 / ADR-024 — designed isolation experiments.
ISOLATED_VARIABLES = {"baseline", "locomotion_velocity_x", "jump_arc", "projectile"}
EXPECTED_SIGNALS = {"none", "monotone_x", "parabolic_y", "linear_x"}

# Non-noop actions permitted inside an experiment's measurement_window, per isolated
# variable. Enforces that each experiment isolates exactly one mechanic (EC-1).
_ISOLATION_ALLOWED_ACTIONS: dict[str, set[str]] = {
    "baseline": set(),
    "locomotion_velocity_x": {"move_left", "move_right"},
    "jump_arc": {"jump"},
    "projectile": {"fire"},
}


@dataclass(slots=True)
class InputStep:
    action: str
    frames: int
    notes: str = ""


@dataclass(slots=True)
class FrameInput:
    frame_index: int
    action: str
    active_buttons: list[str]


@dataclass(slots=True)
class MeasurementWindow:
    """Absolute expanded-frame range [start_frame, end_frame] used for calibration."""

    start_frame: int
    end_frame: int


@dataclass(slots=True)
class ExperimentSpec:
    """T20.3 / ADR-024 — isolation-experiment metadata embedded in an input plan."""

    experiment_id: str
    isolated_variable: str
    measurement_window: MeasurementWindow
    expected_signal: str


@dataclass(slots=True)
class InputPlan:
    plan_name: str
    game_id: str
    steps: list[InputStep]
    experiment: "ExperimentSpec | None" = None

    def expand_to_frames(self) -> list[FrameInput]:
        expanded: list[FrameInput] = []
        frame_index = 0
        for step in self.steps:
            buttons = _buttons_for_action(step.action)
            for _ in range(step.frames):
                expanded.append(
                    FrameInput(
                        frame_index=frame_index,
                        action=step.action,
                        active_buttons=buttons,
                    )
                )
                frame_index += 1
        return expanded

    def export_to_json(self, path: Path) -> Path:
        payload = [
            {
                "frame": frame.frame_index,
                "buttons": list(frame.active_buttons),
            }
            for frame in self.expand_to_frames()
        ]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path


def _buttons_for_action(action: str) -> list[str]:
    mapping = {
        "insert_coin": ["coin"],
        "press_start": ["start"],
        "move_left": ["left"],
        "move_right": ["right"],
        "move_up": ["up"],
        "move_down": ["down"],
        "jump": ["button1"],
        "fire": ["button2"],
        "pause": ["pause"],
        "noop": [],
    }
    return list(mapping[action])


def load_input_plan(path: Path) -> InputPlan:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    steps: list[InputStep] = []
    for step in data.get("steps", []):
        action = str(step["action"])
        if action not in VALID_ACTIONS:
            raise ValueError(f"unsupported action: {action}")
        frames = int(step["frames"])
        if frames < 1:
            raise ValueError("frames must be >= 1")
        steps.append(
            InputStep(
                action=action,
                frames=frames,
                notes=str(step.get("notes", "")),
            )
        )

    plan = InputPlan(
        plan_name=str(data["plan_name"]),
        game_id=str(data["game_id"]),
        steps=steps,
        experiment=_parse_experiment(data.get("experiment")),
    )

    if plan.experiment is not None:
        _validate_experiment(plan)

    return plan


def _parse_experiment(raw: object) -> "ExperimentSpec | None":
    """Parse and shallow-validate the optional `experiment` block (T20.3 / ADR-024)."""
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("experiment must be a mapping")

    isolated = str(raw["isolated_variable"])
    if isolated not in ISOLATED_VARIABLES:
        raise ValueError(f"unsupported isolated_variable: {isolated}")

    signal = str(raw["expected_signal"])
    if signal not in EXPECTED_SIGNALS:
        raise ValueError(f"unsupported expected_signal: {signal}")

    window = raw["measurement_window"]
    start = int(window["start_frame"])
    end = int(window["end_frame"])
    if start < 0 or end < start:
        raise ValueError("measurement_window must satisfy 0 <= start_frame <= end_frame")

    return ExperimentSpec(
        experiment_id=str(raw["experiment_id"]),
        isolated_variable=isolated,
        measurement_window=MeasurementWindow(start_frame=start, end_frame=end),
        expected_signal=signal,
    )


def _validate_experiment(plan: "InputPlan") -> None:
    """Enforce that the measurement window is in range (EC-2) and isolates exactly
    one mechanic — only its allowed non-noop actions appear in the window (EC-1)."""
    experiment = plan.experiment
    assert experiment is not None
    frames = plan.expand_to_frames()
    total = len(frames)
    window = experiment.measurement_window

    if window.end_frame >= total:
        raise ValueError(
            f"measurement_window end_frame {window.end_frame} is outside the "
            f"expanded plan range [0, {total})"
        )

    allowed = _ISOLATION_ALLOWED_ACTIONS[experiment.isolated_variable]
    for frame in frames[window.start_frame : window.end_frame + 1]:
        if frame.action != "noop" and frame.action not in allowed:
            raise ValueError(
                f"experiment '{experiment.experiment_id}' is not isolated: action "
                f"'{frame.action}' at frame {frame.frame_index} is not allowed for "
                f"isolated_variable '{experiment.isolated_variable}'"
            )

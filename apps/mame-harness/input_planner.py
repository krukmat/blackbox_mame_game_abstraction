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
class InputPlan:
    plan_name: str
    game_id: str
    steps: list[InputStep]

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

    return InputPlan(
        plan_name=str(data["plan_name"]),
        game_id=str(data["game_id"]),
        steps=steps,
    )

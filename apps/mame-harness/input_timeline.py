"""T20.1 (ADR-023) — ground-truth input timeline loader and plan comparison.

The MAME Lua bridge (`scripts/mame_autoboot.lua`) records the *effective* per-frame
input state — injected plan OR human keyboard — to a private artifact
`evidence/private/run_<id>/logs/input_timeline.json`.

This module loads and validates that artifact and provides a deterministic comparison
against the exported input plan (used by the scripted-run determinism check, HP-1).
It reads only the public-shaped numeric/string timeline; it never reads frames, video,
or any private visual content.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# Canonical button vocabulary — must match BUTTON_ORDER in scripts/mame_autoboot.lua
# and packages/schemas/input_timeline.schema.json.
VALID_BUTTONS: frozenset[str] = frozenset(
    {"coin", "start", "left", "right", "up", "down", "button1", "button2"}
)


@dataclass(slots=True, frozen=True)
class InputTimelineEntry:
    """One frame of effective input state."""

    frame: int
    buttons: tuple[str, ...]


def parse_input_timeline(data: object) -> list[InputTimelineEntry]:
    """Validate and convert raw decoded JSON into timeline entries.

    Raises ValueError on any structural violation so malformed private artifacts
    fail loudly rather than silently corrupting downstream calibration.
    """
    if not isinstance(data, list):
        raise ValueError("input timeline must be a JSON array")

    entries: list[InputTimelineEntry] = []
    for index, raw in enumerate(data):
        if not isinstance(raw, dict):
            raise ValueError(f"timeline entry {index} is not an object")
        if "frame" not in raw or "buttons" not in raw:
            raise ValueError(f"timeline entry {index} missing 'frame' or 'buttons'")

        frame = raw["frame"]
        # bool is a subclass of int — reject it explicitly.
        if not isinstance(frame, int) or isinstance(frame, bool) or frame < 0:
            raise ValueError(f"timeline entry {index} has invalid frame: {frame!r}")

        buttons = raw["buttons"]
        if not isinstance(buttons, list):
            raise ValueError(f"timeline entry {index} buttons must be an array")

        seen: set[str] = set()
        for button in buttons:
            if not isinstance(button, str) or button not in VALID_BUTTONS:
                raise ValueError(
                    f"timeline entry {index} has invalid button: {button!r}"
                )
            if button in seen:
                raise ValueError(
                    f"timeline entry {index} has duplicate button: {button!r}"
                )
            seen.add(button)

        entries.append(InputTimelineEntry(frame=frame, buttons=tuple(buttons)))

    return entries


def load_input_timeline(path: Path) -> list[InputTimelineEntry]:
    """Load and validate an input_timeline.json file."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_input_timeline(raw)


def buttons_by_frame(timeline: list[InputTimelineEntry]) -> dict[int, frozenset[str]]:
    """Index the timeline by frame number with order-independent button sets."""
    return {entry.frame: frozenset(entry.buttons) for entry in timeline}


def _plan_buttons_by_frame(exported_plan: object) -> dict[int, frozenset[str]]:
    """Index the exported input-plan JSON (`[{frame, buttons}]`) by frame."""
    if not isinstance(exported_plan, list):
        raise ValueError("exported plan must be a JSON array")
    result: dict[int, frozenset[str]] = {}
    for index, raw in enumerate(exported_plan):
        if not isinstance(raw, dict) or "frame" not in raw or "buttons" not in raw:
            raise ValueError(f"plan entry {index} missing 'frame' or 'buttons'")
        result[int(raw["frame"])] = frozenset(raw["buttons"])
    return result


def timeline_matches_plan(
    timeline: list[InputTimelineEntry], exported_plan: object
) -> bool:
    """Return True iff a scripted-run timeline matches the injected plan (HP-1).

    Contract for a scripted run with no human input:
    - every frame named in the plan appears in the timeline with the same button set
      (order-independent);
    - every timeline frame not named in the plan carries no buttons (empty).
    """
    plan_frames = _plan_buttons_by_frame(exported_plan)
    timeline_frames = buttons_by_frame(timeline)

    for frame, expected in plan_frames.items():
        if timeline_frames.get(frame, frozenset()) != expected:
            return False

    for frame, actual in timeline_frames.items():
        if frame not in plan_frames and actual:
            return False

    return True

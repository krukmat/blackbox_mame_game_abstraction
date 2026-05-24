"""T10.7 ST2 — Regression tests for MIN_GROUND_STREAK debounce in _infer_events.

Tests verify that:
- jump_start is suppressed when the player has been grounded for fewer than
  MIN_GROUND_STREAK consecutive frames
- jump_start is emitted when the streak threshold is met
- the ground streak counter resets correctly on ascending
- the legacy_aggregate_compat path (game_id="gng") is unaffected by the debounce
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HARNESS_DIR = ROOT / "apps" / "mame-harness"
VISION_DIR = ROOT / "packages" / "vision"
VALIDATION_DIR = ROOT / "packages" / "validation"

for candidate in (ROOT, HARNESS_DIR, VISION_DIR, VALIDATION_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from frame_differ import FrameDiffStat, MotionBox
from input_planner import InputPlan, InputStep
from trace_extractor import MIN_GROUND_STREAK, extract_trace

FRAME_W = 256
FRAME_H = 224

# Arthur's center_y range accepted by ArthurSignature: 140–195 px
# height=25, width=22 → ar=0.88; center_y must stay in [140, 195]
_ARTHUR_W = 22
_ARTHUR_H = 25
_BASE_CX = 100.0
_BASE_CY = 170.0  # mid-range, well inside center_y_min/max


def _region(cx: float, cy: float) -> MotionBox:
    return MotionBox(
        x=int(cx - _ARTHUR_W / 2),
        y=int(cy - _ARTHUR_H / 2),
        width=_ARTHUR_W,
        height=_ARTHUR_H,
        center_x=cx,
        center_y=cy,
    )


def _stat(start_frame: int, cx: float, cy: float) -> FrameDiffStat:
    return FrameDiffStat(
        start_frame=start_frame,
        end_frame=start_frame + 1,
        changed_pixel_ratio=0.01,
        changed_regions=[_region(cx, cy)],
    )


def _plan_gngb(*actions: str) -> InputPlan:
    """Standard path — game_id='gngb' activates debounce."""
    return InputPlan(
        plan_name="debounce_test",
        game_id="gngb",
        steps=[InputStep(action=a, frames=1) for a in actions],
    )


def _plan_gng(*actions: str) -> InputPlan:
    """Legacy path — game_id='gng' bypasses debounce."""
    return InputPlan(
        plan_name="debounce_test_legacy",
        game_id="gng",
        steps=[InputStep(action=a, frames=1) for a in actions],
    )


def _jump_start_count(entries: list) -> int:
    return sum(1 for e in entries if e.entity_id == "player" and "jump_start" in e.events)


class TestMinGroundStreakDebounce:
    def test_jump_start_not_emitted_when_ground_streak_below_min(self) -> None:
        # Sequence:
        #   frame 0: idle (base position, no prev → vx=vy=0 → idle)
        #   frame 1: ascending (move up by enough to exceed VY_STILL)
        #   frame 2: idle (1 frame grounded — below MIN_GROUND_STREAK=3)
        #   frame 3: ascending again → second jump_start should NOT fire
        #
        # VY_STILL=0.005; frame_height=224 → Δy > 0.005*224 ≈ 1.12px to classify as ascending.
        # Moving center_y UP means cy decreases (screen-y coords, y=0 at top).
        up_cy = _BASE_CY - 4.0   # 4px up → vy = -4/224 ≈ -0.0179 < -VY_STILL → ascending
        diffs = [
            _stat(0, _BASE_CX, _BASE_CY),   # idle (first frame)
            _stat(1, _BASE_CX, up_cy),       # ascending: first jump_start (streak=0 < 3, suppressed)
            _stat(2, _BASE_CX, _BASE_CY),    # back to idle: streak becomes 1
            _stat(3, _BASE_CX, up_cy),       # ascending again: streak=1 < 3 → suppressed
        ]
        plan = _plan_gngb("noop", "noop", "noop", "noop")

        entries = extract_trace(diffs, plan, FRAME_W, FRAME_H)
        assert _jump_start_count(entries) == 0, (
            f"Expected 0 jump_start (streak < MIN_GROUND_STREAK={MIN_GROUND_STREAK}), "
            f"got {_jump_start_count(entries)}"
        )

    def test_jump_start_emitted_when_ground_streak_meets_min(self) -> None:
        # Sequence:
        #   frames 0–2: idle (3 consecutive grounded frames → streak reaches MIN_GROUND_STREAK)
        #   frame 3: ascending → jump_start SHOULD fire
        #
        # To stay idle between frames, keep the same cx/cy so vx=vy=0.
        up_cy = _BASE_CY - 4.0
        diffs = [
            _stat(0, _BASE_CX, _BASE_CY),  # idle, streak→1
            _stat(1, _BASE_CX, _BASE_CY),  # idle, streak→2
            _stat(2, _BASE_CX, _BASE_CY),  # idle, streak→3 (meets MIN)
            _stat(3, _BASE_CX, up_cy),     # ascending → jump_start emitted
        ]
        plan = _plan_gngb("noop", "noop", "noop", "noop")

        entries = extract_trace(diffs, plan, FRAME_W, FRAME_H)
        assert _jump_start_count(entries) == 1, (
            f"Expected 1 jump_start (streak = MIN_GROUND_STREAK={MIN_GROUND_STREAK}), "
            f"got {_jump_start_count(entries)}"
        )

    def test_ground_streak_resets_on_ascending(self) -> None:
        # Sequence:
        #   frames 0–4: idle × 5 (streak reaches 5 > MIN)
        #   frame 5: ascending → first jump_start fires, streak resets to 0
        #   frame 6: idle (streak→1, below MIN)
        #   frame 7: ascending → second jump_start should NOT fire (streak=1 < 3)
        up_cy = _BASE_CY - 4.0
        diffs = [
            _stat(0, _BASE_CX, _BASE_CY),  # idle streak→1
            _stat(1, _BASE_CX, _BASE_CY),  # idle streak→2
            _stat(2, _BASE_CX, _BASE_CY),  # idle streak→3
            _stat(3, _BASE_CX, _BASE_CY),  # idle streak→4
            _stat(4, _BASE_CX, _BASE_CY),  # idle streak→5
            _stat(5, _BASE_CX, up_cy),     # ascending → jump_start #1 fires, streak→0
            _stat(6, _BASE_CX, _BASE_CY),  # idle streak→1
            _stat(7, _BASE_CX, up_cy),     # ascending → streak=1 < 3, suppressed
        ]
        plan = _plan_gngb(*["noop"] * 8)

        entries = extract_trace(diffs, plan, FRAME_W, FRAME_H)
        assert _jump_start_count(entries) == 1, (
            f"Expected exactly 1 jump_start (streak resets on ascending), "
            f"got {_jump_start_count(entries)}"
        )

    def test_legacy_aggregate_path_unchanged(self) -> None:
        # game_id='gng' triggers legacy_aggregate_compat=True — debounce must NOT apply.
        # Even with a fresh entity (streak=0), jump_start should still be emitted.
        up_cy = _BASE_CY - 4.0
        diffs = [
            _stat(0, _BASE_CX, _BASE_CY),  # idle (first frame)
            _stat(1, _BASE_CX, up_cy),     # ascending — legacy path: jump_start fires despite streak=0
        ]
        plan = _plan_gng("noop", "noop")

        entries = extract_trace(diffs, plan, FRAME_W, FRAME_H)
        assert _jump_start_count(entries) == 1, (
            f"Expected 1 jump_start on legacy path (debounce disabled), "
            f"got {_jump_start_count(entries)}"
        )

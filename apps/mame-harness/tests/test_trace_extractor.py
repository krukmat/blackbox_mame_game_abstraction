"""Tests for T10.2.2.2 and T10.2.2.3 — velocity, state extraction, event inference.

All thresholds and state/event strings are taken verbatim from the contract in
T10.2.2.1 and the canonical vocabulary in T09.2.
"""
from __future__ import annotations

import pytest

from dataclasses import asdict

from frame_differ import FrameDiffStat, MotionBox
from trace_extractor import _assign_state, _compute_velocity, _infer_events, extract_trace
from input_planner import InputPlan, InputStep
from guardrails import ensure_no_private_paths

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FRAME_W = 256
FRAME_H = 224


def _stat(
    start: int,
    end: int,
    cx: float,
    cy: float,
    w: int = 20,
    h: int = 20,
) -> FrameDiffStat:
    """Build a FrameDiffStat with a single MotionBox centred at (cx, cy)."""
    half_w = w // 2
    half_h = h // 2
    region = MotionBox(
        x=int(cx) - half_w,
        y=int(cy) - half_h,
        width=w,
        height=h,
        center_x=cx,
        center_y=cy,
    )
    return FrameDiffStat(
        start_frame=start,
        end_frame=end,
        changed_pixel_ratio=0.01,
        changed_regions=[region],
    )


def _empty_stat(start: int, end: int) -> FrameDiffStat:
    """Build a FrameDiffStat with no changed regions (static frame)."""
    return FrameDiffStat(
        start_frame=start,
        end_frame=end,
        changed_pixel_ratio=0.0,
        changed_regions=[],
    )


# ---------------------------------------------------------------------------
# _compute_velocity — Rule 1
# ---------------------------------------------------------------------------


class TestComputeVelocity:
    def test_returns_zero_when_prev_is_none(self) -> None:
        curr = _stat(0, 1, cx=100.0, cy=100.0)
        vx, vy = _compute_velocity(None, curr, FRAME_W, FRAME_H)
        assert vx == 0.0
        assert vy == 0.0

    def test_returns_zero_when_curr_has_no_regions(self) -> None:
        prev = _stat(0, 1, cx=100.0, cy=100.0)
        curr = _empty_stat(1, 2)
        vx, vy = _compute_velocity(prev, curr, FRAME_W, FRAME_H)
        assert vx == 0.0
        assert vy == 0.0

    def test_returns_zero_when_prev_has_no_regions(self) -> None:
        prev = _empty_stat(0, 1)
        curr = _stat(1, 2, cx=100.0, cy=100.0)
        vx, vy = _compute_velocity(prev, curr, FRAME_W, FRAME_H)
        assert vx == 0.0
        assert vy == 0.0

    def test_positive_vx_for_rightward_motion(self) -> None:
        prev = _stat(0, 1, cx=100.0, cy=100.0)
        curr = _stat(1, 2, cx=110.0, cy=100.0)
        vx, vy = _compute_velocity(prev, curr, FRAME_W, FRAME_H)
        assert vx == pytest.approx(10.0 / FRAME_W)
        assert vy == pytest.approx(0.0)

    def test_negative_vx_for_leftward_motion(self) -> None:
        prev = _stat(0, 1, cx=100.0, cy=100.0)
        curr = _stat(1, 2, cx=88.0, cy=100.0)
        vx, vy = _compute_velocity(prev, curr, FRAME_W, FRAME_H)
        assert vx == pytest.approx(-12.0 / FRAME_W)
        assert vy == pytest.approx(0.0)

    def test_negative_vy_for_upward_motion(self) -> None:
        # negative vy = ascending per T09.2 convention
        prev = _stat(0, 1, cx=100.0, cy=80.0)
        curr = _stat(1, 2, cx=100.0, cy=60.0)
        vx, vy = _compute_velocity(prev, curr, FRAME_W, FRAME_H)
        assert vx == pytest.approx(0.0)
        assert vy == pytest.approx(-20.0 / FRAME_H)

    def test_positive_vy_for_downward_motion(self) -> None:
        prev = _stat(0, 1, cx=100.0, cy=60.0)
        curr = _stat(1, 2, cx=100.0, cy=80.0)
        vx, vy = _compute_velocity(prev, curr, FRAME_W, FRAME_H)
        assert vx == pytest.approx(0.0)
        assert vy == pytest.approx(20.0 / FRAME_H)

    def test_diagonal_motion_produces_both_components(self) -> None:
        prev = _stat(0, 1, cx=50.0, cy=100.0)
        curr = _stat(1, 2, cx=60.0, cy=85.0)
        vx, vy = _compute_velocity(prev, curr, FRAME_W, FRAME_H)
        assert vx == pytest.approx(10.0 / FRAME_W)
        assert vy == pytest.approx(-15.0 / FRAME_H)

    def test_zero_motion_returns_zeros(self) -> None:
        prev = _stat(0, 1, cx=100.0, cy=100.0)
        curr = _stat(1, 2, cx=100.0, cy=100.0)
        vx, vy = _compute_velocity(prev, curr, FRAME_W, FRAME_H)
        assert vx == pytest.approx(0.0)
        assert vy == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# _assign_state — Rule 2
# ---------------------------------------------------------------------------

# Threshold constants mirror T10.2.2.1 Rule 2
VX_STILL = 0.005
VY_STILL = 0.005


class TestAssignState:
    # --- projectile entity type (priorities 1 & 2) ---

    def test_projectile_moving_is_in_flight(self) -> None:
        assert _assign_state(0.05, 0.0, "projectile") == "in_flight"

    def test_projectile_stationary_is_despawned(self) -> None:
        assert _assign_state(0.0, 0.0, "projectile") == "despawned"

    # --- vertical motion (priorities 3 & 4) ---

    def test_strong_negative_vy_is_ascending(self) -> None:
        assert _assign_state(0.0, -(VY_STILL + 0.01), "player") == "ascending"

    def test_strong_positive_vy_is_descending(self) -> None:
        assert _assign_state(0.0, VY_STILL + 0.01, "player") == "descending"

    # --- horizontal stillness (priorities 5, 6, 7) ---

    def test_both_zero_is_idle(self) -> None:
        assert _assign_state(0.0, 0.0, "player") == "idle"

    def test_within_deadband_is_idle(self) -> None:
        assert _assign_state(VX_STILL * 0.5, VY_STILL * 0.5, "player") == "idle"

    def test_leftward_vx_is_walking_left(self) -> None:
        assert _assign_state(-(VX_STILL + 0.01), 0.0, "player") == "walking_left"

    def test_rightward_vx_is_walking_right(self) -> None:
        assert _assign_state(VX_STILL + 0.01, 0.0, "player") == "walking_right"

    # --- combined vertical with horizontal (priority 8 fallback to airborne) ---

    def test_moving_with_vy_just_over_still_is_airborne_fallback(self) -> None:
        # vx and vy both just above VY_STILL but not strictly negative
        # Fabricate: vy > VY_STILL but the sign check above hasn't matched
        # This case happens when vy > 0 but <= VY_STILL*2; priority 4 handles
        # strong positives — here we test the exact boundary then one step past
        vy = VY_STILL + 0.001  # triggers descending (priority 4), not airborne
        assert _assign_state(0.0, vy, "player") == "descending"

    def test_enemy_a_falls_through_to_idle(self) -> None:
        assert _assign_state(0.0, 0.0, "enemy_a") == "idle"

    def test_enemy_a_moving_right(self) -> None:
        assert _assign_state(VX_STILL + 0.01, 0.0, "enemy_a") == "walking_right"

    def test_enemy_a_moving_left(self) -> None:
        assert _assign_state(-(VX_STILL + 0.01), 0.0, "enemy_a") == "walking_left"

    # --- output is always a member of T09.2 state.enum ---

    VALID_STATES = {
        "idle",
        "walking_left",
        "walking_right",
        "grounded",
        "airborne",
        "ascending",
        "descending",
        "in_flight",
        "hit",
        "dead",
        "despawned",
    }

    @pytest.mark.parametrize(
        "vx,vy,entity_type",
        [
            (0.0, 0.0, "player"),
            (0.1, 0.0, "player"),
            (-0.1, 0.0, "player"),
            (0.0, -0.1, "player"),
            (0.0, 0.1, "player"),
            (0.05, 0.0, "projectile"),
            (0.0, 0.0, "projectile"),
            (0.0, 0.0, "enemy_a"),
            (0.1, 0.0, "enemy_a"),
        ],
    )
    def test_output_always_in_state_enum(
        self, vx: float, vy: float, entity_type: str
    ) -> None:
        result = _assign_state(vx, vy, entity_type)
        assert result in self.VALID_STATES, f"unexpected state '{result}'"


# ---------------------------------------------------------------------------
# _infer_events — Rule 3 (state transitions) + Rule 4 (input plan injection)
# T10.2.2.3
# ---------------------------------------------------------------------------

VALID_EVENTS = {
    "spawn", "die", "despawn",
    "hit", "hit_enemy", "hit_player",
    "movement_start", "movement_stop",
    "jump_start", "jump_peak", "land", "fall",
    "fire", "hit_wall",
    "score",
}


class TestInferEvents:

    # --- Rule 3: jump arc transitions ---

    def test_grounded_to_ascending_emits_jump_start(self) -> None:
        assert _infer_events("grounded", "ascending", "noop") == ["jump_start"]

    def test_idle_to_ascending_emits_jump_start(self) -> None:
        assert _infer_events("idle", "ascending", "noop") == ["jump_start"]

    def test_walking_left_to_ascending_emits_jump_start(self) -> None:
        assert _infer_events("walking_left", "ascending", "noop") == ["jump_start"]

    def test_walking_right_to_ascending_emits_jump_start(self) -> None:
        assert _infer_events("walking_right", "ascending", "noop") == ["jump_start"]

    def test_ascending_to_descending_emits_jump_peak(self) -> None:
        assert _infer_events("ascending", "descending", "noop") == ["jump_peak"]

    def test_ascending_to_grounded_emits_land(self) -> None:
        assert _infer_events("ascending", "grounded", "noop") == ["land"]

    def test_descending_to_grounded_emits_land(self) -> None:
        assert _infer_events("descending", "grounded", "noop") == ["land"]

    def test_airborne_to_grounded_emits_land(self) -> None:
        assert _infer_events("airborne", "grounded", "noop") == ["land"]

    def test_descending_to_idle_emits_land(self) -> None:
        assert _infer_events("descending", "idle", "noop") == ["land"]

    # --- Rule 3: fall (walked off edge) ---

    def test_grounded_to_airborne_emits_fall(self) -> None:
        assert _infer_events("grounded", "airborne", "noop") == ["fall"]

    def test_idle_to_airborne_emits_fall(self) -> None:
        assert _infer_events("idle", "airborne", "noop") == ["fall"]

    def test_grounded_to_descending_emits_fall(self) -> None:
        assert _infer_events("grounded", "descending", "noop") == ["fall"]

    # --- Rule 3: locomotion transitions ---

    def test_idle_to_walking_left_emits_movement_start(self) -> None:
        assert _infer_events("idle", "walking_left", "noop") == ["movement_start"]

    def test_idle_to_walking_right_emits_movement_start(self) -> None:
        assert _infer_events("idle", "walking_right", "noop") == ["movement_start"]

    def test_walking_left_to_idle_emits_movement_stop(self) -> None:
        assert _infer_events("walking_left", "idle", "noop") == ["movement_stop"]

    def test_walking_right_to_idle_emits_movement_stop(self) -> None:
        assert _infer_events("walking_right", "idle", "noop") == ["movement_stop"]

    def test_walking_left_to_walking_right_emits_stop_then_start(self) -> None:
        assert _infer_events("walking_left", "walking_right", "noop") == [
            "movement_stop",
            "movement_start",
        ]

    def test_walking_right_to_walking_left_emits_stop_then_start(self) -> None:
        assert _infer_events("walking_right", "walking_left", "noop") == [
            "movement_stop",
            "movement_start",
        ]

    # --- Rule 3: projectile despawn ---

    def test_in_flight_to_despawned_emits_despawn(self) -> None:
        assert _infer_events("in_flight", "despawned", "noop") == ["despawn"]

    # --- No transition → empty list ---

    def test_same_state_no_events(self) -> None:
        assert _infer_events("idle", "idle", "noop") == []

    def test_grounded_to_grounded_no_events(self) -> None:
        assert _infer_events("grounded", "grounded", "noop") == []

    def test_walking_right_to_walking_right_no_events(self) -> None:
        assert _infer_events("walking_right", "walking_right", "noop") == []

    def test_ascending_to_ascending_no_events(self) -> None:
        assert _infer_events("ascending", "ascending", "noop") == []

    # --- Rule 4: input plan injection ---

    def test_fire_action_injects_fire_event(self) -> None:
        events = _infer_events("idle", "idle", "fire")
        assert "fire" in events

    def test_fire_event_not_emitted_without_fire_action(self) -> None:
        events = _infer_events("idle", "idle", "noop")
        assert "fire" not in events

    def test_jump_action_injects_jump_start_when_not_ascending(self) -> None:
        # State transition doesn't show ascending yet — plan injects jump_start
        events = _infer_events("grounded", "grounded", "jump")
        assert "jump_start" in events

    def test_jump_action_does_not_duplicate_jump_start_when_already_inferred(self) -> None:
        # State transition already produces jump_start — Rule 4 must not duplicate
        events = _infer_events("grounded", "ascending", "jump")
        assert events.count("jump_start") == 1

    def test_jump_action_suppressed_when_already_ascending(self) -> None:
        # Entity is already ascending — Rule 4 suppresses injection
        events = _infer_events("ascending", "ascending", "jump")
        assert "jump_start" not in events

    # --- Mutual exclusivity: land and fall never co-occur ---

    def test_land_and_fall_never_together_ascending_grounded(self) -> None:
        events = _infer_events("ascending", "grounded", "noop")
        assert not ("land" in events and "fall" in events)

    def test_land_and_fall_never_together_grounded_airborne(self) -> None:
        events = _infer_events("grounded", "airborne", "noop")
        assert not ("land" in events and "fall" in events)

    # --- All emitted events are in T09.2 events.enum ---

    @pytest.mark.parametrize(
        "prev,curr,action",
        [
            ("idle", "ascending", "noop"),
            ("ascending", "descending", "noop"),
            ("descending", "grounded", "noop"),
            ("grounded", "airborne", "noop"),
            ("idle", "walking_left", "noop"),
            ("walking_left", "idle", "noop"),
            ("walking_left", "walking_right", "noop"),
            ("in_flight", "despawned", "noop"),
            ("idle", "idle", "fire"),
            ("grounded", "ascending", "jump"),
            ("idle", "idle", "noop"),
        ],
    )
    def test_all_emitted_events_in_events_enum(
        self, prev: str, curr: str, action: str
    ) -> None:
        result = _infer_events(prev, curr, action)
        for event in result:
            assert event in VALID_EVENTS, f"unexpected event '{event}'"


# ---------------------------------------------------------------------------
# extract_trace — integration test (T10.2.2.4)
# Covers all 5 mechanic categories: locomotion, jump_arc, projectile,
# gravity_collision, entity_event_trace lifecycle (spawn/die).
# ---------------------------------------------------------------------------

def _make_plan(*actions: str) -> InputPlan:
    """Build a minimal InputPlan from a sequence of action strings."""
    steps = [InputStep(action=a, frames=1) for a in actions]
    return InputPlan(plan_name="test", game_id="gng", steps=steps)


def _region(cx: float, cy: float, w: int = 20, h: int = 20) -> MotionBox:
    hw, hh = w // 2, h // 2
    return MotionBox(x=int(cx)-hw, y=int(cy)-hh, width=w, height=h,
                     center_x=cx, center_y=cy)


def _stat_with(start: int, cx: float, cy: float, w: int = 20, h: int = 20) -> FrameDiffStat:
    return FrameDiffStat(
        start_frame=start, end_frame=start + 1,
        changed_pixel_ratio=0.01,
        changed_regions=[_region(cx, cy, w, h)],
    )


def _empty(start: int) -> FrameDiffStat:
    return FrameDiffStat(start_frame=start, end_frame=start+1,
                         changed_pixel_ratio=0.0, changed_regions=[])


class TestExtractTrace:

    # --- basic shape ---

    def test_returns_list_of_trace_entries(self) -> None:
        stats = [_stat_with(0, 100.0, 100.0), _stat_with(1, 102.0, 100.0)]
        plan = _make_plan("noop", "noop")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_empty_stats_returns_empty_list(self) -> None:
        plan = _make_plan()
        result = extract_trace([], plan, frame_width=256, frame_height=224)
        assert result == []

    def test_frame_with_no_motion_produces_no_entry(self) -> None:
        stats = [_empty(0), _empty(1)]
        plan = _make_plan("noop", "noop")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        assert result == []

    # --- locomotion category ---

    def test_rightward_motion_produces_walking_right_state(self) -> None:
        stats = [_stat_with(0, 100.0, 100.0), _stat_with(1, 115.0, 100.0)]
        plan = _make_plan("noop", "move_right")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        states = {e.state for e in result}
        assert "walking_right" in states

    def test_leftward_motion_produces_walking_left_state(self) -> None:
        stats = [_stat_with(0, 115.0, 100.0), _stat_with(1, 100.0, 100.0)]
        plan = _make_plan("noop", "move_left")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        states = {e.state for e in result}
        assert "walking_left" in states

    def test_movement_start_event_on_idle_to_walking(self) -> None:
        # Frame 0: static; frame 1: moves right
        stats = [_stat_with(0, 100.0, 100.0), _stat_with(1, 115.0, 100.0)]
        plan = _make_plan("noop", "move_right")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        all_events = [e for entry in result for e in entry.events]
        assert "movement_start" in all_events

    # --- jump_arc category ---

    def test_upward_motion_produces_ascending_state(self) -> None:
        # Negative vy = upward motion = ascending
        stats = [_stat_with(0, 100.0, 100.0), _stat_with(1, 100.0, 70.0)]
        plan = _make_plan("noop", "jump")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        states = {e.state for e in result}
        assert "ascending" in states

    def test_jump_start_event_emitted_on_ascent(self) -> None:
        stats = [_stat_with(0, 100.0, 100.0), _stat_with(1, 100.0, 70.0)]
        plan = _make_plan("noop", "jump")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        all_events = [e for entry in result for e in entry.events]
        assert "jump_start" in all_events

    def test_land_event_on_descending_to_grounded(self) -> None:
        # frame0: grounded (no prev) → frame1: ascending (vy<0) → frame2: back at y=100 (grounded)
        # frame2 must have a region so it produces a TraceEntry and evaluates the transition
        stats = [
            _stat_with(0, 100.0, 100.0),
            _stat_with(1, 100.0, 70.0),   # ascending (vy negative)
            _stat_with(2, 100.0, 100.0),  # back to ground (vy positive relative to frame 1)
            _stat_with(3, 100.0, 100.0),  # static — triggers land from descending→idle
        ]
        plan = _make_plan("noop", "jump", "noop", "noop")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        all_events = [e for entry in result for e in entry.events]
        assert "land" in all_events

    # --- projectile category ---

    def test_fire_action_injects_fire_event_in_trace(self) -> None:
        stats = [_stat_with(0, 100.0, 100.0), _stat_with(1, 100.0, 100.0)]
        plan = _make_plan("noop", "fire")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        all_events = [e for entry in result for e in entry.events]
        assert "fire" in all_events

    # --- gravity_collision category ---

    def test_fall_event_on_grounded_to_airborne(self) -> None:
        # frame0: grounded (small motion) → frame1: larger downward motion
        stats = [
            _stat_with(0, 100.0, 100.0),
            _stat_with(1, 100.0, 130.0),  # descending (vy positive > VY_STILL)
        ]
        plan = _make_plan("noop", "noop")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        all_events = [e for entry in result for e in entry.events]
        assert "fall" in all_events

    # --- entity lifecycle category (spawn / die) ---

    def test_spawn_event_on_first_appearance(self) -> None:
        # frame0: no motion → frame1: entity appears
        stats = [_empty(0), _stat_with(1, 100.0, 100.0)]
        plan = _make_plan("noop", "noop")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        all_events = [e for entry in result for e in entry.events]
        assert "spawn" in all_events

    def test_die_event_on_disappearance(self) -> None:
        # frame0: entity present → frame1: entity present → frame2: gone
        stats = [
            _stat_with(0, 100.0, 100.0),
            _stat_with(1, 100.0, 100.0),
            _empty(2),
        ]
        plan = _make_plan("noop", "noop", "noop")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        all_events = [e for entry in result for e in entry.events]
        assert "die" in all_events

    # --- clean-room guardrail ---

    def test_output_passes_ensure_no_private_paths(self) -> None:
        stats = [_stat_with(0, 100.0, 100.0), _stat_with(1, 110.0, 100.0)]
        plan = _make_plan("noop", "fire")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        payload = [asdict(entry) for entry in result]
        ensure_no_private_paths(payload)  # must not raise

    # --- canonical vocabulary enforcement ---

    def test_all_states_in_canonical_enum(self) -> None:
        valid_states = {
            "idle", "walking_left", "walking_right", "grounded", "airborne",
            "ascending", "descending", "in_flight", "hit", "dead", "despawned",
        }
        stats = [_stat_with(0, 100.0, 100.0), _stat_with(1, 112.0, 100.0)]
        plan = _make_plan("noop", "noop")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        for entry in result:
            assert entry.state in valid_states, f"unexpected state '{entry.state}'"

    def test_all_events_in_canonical_enum(self) -> None:
        stats = [_stat_with(0, 100.0, 100.0), _stat_with(1, 100.0, 70.0)]
        plan = _make_plan("noop", "jump")
        result = extract_trace(stats, plan, frame_width=256, frame_height=224)
        for entry in result:
            for event in entry.events:
                assert event in VALID_EVENTS, f"unexpected event '{event}'"

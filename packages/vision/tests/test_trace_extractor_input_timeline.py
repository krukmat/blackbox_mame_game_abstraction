"""T20.2 / ADR-023 — event sourcing from the ground-truth input timeline.

Verifies that input-driven player events come from real button edges and that the
CV (Rule 3) jump_start is suppressed in timeline mode, while the legacy plan-based
path is unchanged.
"""
from __future__ import annotations

from trace_extractor import _infer_events


# --------------------------------------------------------------------------- #
# Timeline mode — button edges are authoritative
# --------------------------------------------------------------------------- #


def test_timeline_jump_start_from_button_edge_when_grounded() -> None:
    # button1 edge from a grounded precondition -> jump_start.
    events = _infer_events("idle", "idle", "noop", input_events=["jump_start"])
    assert events == ["jump_start"]


def test_timeline_suppresses_cv_jump_start() -> None:
    # CV transition grounded -> ascending would emit jump_start in legacy mode, but
    # in timeline mode with no button edge it must NOT.
    events = _infer_events("grounded", "ascending", "noop", input_events=[])
    assert "jump_start" not in events


def test_timeline_no_double_jump_start() -> None:
    # Even if both the CV transition and the button edge occur, only one jump_start.
    events = _infer_events("grounded", "ascending", "noop", input_events=["jump_start"])
    assert events.count("jump_start") == 1


def test_timeline_jump_start_ignored_mid_air() -> None:
    # A no-op button1 press while already ascending is not a jump_start.
    events = _infer_events("ascending", "ascending", "noop", input_events=["jump_start"])
    assert "jump_start" not in events


def test_timeline_fire_from_button_edge() -> None:
    events = _infer_events("idle", "idle", "noop", input_events=["fire"])
    assert events == ["fire"]


def test_timeline_no_input_events_emits_nothing_extra() -> None:
    events = _infer_events("idle", "idle", "noop", input_events=[])
    assert events == []


# --------------------------------------------------------------------------- #
# Legacy mode — unchanged behavior
# --------------------------------------------------------------------------- #


def test_legacy_jump_action_still_emits_jump_start() -> None:
    events = _infer_events("idle", "idle", "jump")
    assert "jump_start" in events


def test_legacy_cv_jump_start_preserved() -> None:
    events = _infer_events("grounded", "ascending", "noop")
    assert events == ["jump_start"]

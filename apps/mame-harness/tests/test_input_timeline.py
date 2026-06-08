"""T20.1 (ADR-023) — tests for the ground-truth input timeline loader and the
plan-comparison helper, plus structural guardrails on the Lua bridge.

The MAME-produced equality (a real scripted capture's timeline == injected plan) is
an integration check the operator runs with a ROM; it cannot run in CI. These tests
cover the public-shaped Python contract that T20.2 will consume, and statically
enforce that the Lua never prints the private timeline path to stdout (EC-1).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from conftest import ROOT
from input_timeline import (
    VALID_BUTTONS,
    InputTimelineEntry,
    load_input_timeline,
    parse_input_timeline,
    timeline_matches_plan,
)

LUA_PATH = ROOT / "scripts" / "mame_autoboot.lua"
SCHEMA_PATH = ROOT / "packages" / "schemas" / "input_timeline.schema.json"


# --------------------------------------------------------------------------- #
# Parser — happy paths
# --------------------------------------------------------------------------- #


def test_parse_records_human_buttons() -> None:
    # HP-2 proxy: a manual-style timeline parses with the right button sets.
    data = [
        {"frame": 1500, "buttons": ["right", "button2"]},
        {"frame": 1501, "buttons": ["right"]},
    ]
    entries = parse_input_timeline(data)
    assert entries[0] == InputTimelineEntry(frame=1500, buttons=("right", "button2"))
    assert entries[1].buttons == ("right",)


def test_parse_empty_buttons_frame() -> None:
    # HP-3: a frame with no input is recorded explicitly as empty, not omitted.
    entries = parse_input_timeline([{"frame": 0, "buttons": []}])
    assert entries == [InputTimelineEntry(frame=0, buttons=())]


def test_load_input_timeline_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "input_timeline.json"
    path.write_text(
        json.dumps([{"frame": 950, "buttons": ["coin"]}]), encoding="utf-8"
    )
    entries = load_input_timeline(path)
    assert entries == [InputTimelineEntry(frame=950, buttons=("coin",))]


# --------------------------------------------------------------------------- #
# Parser — edge cases
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "data",
    [
        {"frame": 0, "buttons": []},  # not an array
        [{"buttons": []}],  # missing frame
        [{"frame": 0}],  # missing buttons
        [{"frame": -1, "buttons": []}],  # negative frame
        [{"frame": True, "buttons": []}],  # bool is not a valid frame
        [{"frame": 0, "buttons": ["jump"]}],  # unknown button
        [{"frame": 0, "buttons": "right"}],  # buttons not an array
        [{"frame": 0, "buttons": ["right", "right"]}],  # EC-2: duplicate button
    ],
)
def test_parse_rejects_malformed(data: object) -> None:
    with pytest.raises(ValueError):
        parse_input_timeline(data)


# --------------------------------------------------------------------------- #
# timeline_matches_plan — HP-1 determinism + negatives
# --------------------------------------------------------------------------- #


def test_timeline_matches_plan_scripted_equal() -> None:
    # HP-1: scripted run with extra empty frames still matches the plan.
    plan = [{"frame": 950, "buttons": ["coin"]}, {"frame": 1025, "buttons": ["start"]}]
    timeline = parse_input_timeline(
        [
            {"frame": 949, "buttons": []},
            {"frame": 950, "buttons": ["coin"]},
            {"frame": 1025, "buttons": ["start"]},
            {"frame": 1026, "buttons": []},
        ]
    )
    assert timeline_matches_plan(timeline, plan) is True


def test_timeline_matches_plan_button_order_independent() -> None:
    plan = [{"frame": 5, "buttons": ["right", "button2"]}]
    timeline = parse_input_timeline([{"frame": 5, "buttons": ["button2", "right"]}])
    assert timeline_matches_plan(timeline, plan) is True


def test_timeline_mismatch_on_different_buttons() -> None:
    plan = [{"frame": 5, "buttons": ["right"]}]
    timeline = parse_input_timeline([{"frame": 5, "buttons": ["left"]}])
    assert timeline_matches_plan(timeline, plan) is False


def test_timeline_mismatch_on_unexpected_human_input() -> None:
    # A "scripted" timeline that carries input on a non-plan frame is not a match.
    plan = [{"frame": 5, "buttons": ["right"]}]
    timeline = parse_input_timeline(
        [{"frame": 5, "buttons": ["right"]}, {"frame": 6, "buttons": ["button1"]}]
    )
    assert timeline_matches_plan(timeline, plan) is False


def test_timeline_mismatch_on_missing_plan_frame() -> None:
    plan = [{"frame": 5, "buttons": ["right"]}, {"frame": 6, "buttons": ["left"]}]
    timeline = parse_input_timeline([{"frame": 5, "buttons": ["right"]}])
    assert timeline_matches_plan(timeline, plan) is False


# --------------------------------------------------------------------------- #
# Schema / Lua / Python vocabulary consistency
# --------------------------------------------------------------------------- #


def test_schema_enum_matches_valid_buttons() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    enum = schema["items"]["properties"]["buttons"]["items"]["enum"]
    assert set(enum) == set(VALID_BUTTONS)


def test_lua_button_order_matches_valid_buttons() -> None:
    lua = LUA_PATH.read_text(encoding="utf-8")
    match = re.search(r"local BUTTON_ORDER = \{([^}]*)\}", lua)
    assert match is not None, "BUTTON_ORDER not found in Lua"
    names = set(re.findall(r'"([a-z0-9]+)"', match.group(1)))
    assert names == set(VALID_BUTTONS)


# --------------------------------------------------------------------------- #
# EC-1 — the Lua must never print the private timeline path to stdout
# --------------------------------------------------------------------------- #


def test_lua_timeline_stdout_carries_no_path() -> None:
    lua = LUA_PATH.read_text(encoding="utf-8")
    # The three timeline stdout markers must be path-free literals (no `.. path`).
    assert 'print("blackbox_harness:input_timeline:no_path")' in lua
    assert 'print("blackbox_harness:input_timeline:unwritable")' in lua
    assert (
        'print("blackbox_harness:input_timeline:written:" .. tostring(#input_timeline))'
        in lua
    )
    # No timeline stdout line may concatenate a path-bearing variable.
    for line in lua.splitlines():
        if "input_timeline:" in line and "print(" in line:
            assert ".. path" not in line and ".. explicit" not in line


def test_lua_wires_timeline_env_var() -> None:
    lua = LUA_PATH.read_text(encoding="utf-8")
    assert "BLACKBOX_INPUT_TIMELINE_PATH" in lua
    assert "record_effective_state" in lua
    assert "write_timeline()" in lua

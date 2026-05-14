from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import ROOT
from input_planner import load_input_plan


def test_load_input_plan() -> None:
    plan = load_input_plan(ROOT / "plans/basic_controls.yaml")
    assert plan.plan_name == "basic_controls"
    assert plan.game_id == "sample_game"
    assert [step.action for step in plan.steps] == [
        "insert_coin",
        "press_start",
        "move_left",
        "move_right",
    ]
    expanded = plan.expand_to_frames()
    assert len(expanded) == 130
    assert expanded[0].active_buttons == ["coin"]
    assert expanded[-1].active_buttons == ["right"]


def test_load_input_plan_rejects_unknown_action(tmp_path: Path) -> None:
    plan_path = tmp_path / "invalid_plan.yaml"
    plan_path.write_text(
        "plan_name: broken\n"
        "game_id: demo\n"
        "steps:\n"
        "  - action: teleport\n"
        "    frames: 2\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_input_plan(plan_path)


def test_export_to_json_writes_flat_frame_button_array(tmp_path: Path) -> None:
    plan = load_input_plan(ROOT / "plans/basic_controls.yaml")

    output = plan.export_to_json(tmp_path / "private" / "input_plan.json")

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert output.exists()
    assert payload[0] == {"frame": 0, "buttons": ["coin"]}
    assert payload[29] == {"frame": 29, "buttons": ["coin"]}
    assert payload[30] == {"frame": 30, "buttons": ["start"]}
    assert payload[-1] == {"frame": 129, "buttons": ["right"]}

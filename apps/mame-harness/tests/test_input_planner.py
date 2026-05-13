from __future__ import annotations

from pathlib import Path

import pytest

from input_planner import load_input_plan


def test_load_input_plan() -> None:
    plan = load_input_plan(Path("plans/basic_controls.yaml"))
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

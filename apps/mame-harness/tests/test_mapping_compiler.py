from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conftest import ROOT
from guardrails import ensure_no_private_paths, ensure_public_output_path
from input_planner import VALID_ACTIONS, load_input_plan
from mapping_compiler import build_compiled_input_plan, compile_mapping_files
from mapping_profiles import (
    ControllerProfile,
    DeviceProfile,
    GameActionProfile,
    InputSequence,
    load_mapping_profile,
)


DEVICE_PROFILE_PATH = ROOT / "profiles" / "devices" / "keyboard_default.yaml"
CONTROLLER_PROFILE_PATH = ROOT / "profiles" / "controllers" / "arcade_2button.yaml"
GAME_ACTION_PROFILE_PATH = ROOT / "profiles" / "games" / "gngb" / "default_actions.yaml"
INPUT_SEQUENCE_PATH = ROOT / "plans" / "sequences" / "gng_smoke_sequence.yaml"
GNG_BOOT_SEQUENCE_PATH = ROOT / "plans" / "sequences" / "gng_boot_only.yaml"
GNG_GAMEPLAY_SEQUENCE_PATH = ROOT / "plans" / "sequences" / "gng_gameplay.yaml"
LEGACY_GNG_BOOT_PLAN_PATH = ROOT / "plans" / "gng_boot_only.yaml"
LEGACY_GNG_GAMEPLAY_PLAN_PATH = ROOT / "plans" / "gng_gameplay.yaml"
GENERATED_GNG_BOOT_PLAN_PATH = ROOT / "plans" / "generated" / "gng_boot_only.yaml"
GENERATED_GNG_GAMEPLAY_PLAN_PATH = ROOT / "plans" / "generated" / "gng_gameplay.yaml"


def test_sample_profiles_compile_smoke_sequence(tmp_path: Path) -> None:
    output_path = tmp_path / "plans" / "generated" / "gng_smoke_compiled.yaml"

    written = compile_mapping_files(
        device_profile_path=DEVICE_PROFILE_PATH,
        controller_profile_path=CONTROLLER_PROFILE_PATH,
        game_action_profile_path=GAME_ACTION_PROFILE_PATH,
        input_sequence_path=INPUT_SEQUENCE_PATH,
        output_path=output_path,
    )

    assert written == output_path
    assert written.exists()

    compiled_plan = load_input_plan(written)
    assert compiled_plan.plan_name == "gng_smoke_sequence"
    assert compiled_plan.game_id == "gngb"
    assert [step.action for step in compiled_plan.steps] == [
        "insert_coin",
        "press_start",
        "move_right",
        "jump",
        "fire",
    ]


def test_compiled_output_contains_only_allowed_semantic_actions() -> None:
    payload = build_compiled_input_plan(
        device_profile=_load_typed(DEVICE_PROFILE_PATH, DeviceProfile),
        controller_profile=_load_typed(CONTROLLER_PROFILE_PATH, ControllerProfile),
        game_action_profile=_load_typed(GAME_ACTION_PROFILE_PATH, GameActionProfile),
        input_sequence=_load_typed(INPUT_SEQUENCE_PATH, InputSequence),
    )

    compiled_actions = {step["action"] for step in payload["steps"]}
    assert compiled_actions <= VALID_ACTIONS


def test_unknown_sequence_control_fails_when_not_declared_by_controller(tmp_path: Path) -> None:
    controller_path = tmp_path / "controller_without_start.yaml"
    controller_path.write_text(
        "schema_version: 1\n"
        "profile_type: controller_profile\n"
        "id: no_start_controller\n"
        "canonical_controls:\n"
        "  - dpad_left\n"
        "  - dpad_right\n"
        "  - dpad_up\n"
        "  - dpad_down\n"
        "  - south\n"
        "  - east\n"
        "  - select\n"
        "  - noop\n"
        "constraints:\n"
        "  required:\n"
        "    - dpad_left\n"
        "    - dpad_right\n"
        "    - south\n"
        "    - east\n"
        "    - select\n"
        "  optional:\n"
        "    - dpad_up\n"
        "    - dpad_down\n"
        "    - noop\n"
        "metadata:\n"
        "  clean_room_safe: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="input_sequence control 'start' is not declared"):
        compile_mapping_files(
            device_profile_path=DEVICE_PROFILE_PATH,
            controller_profile_path=controller_path,
            game_action_profile_path=GAME_ACTION_PROFILE_PATH,
            input_sequence_path=INPUT_SEQUENCE_PATH,
            output_path=tmp_path / "plans" / "generated" / "broken.yaml",
        )


def test_missing_game_action_mapping_fails(tmp_path: Path) -> None:
    game_action_path = tmp_path / "missing_jump_mapping.yaml"
    game_action_path.write_text(
        "schema_version: 1\n"
        "profile_type: game_action_profile\n"
        "id: gngb_missing_jump\n"
        "source_profile: gng\n"
        "driver: gngb\n"
        "canonical_to_action:\n"
        "  dpad_left: move_left\n"
        "  dpad_right: move_right\n"
        "  dpad_up: move_up\n"
        "  dpad_down: move_down\n"
        "  east: fire\n"
        "  start: press_start\n"
        "  select: insert_coin\n"
        "  noop: noop\n"
        "allowed_actions:\n"
        "  - noop\n"
        "  - insert_coin\n"
        "  - press_start\n"
        "  - move_left\n"
        "  - move_right\n"
        "  - move_up\n"
        "  - move_down\n"
        "  - fire\n"
        "metadata:\n"
        "  clean_room_safe: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="input_sequence control 'south' has no semantic mapping"):
        compile_mapping_files(
            device_profile_path=DEVICE_PROFILE_PATH,
            controller_profile_path=CONTROLLER_PROFILE_PATH,
            game_action_profile_path=game_action_path,
            input_sequence_path=INPUT_SEQUENCE_PATH,
            output_path=tmp_path / "plans" / "generated" / "broken.yaml",
        )


def test_generated_yaml_is_parseable_by_existing_input_planner(tmp_path: Path) -> None:
    output_path = tmp_path / "plans" / "generated" / "gng_smoke_compiled.yaml"

    compile_mapping_files(
        device_profile_path=DEVICE_PROFILE_PATH,
        controller_profile_path=CONTROLLER_PROFILE_PATH,
        game_action_profile_path=GAME_ACTION_PROFILE_PATH,
        input_sequence_path=INPUT_SEQUENCE_PATH,
        output_path=output_path,
    )

    payload = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    compiled_plan = load_input_plan(output_path)

    assert payload["plan_name"] == compiled_plan.plan_name
    assert payload["game_id"] == compiled_plan.game_id
    assert len(payload["steps"]) == len(compiled_plan.steps)


@pytest.mark.parametrize(
    ("sequence_path", "legacy_plan_path"),
    [
        (GNG_BOOT_SEQUENCE_PATH, LEGACY_GNG_BOOT_PLAN_PATH),
        (GNG_GAMEPLAY_SEQUENCE_PATH, LEGACY_GNG_GAMEPLAY_PLAN_PATH),
    ],
)
def test_gng_runtime_sequences_compile_to_legacy_plan_steps(
    tmp_path: Path,
    sequence_path: Path,
    legacy_plan_path: Path,
) -> None:
    output_path = tmp_path / "plans" / "generated" / sequence_path.name

    compile_mapping_files(
        device_profile_path=DEVICE_PROFILE_PATH,
        controller_profile_path=CONTROLLER_PROFILE_PATH,
        game_action_profile_path=GAME_ACTION_PROFILE_PATH,
        input_sequence_path=sequence_path,
        output_path=output_path,
    )

    compiled_plan = load_input_plan(output_path)
    legacy_plan = load_input_plan(legacy_plan_path)

    assert _plan_steps(compiled_plan) == _plan_steps(legacy_plan)


@pytest.mark.parametrize(
    ("generated_plan_path", "legacy_plan_path"),
    [
        (GENERATED_GNG_BOOT_PLAN_PATH, LEGACY_GNG_BOOT_PLAN_PATH),
        (GENERATED_GNG_GAMEPLAY_PLAN_PATH, LEGACY_GNG_GAMEPLAY_PLAN_PATH),
    ],
)
def test_checked_in_generated_gng_runtime_plans_match_legacy_behavior(
    generated_plan_path: Path,
    legacy_plan_path: Path,
) -> None:
    generated_plan = load_input_plan(generated_plan_path)
    legacy_plan = load_input_plan(legacy_plan_path)

    assert _plan_steps(generated_plan) == _plan_steps(legacy_plan)


@pytest.mark.parametrize(
    "generated_plan_path",
    [
        GENERATED_GNG_BOOT_PLAN_PATH,
        GENERATED_GNG_GAMEPLAY_PLAN_PATH,
    ],
)
def test_checked_in_generated_gng_runtime_plans_use_public_safe_paths_and_payloads(
    generated_plan_path: Path,
) -> None:
    ensure_public_output_path(generated_plan_path)

    payload = yaml.safe_load(generated_plan_path.read_text(encoding="utf-8"))
    ensure_no_private_paths(payload)


def test_compiler_rejects_unsafe_public_output_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="blocked public output directory"):
        compile_mapping_files(
            device_profile_path=DEVICE_PROFILE_PATH,
            controller_profile_path=CONTROLLER_PROFILE_PATH,
            game_action_profile_path=GAME_ACTION_PROFILE_PATH,
            input_sequence_path=INPUT_SEQUENCE_PATH,
            output_path=tmp_path / "specs" / "frames" / "gng_smoke_compiled.yaml",
        )


def _load_typed(path: Path, expected_type: type[object]) -> DeviceProfile | ControllerProfile | GameActionProfile | InputSequence:
    loaded = load_mapping_profile(path)
    assert isinstance(loaded, expected_type)
    return loaded


def _plan_steps(plan: object) -> list[tuple[str, int, str]]:
    assert hasattr(plan, "steps")
    return [
        (step.action, step.frames, step.notes)
        for step in plan.steps
    ]

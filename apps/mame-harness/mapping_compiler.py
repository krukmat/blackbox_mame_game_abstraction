from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

import yaml

from guardrails import ensure_no_private_paths, ensure_public_output_path
from input_planner import load_input_plan
from mapping_profiles import (
    ControllerProfile,
    DeviceProfile,
    GameActionProfile,
    InputSequence,
    MappingProfile,
    load_mapping_profile,
)


CompiledInputPlan = dict[str, Any]
_ProfileT = TypeVar(
    "_ProfileT",
    DeviceProfile,
    ControllerProfile,
    GameActionProfile,
    InputSequence,
)


def build_compiled_input_plan(
    device_profile: DeviceProfile,
    controller_profile: ControllerProfile,
    game_action_profile: GameActionProfile,
    input_sequence: InputSequence,
) -> CompiledInputPlan:
    _validate_profile_stack(device_profile, controller_profile, game_action_profile, input_sequence)

    compiled_steps: list[dict[str, object]] = []
    for step in input_sequence.steps:
        action = game_action_profile.canonical_to_action.get(step.control)
        if action is None:
            raise ValueError(
                f"input_sequence control '{step.control}' has no semantic mapping in "
                f"game_action_profile '{game_action_profile.id}'"
            )
        compiled_step: dict[str, object] = {
            "action": action,
            "frames": step.frames,
        }
        if step.notes:
            compiled_step["notes"] = step.notes
        compiled_steps.append(compiled_step)

    payload: CompiledInputPlan = {
        "plan_name": input_sequence.id,
        "game_id": game_action_profile.driver,
        "steps": compiled_steps,
    }
    ensure_no_private_paths(payload)
    return payload


def write_compiled_input_plan(payload: CompiledInputPlan, output_path: Path) -> Path:
    ensure_public_output_path(output_path)
    ensure_no_private_paths(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return output_path


def compile_mapping_files(
    device_profile_path: Path,
    controller_profile_path: Path,
    game_action_profile_path: Path,
    input_sequence_path: Path,
    output_path: Path,
) -> Path:
    device_profile = _expect_profile_type(load_mapping_profile(device_profile_path), DeviceProfile)
    controller_profile = _expect_profile_type(load_mapping_profile(controller_profile_path), ControllerProfile)
    game_action_profile = _expect_profile_type(load_mapping_profile(game_action_profile_path), GameActionProfile)
    input_sequence = _expect_profile_type(load_mapping_profile(input_sequence_path), InputSequence)

    payload = build_compiled_input_plan(
        device_profile=device_profile,
        controller_profile=controller_profile,
        game_action_profile=game_action_profile,
        input_sequence=input_sequence,
    )
    written = write_compiled_input_plan(payload, output_path)
    load_input_plan(written)
    return written


def _validate_profile_stack(
    device_profile: DeviceProfile,
    controller_profile: ControllerProfile,
    game_action_profile: GameActionProfile,
    input_sequence: InputSequence,
) -> None:
    controller_controls = set(controller_profile.canonical_controls)
    bound_controls = set(device_profile.raw_to_canonical.values())

    missing_required_controls = sorted(set(controller_profile.constraints.required) - bound_controls)
    if missing_required_controls:
        joined = ", ".join(missing_required_controls)
        raise ValueError(
            f"device_profile '{device_profile.id}' is missing required controller bindings: {joined}"
        )

    for step in input_sequence.steps:
        if step.control not in controller_controls:
            raise ValueError(
                f"input_sequence control '{step.control}' is not declared by "
                f"controller_profile '{controller_profile.id}'"
            )
        if step.control != "noop" and step.control not in bound_controls:
            raise ValueError(
                f"input_sequence control '{step.control}' is not bound by "
                f"device_profile '{device_profile.id}'"
            )
        if step.control not in game_action_profile.canonical_to_action:
            raise ValueError(
                f"input_sequence control '{step.control}' has no semantic mapping in "
                f"game_action_profile '{game_action_profile.id}'"
            )

    extra_device_controls = sorted(bound_controls - controller_controls)
    if extra_device_controls:
        joined = ", ".join(extra_device_controls)
        raise ValueError(
            f"device_profile '{device_profile.id}' maps canonical controls not declared by "
            f"controller_profile '{controller_profile.id}': {joined}"
        )


def _expect_profile_type(profile: MappingProfile, expected_type: type[_ProfileT]) -> _ProfileT:
    if not isinstance(profile, expected_type):
        raise ValueError(
            f"expected {expected_type.__name__}, got {type(profile).__name__}"
        )
    return profile

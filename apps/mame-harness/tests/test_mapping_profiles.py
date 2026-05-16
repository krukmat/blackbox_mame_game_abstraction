from __future__ import annotations

from pathlib import Path

import pytest

from conftest import ROOT
from mapping_profiles import (
    ControllerProfile,
    DeviceProfile,
    GameActionProfile,
    InputSequence,
    load_mapping_profile,
)


@pytest.mark.parametrize(
    ("path", "expected_type"),
    [
        (ROOT / "profiles" / "devices" / "keyboard_default.yaml", DeviceProfile),
        (ROOT / "profiles" / "controllers" / "arcade_2button.yaml", ControllerProfile),
        (ROOT / "profiles" / "games" / "gngb" / "default_actions.yaml", GameActionProfile),
        (ROOT / "plans" / "sequences" / "gng_smoke_sequence.yaml", InputSequence),
    ],
)
def test_valid_sample_profiles_load_successfully(path: Path, expected_type: type[object]) -> None:
    loaded = load_mapping_profile(path)
    assert isinstance(loaded, expected_type)


def test_input_sequence_loads_steps_and_preserves_control_order() -> None:
    sequence = load_mapping_profile(ROOT / "plans" / "sequences" / "gng_smoke_sequence.yaml")
    assert isinstance(sequence, InputSequence)
    assert sequence.id == "gng_smoke_sequence"
    assert [step.control for step in sequence.steps] == [
        "select",
        "start",
        "dpad_right",
        "south",
        "east",
    ]


def test_invalid_profile_type_fails_with_actionable_error(tmp_path: Path) -> None:
    profile_path = tmp_path / "broken.yaml"
    profile_path.write_text(
        "schema_version: 1\n"
        "profile_type: broken_profile\n"
        "id: nope\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported profile_type: broken_profile"):
        load_mapping_profile(profile_path)


def test_missing_required_field_fails(tmp_path: Path) -> None:
    profile_path = tmp_path / "missing.yaml"
    profile_path.write_text(
        "schema_version: 1\n"
        "profile_type: device_profile\n"
        "id: keyboard_default\n"
        "source: manual\n"
        "device:\n"
        "  kind: keyboard\n"
        "  name: Default Keyboard\n"
        "metadata:\n"
        "  clean_room_safe: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="raw_to_canonical must be a non-empty object"):
        load_mapping_profile(profile_path)


def test_absolute_local_path_is_rejected(tmp_path: Path) -> None:
    profile_path = tmp_path / "absolute_path.yaml"
    profile_path.write_text(
        "schema_version: 1\n"
        "profile_type: device_profile\n"
        "id: keyboard_default\n"
        "source: /Users/alice/private-config\n"
        "device:\n"
        "  kind: keyboard\n"
        "  name: Default Keyboard\n"
        "raw_to_canonical:\n"
        "  ArrowLeft: dpad_left\n"
        "metadata:\n"
        "  clean_room_safe: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="absolute machine path leaked into public payload"):
        load_mapping_profile(profile_path)


def test_private_evidence_path_is_rejected(tmp_path: Path) -> None:
    profile_path = tmp_path / "private_evidence.yaml"
    profile_path.write_text(
        "schema_version: 1\n"
        "profile_type: device_profile\n"
        "id: keyboard_default\n"
        "source: manual\n"
        "device:\n"
        "  kind: keyboard\n"
        "  name: evidence/private/run_123/frames/frame_0001.png\n"
        "raw_to_canonical:\n"
        "  ArrowLeft: dpad_left\n"
        "metadata:\n"
        "  clean_room_safe: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="private path leaked into public payload"):
        load_mapping_profile(profile_path)


def test_private_uri_handle_is_rejected(tmp_path: Path) -> None:
    profile_path = tmp_path / "private_uri.yaml"
    profile_path.write_text(
        "schema_version: 1\n"
        "profile_type: game_action_profile\n"
        "id: gngb_default_actions\n"
        "source_profile: private://run_abc\n"
        "driver: gngb\n"
        "canonical_to_action:\n"
        "  south: jump\n"
        "allowed_actions:\n"
        "  - jump\n"
        "metadata:\n"
        "  clean_room_safe: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must not contain private:// evidence handles"):
        load_mapping_profile(profile_path)


def test_duplicate_canonical_controls_are_rejected(tmp_path: Path) -> None:
    profile_path = tmp_path / "duplicates.yaml"
    profile_path.write_text(
        "schema_version: 1\n"
        "profile_type: controller_profile\n"
        "id: arcade_dup\n"
        "canonical_controls:\n"
        "  - dpad_left\n"
        "  - dpad_left\n"
        "constraints:\n"
        "  required:\n"
        "    - dpad_left\n"
        "  optional: []\n"
        "metadata:\n"
        "  clean_room_safe: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="canonical_controls contains duplicate entries: dpad_left"):
        load_mapping_profile(profile_path)


def test_invalid_canonical_control_is_rejected(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid_control.yaml"
    profile_path.write_text(
        "schema_version: 1\n"
        "profile_type: input_sequence\n"
        "sequence_type: input_sequence\n"
        "id: broken_sequence\n"
        "steps:\n"
        "  - control: turbo\n"
        "    frames: 4\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported canonical control 'turbo'"):
        load_mapping_profile(profile_path)


def test_invalid_action_mapping_is_rejected(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid_action.yaml"
    profile_path.write_text(
        "schema_version: 1\n"
        "profile_type: game_action_profile\n"
        "id: broken_actions\n"
        "source_profile: gng\n"
        "driver: gngb\n"
        "canonical_to_action:\n"
        "  south: dash\n"
        "allowed_actions:\n"
        "  - dash\n"
        "metadata:\n"
        "  clean_room_safe: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported action 'dash'"):
        load_mapping_profile(profile_path)

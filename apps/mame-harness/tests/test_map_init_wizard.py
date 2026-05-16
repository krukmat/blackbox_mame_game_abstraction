from __future__ import annotations

from io import StringIO
from pathlib import Path

from map_init_wizard import run_map_init_wizard
from mapping_profiles import DeviceProfile, load_mapping_profile


def test_wizard_generates_valid_device_profile(tmp_path: Path) -> None:
    output_path = tmp_path / "profiles" / "devices" / "wizard_keyboard.yaml"
    user_input = StringIO(
        "\n".join(
            [
                "keyboard",
                "keyboard_default",
                "arcade_2button",
                "wizard_keyboard",
                "Wizard Keyboard",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )
        + "\n"
    )
    output = StringIO()

    result = run_map_init_wizard(
        input_stream=user_input,
        output_stream=output,
        output_path=output_path,
    )

    loaded = load_mapping_profile(output_path)
    assert isinstance(loaded, DeviceProfile)
    assert result.profile.id == "wizard_keyboard"
    assert loaded.raw_to_canonical["ArrowLeft"] == "dpad_left"
    assert "map validate --profile" in result.next_validate_command
    assert "map compile" in result.next_compile_command


def test_wizard_reprompts_on_duplicate_binding_and_accepts_replacement(tmp_path: Path) -> None:
    output_path = tmp_path / "profiles" / "devices" / "manual_pad.yaml"
    user_input = StringIO(
        "\n".join(
            [
                "controller",
                "none",
                "arcade_2button",
                "manual_pad",
                "Manual Pad",
                "",
                "left",
                "left",
                "right",
                "jump",
                "fire",
                "start_btn",
                "select_btn",
                "",
                "",
            ]
        )
        + "\n"
    )
    output = StringIO()

    result = run_map_init_wizard(
        input_stream=user_input,
        output_stream=output,
        output_path=output_path,
    )

    assert result.profile.raw_to_canonical["left"] == "dpad_left"
    assert result.profile.raw_to_canonical["right"] == "dpad_right"
    assert "duplicate raw binding 'left'" in output.getvalue()


def test_wizard_skips_optional_controls_when_blank(tmp_path: Path) -> None:
    output_path = tmp_path / "profiles" / "devices" / "minimal_keyboard.yaml"
    user_input = StringIO(
        "\n".join(
            [
                "keyboard",
                "none",
                "arcade_2button",
                "minimal_keyboard",
                "Minimal Keyboard",
                "",
                "KeyA",
                "KeyD",
                "KeyZ",
                "KeyX",
                "Enter",
                "ShiftRight",
                "",
                "",
            ]
        )
        + "\n"
    )
    output = StringIO()

    result = run_map_init_wizard(
        input_stream=user_input,
        output_stream=output,
        output_path=output_path,
    )

    assert "KeyA" in result.profile.raw_to_canonical
    assert "dpad_up" not in result.profile.raw_to_canonical.values()
    assert "dpad_down" not in result.profile.raw_to_canonical.values()

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from cli import (
    build_parser,
    handle_map_compile,
    handle_map_import_retroarch,
    handle_map_import_sdl,
    handle_map_validate,
)
from input_planner import load_input_plan
from tests.conftest import ROOT


DEVICE_PROFILE_PATH = ROOT / "profiles" / "devices" / "keyboard_default.yaml"
CONTROLLER_PROFILE_PATH = ROOT / "profiles" / "controllers" / "arcade_2button.yaml"
GAME_ACTION_PROFILE_PATH = ROOT / "profiles" / "games" / "gngb" / "default_actions.yaml"
INPUT_SEQUENCE_PATH = ROOT / "plans" / "sequences" / "gng_smoke_sequence.yaml"


def test_map_validate_succeeds_for_valid_sample_profile() -> None:
    args = argparse.Namespace(profile=DEVICE_PROFILE_PATH)

    result = handle_map_validate(args)

    assert result == {
        "status": "validated",
        "profile_type": "device_profile",
        "id": "keyboard_default",
        "path": str(DEVICE_PROFILE_PATH),
    }


def test_map_validate_fails_for_invalid_profile(tmp_path: Path) -> None:
    invalid_profile = tmp_path / "invalid.yaml"
    invalid_profile.write_text(
        "schema_version: 1\n"
        "profile_type: invalid_profile\n"
        "id: nope\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported profile_type: invalid_profile"):
        handle_map_validate(argparse.Namespace(profile=invalid_profile))


def test_map_compile_writes_generated_plan(tmp_path: Path) -> None:
    output_path = tmp_path / "plans" / "generated" / "gng_smoke_compiled.yaml"
    args = argparse.Namespace(
        device=DEVICE_PROFILE_PATH,
        controller=CONTROLLER_PROFILE_PATH,
        game=GAME_ACTION_PROFILE_PATH,
        sequence=INPUT_SEQUENCE_PATH,
        out=output_path,
    )

    result = handle_map_compile(args)

    assert output_path.exists()
    assert result["status"] == "compiled"
    assert result["output"] == str(output_path)
    assert result["plan_name"] == "gng_smoke_sequence"
    assert result["game_id"] == "gngb"
    assert result["steps"] == 5


def test_map_compile_output_is_parseable_by_input_planner(tmp_path: Path) -> None:
    output_path = tmp_path / "plans" / "generated" / "gng_smoke_compiled.yaml"
    args = argparse.Namespace(
        device=DEVICE_PROFILE_PATH,
        controller=CONTROLLER_PROFILE_PATH,
        game=GAME_ACTION_PROFILE_PATH,
        sequence=INPUT_SEQUENCE_PATH,
        out=output_path,
    )

    handle_map_compile(args)
    compiled_plan = load_input_plan(output_path)

    assert compiled_plan.plan_name == "gng_smoke_sequence"
    assert compiled_plan.game_id == "gngb"


def test_map_import_sdl_writes_device_profile(tmp_path: Path) -> None:
    db_path = tmp_path / "gamecontrollerdb.txt"
    db_path.write_text(
        "03000000de280000ff11000001000000,8BitDo Pro 2,a:b0,b:b1,start:b11,back:b10,\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "profiles" / "devices" / "8bitdo_pro2.yaml"
    args = argparse.Namespace(
        db=db_path,
        out=output_path,
        guid=None,
        name=None,
        profile_id=None,
    )

    result = handle_map_import_sdl(args)

    assert result["status"] == "imported"
    assert result["output"] == str(output_path)
    assert result["profile_type"] == "device_profile"
    assert result["id"] == "8bitdo_pro_2_sdl"
    assert result["bindings"] == 4


def test_map_import_retroarch_writes_device_profile(tmp_path: Path) -> None:
    config_path = tmp_path / "controller.cfg"
    config_path.write_text(
        'input_device = "Pad"\ninput_b_btn = "0"\ninput_start_btn = "9"\n',
        encoding="utf-8",
    )
    output_path = tmp_path / "profiles" / "devices" / "pad.yaml"
    args = argparse.Namespace(
        config=config_path,
        out=output_path,
        profile_id=None,
    )

    result = handle_map_import_retroarch(args)

    assert result["status"] == "imported"
    assert result["output"] == str(output_path)
    assert result["profile_type"] == "device_profile"
    assert result["id"] == "pad_retroarch"
    assert result["bindings"] == 2


def test_map_init_subcommand_parses_correctly() -> None:
    parser = build_parser()

    init_args = parser.parse_args(
        [
            "map",
            "init",
            "--out",
            "profiles/devices/wizard.yaml",
        ]
    )

    assert init_args.command == "map"
    assert init_args.map_command == "init"
    assert init_args.out == Path("profiles/devices/wizard.yaml")


def test_existing_cli_behavior_still_parses_run_command() -> None:
    parser = build_parser()

    args = parser.parse_args(["run", "--rom", "gngb", "--dry-run"])

    assert args.command == "run"
    assert args.rom == "gngb"
    assert args.dry_run is True


def test_map_subcommands_parse_correctly() -> None:
    parser = build_parser()

    validate_args = parser.parse_args(["map", "validate", "--profile", str(DEVICE_PROFILE_PATH)])
    compile_args = parser.parse_args(
        [
            "map",
            "compile",
            "--device",
            str(DEVICE_PROFILE_PATH),
            "--controller",
            str(CONTROLLER_PROFILE_PATH),
            "--game",
            str(GAME_ACTION_PROFILE_PATH),
            "--sequence",
            str(INPUT_SEQUENCE_PATH),
            "--out",
            "plans/generated/gng_smoke_compiled.yaml",
        ]
    )
    import_args = parser.parse_args(
        [
            "map",
            "import-sdl",
            "--db",
            "controllers/gamecontrollerdb.txt",
            "--out",
            "profiles/devices/pad.yaml",
        ]
    )
    import_retroarch_args = parser.parse_args(
        [
            "map",
            "import-retroarch",
            "--config",
            "controllers/pad.cfg",
            "--out",
            "profiles/devices/pad.yaml",
        ]
    )
    init_args = parser.parse_args(
        [
            "map",
            "init",
            "--out",
            "profiles/devices/wizard.yaml",
        ]
    )

    assert validate_args.command == "map"
    assert validate_args.map_command == "validate"
    assert validate_args.profile == DEVICE_PROFILE_PATH
    assert compile_args.command == "map"
    assert compile_args.map_command == "compile"
    assert import_args.command == "map"
    assert import_args.map_command == "import-sdl"
    assert import_retroarch_args.command == "map"
    assert import_retroarch_args.map_command == "import-retroarch"
    assert init_args.command == "map"
    assert init_args.map_command == "init"

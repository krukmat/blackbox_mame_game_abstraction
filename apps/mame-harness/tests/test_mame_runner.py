from __future__ import annotations

from pathlib import Path

from mame_runner import MameRunRequest, build_mame_command, run_mame


def test_dry_run_mame_command_construction() -> None:
    request = MameRunRequest(
        game_shortname="sample_game",
        mame_binary="mame",
        rom_path=Path("roms"),
        state_dir=Path("evidence/private/run_001/states"),
        snapshot_dir=Path("evidence/private/run_001/frames"),
        record_input_file=Path("evidence/private/run_001/logs/input.inp"),
        aviwrite_path=Path("evidence/private/run_001/video/capture.avi"),
        autoboot_script=Path("scripts/mame_autoboot.lua"),
        extra_args=["-window"],
        dry_run=True,
    )
    assert build_mame_command(request) == [
        "mame",
        "sample_game",
        "-rompath",
        "roms",
        "-state_directory",
        "evidence/private/run_001/states",
        "-snapshot_directory",
        "evidence/private/run_001/frames",
        "-record",
        "evidence/private/run_001/logs/input.inp",
        "-aviwrite",
        "evidence/private/run_001/video/capture.avi",
        "-autoboot_script",
        "scripts/mame_autoboot.lua",
        "-window",
    ]


def test_real_run_executes_when_dry_run_disabled() -> None:
    result = run_mame(
        MameRunRequest(
            game_shortname="-c",
            mame_binary="python3.11",
            extra_args=["print('ok')"],
            dry_run=False,
        )
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "ok"

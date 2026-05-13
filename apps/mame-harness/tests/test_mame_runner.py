from __future__ import annotations

from pathlib import Path

from mame_runner import MameRunRequest, build_mame_command, run_mame
from source_profiles import GNG_SOURCE_PROFILE


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


def test_dry_run_returns_structured_result_with_preflight(tmp_path: Path) -> None:
    rom_zip = tmp_path / "gng.zip"
    rom_zip.write_text("placeholder")
    fake_mame = _write_fake_mame(tmp_path, "0.287 (mame0287)\n")

    result = run_mame(
        MameRunRequest(
            game_shortname="gng",
            mame_binary=str(fake_mame),
            source_profile=GNG_SOURCE_PROFILE,
            rom_path=tmp_path,
            dry_run=True,
        )
    )

    assert result.status == "dry_run"
    assert result.preflight is not None
    assert result.preflight.ok is True
    assert result.execution is None


def test_runner_returns_structured_preflight_failure(tmp_path: Path) -> None:
    result = run_mame(
        MameRunRequest(
            game_shortname="gng",
            mame_binary="missing-mame-binary",
            source_profile=GNG_SOURCE_PROFILE,
            rom_path=tmp_path,
            dry_run=False,
        )
    )

    assert result.status == "preflight_failure"
    assert result.preflight is not None
    assert result.preflight.ok is False
    assert result.preflight.issues[0].code == "mame_binary_missing"
    assert result.execution is None


def test_real_run_executes_when_dry_run_disabled() -> None:
    result = run_mame(
        MameRunRequest(
            game_shortname="-c",
            mame_binary="python3.11",
            extra_args=["print('ok')"],
            dry_run=False,
        )
    )
    assert result.status == "success"
    assert result.execution is not None
    assert result.execution.returncode == 0
    assert result.execution.stdout.strip() == "ok"


def test_runner_returns_structured_execution_failure() -> None:
    result = run_mame(
        MameRunRequest(
            game_shortname="-c",
            mame_binary="python3.11",
            extra_args=["import sys; sys.exit(2)"],
            dry_run=False,
        )
    )

    assert result.status == "execution_failure"
    assert result.execution is not None
    assert result.execution.returncode == 2


def _write_fake_mame(tmp_path: Path, version_output: str) -> Path:
    fake_mame = tmp_path / "fake-mame"
    fake_mame.write_text(f"#!/bin/sh\necho '{version_output.strip()}'\n")
    fake_mame.chmod(0o755)
    return fake_mame

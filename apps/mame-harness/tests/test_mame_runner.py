from __future__ import annotations

from pathlib import Path

import pytest

from mame_runner import MAME_FRAME_RATE, MameRunRequest, build_mame_command, run_mame
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
        str(Path("evidence/private/run_001/video/capture.avi").resolve()),  # T08.2.5 — absolute
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


def test_aviwrite_path_is_absolute_in_command() -> None:
    # T08.2.5 — MAME resolves -aviwrite relative to -snapshot_directory unless absolute.
    # Pass a relative path (the real-world case) and assert the command has an absolute one.
    aviwrite = Path("evidence/private/run_abc/video/capture.avi")
    snapshot = Path("evidence/private/run_abc/frames")
    request = MameRunRequest(
        game_shortname="gngb",
        aviwrite_path=aviwrite,
        snapshot_dir=snapshot,
        dry_run=True,
    )
    cmd = build_mame_command(request)
    idx = cmd.index("-aviwrite")
    assert Path(cmd[idx + 1]).is_absolute(), "aviwrite path must be absolute to avoid MAME path nesting"


def test_frames_to_run_emits_seconds_to_run() -> None:
    # T08.2.2 — MAME 0.287 removed -frames_to_run; must convert to -seconds_to_run
    request = MameRunRequest(
        game_shortname="gngb",
        frames_to_run=300,
        dry_run=True,
    )
    cmd = build_mame_command(request)
    assert "-seconds_to_run" in cmd
    assert "-frames_to_run" not in cmd
    idx = cmd.index("-seconds_to_run")
    assert cmd[idx + 1] == str(-(-(300) // MAME_FRAME_RATE))  # ceil via integer division


def test_frames_to_run_ceiling_conversion() -> None:
    # 61 frames at 60fps -> ceil(61/60) = 2 seconds, not 1
    request = MameRunRequest(game_shortname="x", frames_to_run=61, dry_run=True)
    cmd = build_mame_command(request)
    idx = cmd.index("-seconds_to_run")
    assert cmd[idx + 1] == "2"


def test_run_mame_passes_environment_overrides_to_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class CompletedProcess:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return CompletedProcess()

    monkeypatch.setattr("mame_runner.subprocess.run", fake_run)
    monkeypatch.setenv("UNCHANGED_PARENT_VAR", "parent")

    result = run_mame(
        MameRunRequest(
            game_shortname="gngb",
            environment={"BLACKBOX_INPUT_PLAN_PATH": "/tmp/input_plan.json"},
            dry_run=False,
        )
    )

    assert result.status == "success"
    env = captured["kwargs"]["env"]
    assert env["BLACKBOX_INPUT_PLAN_PATH"] == "/tmp/input_plan.json"
    assert env["UNCHANGED_PARENT_VAR"] == "parent"


def _write_fake_mame(tmp_path: Path, version_output: str) -> Path:
    fake_mame = tmp_path / "fake-mame"
    fake_mame.write_text(f"#!/bin/sh\necho '{version_output.strip()}'\n")
    fake_mame.chmod(0o755)
    return fake_mame

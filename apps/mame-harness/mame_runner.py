from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Mapping, Sequence

from guardrails import ensure_private_evidence_path
from preflight import PreflightResult, run_preflight
from source_profiles import SourceProfile

# T08.2.2 — MAME 0.287 removed -frames_to_run; only -seconds_to_run is exposed.
# Conversion assumes 60fps. ceil() ensures we run at least the requested frames.
MAME_FRAME_RATE = 60


@dataclass(slots=True)
class MameExecution:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass(slots=True)
class MameRunResult:
    status: str
    command: list[str]
    preflight: PreflightResult | None = None
    execution: MameExecution | None = None


@dataclass(slots=True)
class MameRunRequest:
    game_shortname: str
    mame_binary: str = "mame"
    working_dir: Path = Path(".")
    source_profile: SourceProfile | None = None
    rom_path: Path | None = None
    cfg_dir: Path | None = None
    nvram_dir: Path | None = None
    input_dir: Path | None = None
    state_dir: Path | None = None
    snapshot_dir: Path | None = None
    record_input_file: Path | None = None
    playback_input_file: Path | None = None
    state_name: str | None = None
    aviwrite_path: Path | None = None
    mngwrite_path: Path | None = None
    seconds_to_run: int | None = None
    frames_to_run: int | None = None
    autoboot_script: Path | None = None
    environment: Mapping[str, str] | None = None
    extra_args: Sequence[str] | None = None
    dry_run: bool = True


def _append_path_arg(command: list[str], flag: str, path: Path | None, enforce_private: bool = False) -> None:
    if path is None:
        return
    normalized = Path(path)
    if enforce_private:
        ensure_private_evidence_path(normalized)
    command.extend([flag, str(normalized)])


def build_mame_command(request: MameRunRequest) -> list[str]:
    command = [request.mame_binary, request.game_shortname]
    _append_path_arg(command, "-rompath", request.rom_path)
    _append_path_arg(command, "-cfg_directory", request.cfg_dir)
    _append_path_arg(command, "-nvram_directory", request.nvram_dir)
    _append_path_arg(command, "-input_directory", request.input_dir)
    _append_path_arg(command, "-state_directory", request.state_dir, enforce_private=True)
    _append_path_arg(command, "-snapshot_directory", request.snapshot_dir, enforce_private=True)
    _append_path_arg(command, "-record", request.record_input_file, enforce_private=True)
    _append_path_arg(command, "-playback", request.playback_input_file, enforce_private=True)
    # T08.2.5 — resolve to absolute so MAME doesn't nest -aviwrite under -snapshot_directory
    aviwrite_abs = request.aviwrite_path.resolve() if request.aviwrite_path else None
    _append_path_arg(command, "-aviwrite", aviwrite_abs, enforce_private=True)
    _append_path_arg(command, "-mngwrite", request.mngwrite_path, enforce_private=True)
    if request.state_name:
        command.extend(["-state", request.state_name])
    if request.seconds_to_run is not None:
        command.extend(["-seconds_to_run", str(request.seconds_to_run)])
    if request.frames_to_run is not None:
        # T08.2.2 — convert frames to seconds; ceil guarantees at least frames_to_run frames
        seconds = math.ceil(request.frames_to_run / MAME_FRAME_RATE)
        command.extend(["-seconds_to_run", str(seconds)])
    if request.autoboot_script:
        command.extend(["-autoboot_script", str(request.autoboot_script)])
    if request.extra_args:
        command.extend(list(request.extra_args))
    return command


def run_mame(request: MameRunRequest) -> MameRunResult:
    command = build_mame_command(request)
    preflight = _run_request_preflight(request)
    if preflight is not None and not preflight.ok:
        return MameRunResult(
            status="preflight_failure",
            command=command,
            preflight=preflight,
        )
    if request.dry_run:
        return MameRunResult(
            status="dry_run",
            command=command,
            preflight=preflight,
        )
    completed = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
        cwd=request.working_dir,
        env=_build_run_environment(request.environment),
    )
    execution = MameExecution(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    if completed.returncode != 0:
        return MameRunResult(
            status="execution_failure",
            command=command,
            preflight=preflight,
            execution=execution,
        )
    return MameRunResult(
        status="success",
        command=command,
        preflight=preflight,
        execution=execution,
    )


def _run_request_preflight(request: MameRunRequest) -> PreflightResult | None:
    if request.source_profile is None:
        return None
    return run_preflight(
        profile=request.source_profile,
        mame_binary=request.mame_binary,
        rom_path=request.rom_path,
    )


def _build_run_environment(overrides: Mapping[str, str] | None) -> dict[str, str]:
    environment = dict(os.environ)
    if overrides:
        environment.update(overrides)
    return environment

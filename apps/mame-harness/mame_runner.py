from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Sequence

from guardrails import ensure_private_evidence_path


@dataclass(slots=True)
class MameRunResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass(slots=True)
class MameRunRequest:
    game_shortname: str
    mame_binary: str = "mame"
    working_dir: Path = Path(".")
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
    _append_path_arg(command, "-aviwrite", request.aviwrite_path, enforce_private=True)
    _append_path_arg(command, "-mngwrite", request.mngwrite_path, enforce_private=True)
    if request.state_name:
        command.extend(["-state", request.state_name])
    if request.seconds_to_run is not None:
        command.extend(["-seconds_to_run", str(request.seconds_to_run)])
    if request.frames_to_run is not None:
        command.extend(["-frames_to_run", str(request.frames_to_run)])
    if request.autoboot_script:
        command.extend(["-autoboot_script", str(request.autoboot_script)])
    if request.extra_args:
        command.extend(list(request.extra_args))
    return command


def run_mame(request: MameRunRequest) -> MameRunResult | list[str]:
    command = build_mame_command(request)
    if request.dry_run:
        return command
    completed = subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=True,
        cwd=request.working_dir,
    )
    return MameRunResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )

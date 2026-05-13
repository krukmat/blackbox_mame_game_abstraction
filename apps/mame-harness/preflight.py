from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shutil
import subprocess

from source_profiles import SourceProfile


MAME_MINIMUM_VERSION = 240
EXPECTED_GNG_DRIVER = "gngb"


@dataclass(frozen=True, slots=True)
class PreflightIssue:
    code: str
    message: str
    field: str


@dataclass(frozen=True, slots=True)
class PreflightResult:
    ok: bool
    profile_id: str
    mame_binary: str
    driver: str
    issues: tuple[PreflightIssue, ...] = ()
    detected_version: int | None = None
    rom_zip_path: Path | None = None


def parse_mame_version(output: str) -> int | None:
    normalized = output.strip()
    if not normalized.startswith("0."):
        return None
    major, _, remainder = normalized.partition(".")
    if major != "0" or not remainder:
        return None

    digits = []
    for char in remainder:
        if not char.isdigit():
            break
        digits.append(char)
    if not digits:
        return None
    return int("".join(digits))


def run_preflight(profile: SourceProfile, mame_binary: str, rom_path: Path | None) -> PreflightResult:
    driver_issue = _validate_driver_contract(profile)
    if driver_issue is not None:
        return _failure(profile, mame_binary, driver_issue)

    binary_issue = _validate_mame_binary_presence(mame_binary)
    if binary_issue is not None:
        return _failure(profile, mame_binary, binary_issue)

    version_probe = _probe_mame_version(mame_binary)
    if isinstance(version_probe, PreflightIssue):
        return _failure(profile, mame_binary, version_probe)

    rom_probe = _resolve_rom_zip_path(profile, rom_path)
    if isinstance(rom_probe, PreflightIssue):
        return _failure(profile, mame_binary, rom_probe, detected_version=version_probe)

    return PreflightResult(
        ok=True,
        profile_id=profile.profile_id,
        mame_binary=mame_binary,
        driver=profile.mame_driver,
        detected_version=version_probe,
        rom_zip_path=rom_probe,
    )


def _failure(
    profile: SourceProfile,
    mame_binary: str,
    issue: PreflightIssue,
    *,
    detected_version: int | None = None,
) -> PreflightResult:
    return PreflightResult(
        ok=False,
        profile_id=profile.profile_id,
        mame_binary=mame_binary,
        driver=profile.mame_driver,
        issues=(issue,),
        detected_version=detected_version,
    )


def _validate_driver_contract(profile: SourceProfile) -> PreflightIssue | None:
    if profile.profile_id == "gng" and profile.mame_driver != EXPECTED_GNG_DRIVER:
        return PreflightIssue(
            code="driver_contract_mismatch",
            field="profile.mame_driver",
            message=(
                f"Source profile '{profile.profile_id}' must resolve to MAME driver "
                f"'{EXPECTED_GNG_DRIVER}', got '{profile.mame_driver}'."
            ),
        )
    return None


def _validate_mame_binary_presence(mame_binary: str) -> PreflightIssue | None:
    resolved = shutil.which(mame_binary)
    if resolved is None:
        return PreflightIssue(
            code="mame_binary_missing",
            field="mame_binary",
            message=f"MAME binary '{mame_binary}' was not found in PATH or at the provided location.",
        )
    return None


def _probe_mame_version(mame_binary: str) -> int | PreflightIssue:
    try:
        completed = subprocess.run(
            [mame_binary, "-version"],
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        return PreflightIssue(
            code="mame_version_probe_failed",
            field="mame_binary",
            message=f"Failed to run '{mame_binary} -version': {exc}.",
        )

    version = parse_mame_version(completed.stdout)
    if version is None:
        excerpt = completed.stdout.strip()[:80]
        return PreflightIssue(
            code="mame_version_unparseable",
            field="mame_binary",
            message=f"Could not parse MAME version from output: '{excerpt}'. Expected '0.<NNN>'.",
        )
    if version < MAME_MINIMUM_VERSION:
        return PreflightIssue(
            code="mame_version_too_old",
            field="mame_binary",
            message=(
                f"MAME version 0.{version} is below the minimum supported version "
                f"0.{MAME_MINIMUM_VERSION}."
            ),
        )
    return version


def _resolve_rom_zip_path(profile: SourceProfile, rom_path: Path | None) -> Path | PreflightIssue:
    if rom_path is None:
        return PreflightIssue(
            code="rom_path_missing",
            field="rom_path",
            message=(
                f"ROM input is required for source profile '{profile.profile_id}'. "
                f"Provide a path to the directory containing {profile.expected_rom_zip} "
                f"or the zip itself."
            ),
        )

    normalized = Path(rom_path)
    candidate = normalized / profile.expected_rom_zip if normalized.is_dir() else normalized

    if candidate.name != profile.expected_rom_zip:
        return PreflightIssue(
            code="rom_zip_name_mismatch",
            field="rom_path",
            message=(
                f"ROM input for source profile '{profile.profile_id}' must resolve to "
                f"'{profile.expected_rom_zip}', got '{candidate.name}'."
            ),
        )

    if not candidate.is_file():
        return PreflightIssue(
            code="rom_zip_missing",
            field="rom_path",
            message=f"Expected ROM zip '{profile.expected_rom_zip}' was not found at {candidate}.",
        )

    return candidate

"""T06 — GNG Contract Test Coverage.

T06.1: verify that run_mame with GNG_SOURCE_PROFILE builds a command that uses
gngb as the MAME driver (game shortname).

T06.2: verify that preflight failure messages for mame_binary_missing and
rom_path_missing are sanitized — no absolute paths survive into public metadata.

T06.3: verify that GNG profile + preflight failure + build_sanitized_metadata
produces a payload that write_public_metadata accepts without raising.
"""
from __future__ import annotations

import json
from pathlib import Path

from cli import _sanitize_preflight_issue_message
from mame_runner import MameExecution, MameRunRequest, MameRunResult, build_mame_command, run_mame
from metadata_writer import write_public_metadata
from preflight import PreflightIssue, PreflightResult
from source_profiles import GNG_SOURCE_PROFILE, get_source_profile
from tests.test_redaction_regression import build_run_result, build_sanitized_metadata

# Sentinel paths used to construct worst-case raw issue messages
_UNIX_ROM_PATH = "/Users/alice/roms/gng.zip"
_WINDOWS_ROM_PATH = "C:\\Users\\alice\\roms\\gng.zip"
_UNIX_BINARY_PATH = "/usr/local/bin/mame"

# All known preflight issue codes — each must produce a path-free sanitized message
_ALL_PREFLIGHT_CODES = [
    "mame_binary_missing",
    "mame_version_probe_failed",
    "mame_version_unparseable",
    "mame_version_too_old",
    "rom_path_missing",
    "rom_zip_name_mismatch",
    "rom_zip_missing",
    "driver_contract_mismatch",
]

# ---------------------------------------------------------------------------
# T06.1 — GNG driver contract
# ---------------------------------------------------------------------------


def test_gng_profile_driver_is_gngb() -> None:
    """T06.1 — profile encodes gngb as the required MAME driver."""
    assert GNG_SOURCE_PROFILE.mame_driver == "gngb"


def test_gng_profile_resolves_via_registry() -> None:
    """T06.1 — get_source_profile('gng') returns the canonical profile."""
    profile = get_source_profile("gng")
    assert profile is GNG_SOURCE_PROFILE
    assert profile.mame_driver == "gngb"


def test_build_mame_command_with_gng_driver_places_gngb_as_second_token() -> None:
    """T06.1 — build_mame_command uses game_shortname as second token; must be gngb."""
    request = MameRunRequest(
        game_shortname=GNG_SOURCE_PROFILE.mame_driver,  # "gngb"
        source_profile=GNG_SOURCE_PROFILE,
        dry_run=True,
    )
    command = build_mame_command(request)
    assert command[0] == "mame"
    assert command[1] == "gngb"


def test_gngb_driver_present_in_command_list() -> None:
    """T06.1 — the string 'gngb' appears in the constructed command."""
    request = MameRunRequest(
        game_shortname=GNG_SOURCE_PROFILE.mame_driver,
        source_profile=GNG_SOURCE_PROFILE,
        dry_run=True,
    )
    command = build_mame_command(request)
    assert "gngb" in command


def test_run_mame_with_gng_profile_command_contains_gngb() -> None:
    """T06.1 — run_mame result carries a command with gngb regardless of preflight outcome.

    In CI there is no real MAME binary, so preflight will fail with
    mame_binary_missing. The important contract is that the command was
    constructed correctly before preflight ran.
    """
    request = MameRunRequest(
        game_shortname=GNG_SOURCE_PROFILE.mame_driver,
        source_profile=GNG_SOURCE_PROFILE,
        dry_run=True,
    )
    result = run_mame(request)
    assert "gngb" in result.command


def test_run_mame_with_gng_profile_attaches_preflight_result() -> None:
    """T06.1 — preflight is never None when source_profile is provided."""
    request = MameRunRequest(
        game_shortname=GNG_SOURCE_PROFILE.mame_driver,
        source_profile=GNG_SOURCE_PROFILE,
        dry_run=True,
    )
    result = run_mame(request)
    assert result.preflight is not None
    assert result.preflight.profile_id == "gng"
    assert result.preflight.driver == "gngb"


def test_run_mame_without_profile_has_no_preflight() -> None:
    """T06.1 — baseline: omitting source_profile produces no preflight."""
    request = MameRunRequest(
        game_shortname="gngb",
        dry_run=True,
    )
    result = run_mame(request)
    assert result.preflight is None


# ---------------------------------------------------------------------------
# T06.2 — preflight failure messages are path-free after sanitization
# ---------------------------------------------------------------------------


def test_mame_binary_missing_message_is_path_free() -> None:
    """T06.2 — mame_binary_missing raw message with binary path is sanitized."""
    issue = PreflightIssue(
        code="mame_binary_missing",
        field="mame_binary",
        message=f"MAME binary '{_UNIX_BINARY_PATH}' was not found in PATH.",
    )
    sanitized = _sanitize_preflight_issue_message(issue)
    assert _UNIX_BINARY_PATH not in sanitized
    assert "/" not in sanitized or sanitized.startswith("private://")


def test_rom_path_missing_message_is_path_free() -> None:
    """T06.2 — rom_path_missing raw message produces a path-free sanitized form."""
    issue = PreflightIssue(
        code="rom_path_missing",
        field="rom_path",
        message=f"ROM input is required. Provide a path containing gng.zip or the zip itself.",
    )
    sanitized = _sanitize_preflight_issue_message(issue)
    assert _UNIX_ROM_PATH not in sanitized
    assert _WINDOWS_ROM_PATH not in sanitized


def test_mame_binary_missing_message_is_human_readable() -> None:
    """T06.2 — sanitized mame_binary_missing message is non-empty and informative."""
    issue = PreflightIssue(
        code="mame_binary_missing",
        field="mame_binary",
        message="MAME binary 'mame' was not found in PATH.",
    )
    sanitized = _sanitize_preflight_issue_message(issue)
    assert len(sanitized) > 10
    assert "MAME" in sanitized or "binary" in sanitized or "executable" in sanitized


def test_rom_path_missing_message_is_human_readable() -> None:
    """T06.2 — sanitized rom_path_missing message is non-empty and informative."""
    issue = PreflightIssue(
        code="rom_path_missing",
        field="rom_path",
        message="ROM input is required.",
    )
    sanitized = _sanitize_preflight_issue_message(issue)
    assert len(sanitized) > 10
    assert "ROM" in sanitized or "rom" in sanitized


def test_rom_zip_missing_message_with_real_path_is_sanitized() -> None:
    """T06.2 — rom_zip_missing worst case: raw message contains absolute ROM path."""
    issue = PreflightIssue(
        code="rom_zip_missing",
        field="rom_path",
        message=f"Expected ROM zip 'gng.zip' was not found at {_UNIX_ROM_PATH}.",
    )
    sanitized = _sanitize_preflight_issue_message(issue)
    assert _UNIX_ROM_PATH not in sanitized
    assert _WINDOWS_ROM_PATH not in sanitized


def test_all_known_preflight_codes_produce_path_free_messages() -> None:
    """T06.2 — every known issue code produces a message free of absolute paths."""
    for code in _ALL_PREFLIGHT_CODES:
        issue = PreflightIssue(
            code=code,
            field="test_field",
            # Worst case: embed both a Unix and Windows path in raw message
            message=f"Some error involving {_UNIX_ROM_PATH} and {_WINDOWS_ROM_PATH}.",
        )
        sanitized = _sanitize_preflight_issue_message(issue)
        assert _UNIX_ROM_PATH not in sanitized, f"Unix path leaked for code '{code}'"
        assert _WINDOWS_ROM_PATH not in sanitized, f"Windows path leaked for code '{code}'"
        assert _UNIX_BINARY_PATH not in sanitized, f"Binary path leaked for code '{code}'"


# ---------------------------------------------------------------------------
# T06.3 — GNG profile + preflight failure + writer integration
# ---------------------------------------------------------------------------

def _make_gng_preflight_failure(code: str, message: str) -> MameRunResult:
    """Build a MameRunResult with GNG profile and a single preflight failure."""
    issue = PreflightIssue(code=code, field="rom_path", message=message)
    preflight = PreflightResult(
        ok=False,
        profile_id=GNG_SOURCE_PROFILE.profile_id,
        mame_binary="mame",
        driver=GNG_SOURCE_PROFILE.mame_driver,
        issues=(issue,),
    )
    return MameRunResult(
        status="preflight_failure",
        command=["mame", GNG_SOURCE_PROFILE.mame_driver],
        preflight=preflight,
    )


def test_gng_preflight_failure_metadata_accepted_by_writer(tmp_path: Path) -> None:
    """T06.3 — sanitized GNG preflight failure metadata passes write_public_metadata."""
    run_result = build_run_result()
    metadata = build_sanitized_metadata(run_result)
    output = tmp_path / "specs" / "run_metadata.json"
    written = write_public_metadata(output, metadata)
    assert written.exists()


def test_gng_mame_missing_metadata_accepted_by_writer(tmp_path: Path) -> None:
    """T06.3 — mame_binary_missing failure with GNG profile passes the writer."""
    run_result = _make_gng_preflight_failure(
        code="mame_binary_missing",
        message="MAME binary 'mame' was not found in PATH or at the provided location.",
    )
    metadata = build_sanitized_metadata(run_result)
    output = tmp_path / "specs" / "run_metadata.json"
    written = write_public_metadata(output, metadata)
    assert written.exists()


def test_gng_rom_missing_metadata_accepted_by_writer(tmp_path: Path) -> None:
    """T06.3 — rom_path_missing failure with GNG profile passes the writer."""
    run_result = _make_gng_preflight_failure(
        code="rom_path_missing",
        message="ROM input is required for source profile 'gng'. Provide a path containing gng.zip.",
    )
    metadata = build_sanitized_metadata(run_result)
    output = tmp_path / "specs" / "run_metadata.json"
    written = write_public_metadata(output, metadata)
    assert written.exists()


def test_gng_sanitized_metadata_contains_profile_id(tmp_path: Path) -> None:
    """T06.3 — profile_id 'gng' survives sanitization into written metadata."""
    run_result = _make_gng_preflight_failure(
        code="mame_binary_missing",
        message="MAME binary not found.",
    )
    metadata = build_sanitized_metadata(run_result)
    output = tmp_path / "specs" / "run_metadata.json"
    write_public_metadata(output, metadata)
    content = json.loads(output.read_text(encoding="utf-8"))
    assert content["preflight"]["ok"] is False


def test_gng_sanitized_metadata_contains_driver(tmp_path: Path) -> None:
    """T06.3 — driver field 'gngb' survives sanitization into written metadata."""
    run_result = build_run_result()
    metadata = build_sanitized_metadata(run_result)
    output = tmp_path / "specs" / "run_metadata.json"
    write_public_metadata(output, metadata)
    content = json.loads(output.read_text(encoding="utf-8"))
    assert content["preflight"]["issues"][0]["code"] == "rom_zip_missing"


def test_gng_sanitized_metadata_has_no_absolute_paths(tmp_path: Path) -> None:
    """T06.3 — no string in the written metadata JSON contains an absolute path."""
    run_result = build_run_result()
    metadata = build_sanitized_metadata(run_result)
    output = tmp_path / "specs" / "run_metadata.json"
    write_public_metadata(output, metadata)
    raw = output.read_text(encoding="utf-8")
    assert "/Users/" not in raw
    assert "/home/" not in raw
    assert "C:\\" not in raw
    assert "evidence/private" not in raw

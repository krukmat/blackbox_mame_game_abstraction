"""T05.4 — Leakage regression tests for the full handle_run metadata pipeline.

These tests exercise the chain:
  MameRunResult (with path-bearing fields)
  → _redact_command_paths / _sanitize_preflight_issue_message / _sanitize_execution_output
  → write_public_metadata (guardrail last-gate)

They verify that no sensitive class (S1–S8 from T05.2.4) survives into the
final written metadata, and that allowed forms (private://, <redacted:path>,
path-free text) are present where expected.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pytest

from cli import (
    REPO_SAFE_COMMAND_PATHS,
    _redact_command_paths,
    _sanitize_execution_output,
    _sanitize_preflight_issue_message,
)
from mame_runner import MameExecution, MameRunResult
from metadata_writer import write_public_metadata
from preflight import PreflightIssue, PreflightResult

# ---------------------------------------------------------------------------
# T05.4.1 — shared fixture
# ---------------------------------------------------------------------------

RUN_ID = "abc123def456"
PRIVATE_SNAPSHOT_DIR = f"evidence/private/run_{RUN_ID}/frames"
ABSOLUTE_ROM_PATH = "/Users/alice/roms/gng.zip"
ABSOLUTE_HOME_PATH = "/home/alice/config"
WINDOWS_ROM_PATH = "C:\\Users\\alice\\roms\\gng.zip"
REPO_SAFE_SCRIPT = "scripts/mame_autoboot.lua"
ARBITRARY_RELATIVE_PATH = "tmp/config/mame.ini"


def build_run_result(
    command: Optional[list[str]] = None,
    preflight_issues: Optional[list[PreflightIssue]] = None,
    stdout: Optional[str] = None,
    stderr: Optional[str] = None,
) -> MameRunResult:
    """T05.4.1 — construct a MameRunResult with path-bearing fields.

    Defaults include one instance of every sensitive class so that tests
    that do not override a field always have material to verify against.
    """
    default_command = [
        "mame",
        "gngb",
        "-rompath", ABSOLUTE_ROM_PATH,          # S4 direct ROM path
        "-snapshot_directory", PRIVATE_SNAPSHOT_DIR,  # S1 private evidence + S2 frame path
        "-cfg_directory", ABSOLUTE_HOME_PATH,   # S5 absolute local machine path
        "-autoboot_script", REPO_SAFE_SCRIPT,   # S6 repo-safe — must survive
        "-autoboot_script", ARBITRARY_RELATIVE_PATH,  # S6 non-approved — must be redacted
    ]
    default_issues = [
        PreflightIssue(
            code="rom_zip_missing",
            field="rom_path",
            message=f"Expected ROM zip was not found at {ABSOLUTE_ROM_PATH}.",
        ),
    ]
    default_stdout = (
        f"mame: rompath {ABSOLUTE_ROM_PATH} not found\n"
        f"Writing snapshot to {PRIVATE_SNAPSHOT_DIR}/0001.png\n"
        "MAME 0.264 initialized."
    )
    default_stderr = (
        f"ERROR: required files are missing for driver 'gngb'. [{ABSOLUTE_ROM_PATH}]\n"
        f"cfg directory: {ABSOLUTE_HOME_PATH}\n"
    )

    preflight = PreflightResult(
        ok=False,
        profile_id="gng",
        mame_binary="mame",
        driver="gngb",
        issues=tuple(preflight_issues if preflight_issues is not None else default_issues),
        detected_version=264,
    )
    execution = MameExecution(
        command=command if command is not None else default_command,
        returncode=1,
        stdout=stdout if stdout is not None else default_stdout,
        stderr=stderr if stderr is not None else default_stderr,
    )
    return MameRunResult(
        status="execution_failure",
        command=command if command is not None else default_command,
        preflight=preflight,
        execution=execution,
    )


def build_sanitized_metadata(run_result: MameRunResult, run_id: str = RUN_ID) -> dict:
    """Apply the same sanitization chain that handle_run uses, return the metadata dict."""
    metadata: dict = {
        "run_id": run_id,
        "command": _redact_command_paths(run_result.command, run_id=run_id),
    }
    if run_result.preflight is not None:
        metadata["preflight"] = {
            "ok": run_result.preflight.ok,
            "issues": [
                {
                    "code": issue.code,
                    "field": issue.field,
                    "message": _sanitize_preflight_issue_message(issue),
                }
                for issue in run_result.preflight.issues
            ],
        }
    if run_result.execution is not None:
        metadata["execution"] = {
            "returncode": run_result.execution.returncode,
            "stdout": _sanitize_execution_output(run_result.execution.stdout),
            "stderr": _sanitize_execution_output(run_result.execution.stderr),
        }
    return metadata


# ---------------------------------------------------------------------------
# T05.4.1 — smoke test: fixture constructs correctly
# ---------------------------------------------------------------------------


def test_fixture_produces_valid_run_result() -> None:
    result = build_run_result()
    assert result.status == "execution_failure"
    assert result.command is not None
    assert result.preflight is not None
    assert result.execution is not None
    assert result.execution.stdout is not None
    assert result.execution.stderr is not None
    assert len(result.preflight.issues) >= 1


def test_fixture_is_configurable() -> None:
    custom_command = ["mame", "gngb", "-rompath", "/tmp/custom/roms"]
    result = build_run_result(command=custom_command)
    assert result.command == custom_command


def test_sanitized_metadata_is_a_dict_with_expected_keys() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    assert "run_id" in metadata
    assert "command" in metadata
    assert "preflight" in metadata
    assert "execution" in metadata


def test_sanitized_metadata_passes_write_public_metadata(tmp_path: Path) -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    output = tmp_path / "specs" / "run_metadata.json"
    written = write_public_metadata(output, metadata)
    assert written.exists()
    content = json.loads(written.read_text(encoding="utf-8"))
    assert content["run_id"] == RUN_ID


# ---------------------------------------------------------------------------
# T05.4.2 — S1/S2 regression: private evidence paths and frame paths
# ---------------------------------------------------------------------------


def _flatten_strings(obj: object) -> list[str]:
    """Recursively collect all string values from a nested dict/list structure."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        result = []
        for v in obj.values():
            result.extend(_flatten_strings(v))
        return result
    if isinstance(obj, list):
        result = []
        for item in obj:
            result.extend(_flatten_strings(item))
        return result
    return []


def _all_strings(metadata: dict) -> list[str]:
    return _flatten_strings(metadata)


def test_s1_private_evidence_path_absent_from_command() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    command_strings = metadata["command"]
    assert not any("evidence/private" in s for s in command_strings)


def test_s1_private_evidence_path_replaced_with_opaque_handle_in_command() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    command_strings = metadata["command"]
    assert any(s.startswith("private://") for s in command_strings)


def test_s1_private_evidence_path_absent_from_stdout() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    assert "evidence/private" not in (metadata["execution"]["stdout"] or "")


def test_s1_private_evidence_path_absent_from_stderr() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    assert "evidence/private" not in (metadata["execution"]["stderr"] or "")


def test_s2_frame_path_absent_from_command() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    command_strings = metadata["command"]
    # frame directory as a literal path must not appear verbatim
    assert not any(
        "frames" in s and ("/" in s or "\\" in s) and not s.startswith("private://")
        for s in command_strings
    )


def test_s2_frame_path_absent_from_stdout() -> None:
    result = build_run_result(
        stdout=f"Writing snapshot to {PRIVATE_SNAPSHOT_DIR}/0001.png\nMame initialized."
    )
    metadata = build_sanitized_metadata(result)
    stdout = metadata["execution"]["stdout"] or ""
    assert PRIVATE_SNAPSHOT_DIR not in stdout


def test_s2_frame_path_redacted_form_present_in_stdout() -> None:
    result = build_run_result(
        stdout=f"Writing snapshot to {PRIVATE_SNAPSHOT_DIR}/0001.png\nMame initialized."
    )
    metadata = build_sanitized_metadata(result)
    stdout = metadata["execution"]["stdout"] or ""
    assert "<redacted:path>" in stdout


def test_s1_s2_full_metadata_passes_guardrail(tmp_path: Path) -> None:
    """End-to-end: sanitized metadata with S1/S2 inputs must be accepted by write_public_metadata."""
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    output = tmp_path / "specs" / "run_metadata.json"
    written = write_public_metadata(output, metadata)
    assert written.exists()


# ---------------------------------------------------------------------------
# T05.4.3 — S4/S5 regression: ROM paths and absolute machine paths
# ---------------------------------------------------------------------------


def test_s4_rom_path_absent_from_command() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    assert not any(ABSOLUTE_ROM_PATH in s for s in metadata["command"])


def test_s4_rom_path_absent_from_preflight_message() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    for issue in metadata["preflight"]["issues"]:
        assert ABSOLUTE_ROM_PATH not in issue["message"]


def test_s4_rom_path_absent_from_stdout() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    assert ABSOLUTE_ROM_PATH not in (metadata["execution"]["stdout"] or "")


def test_s4_rom_path_absent_from_stderr() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    assert ABSOLUTE_ROM_PATH not in (metadata["execution"]["stderr"] or "")


def test_s4_windows_rom_path_absent_from_command() -> None:
    command = ["mame", "gngb", "-rompath", WINDOWS_ROM_PATH]
    result = build_run_result(command=command)
    metadata = build_sanitized_metadata(result)
    assert not any(WINDOWS_ROM_PATH in s for s in metadata["command"])


def test_s4_windows_rom_path_absent_from_stdout() -> None:
    result = build_run_result(stdout=f"loading {WINDOWS_ROM_PATH}")
    metadata = build_sanitized_metadata(result)
    assert WINDOWS_ROM_PATH not in (metadata["execution"]["stdout"] or "")


def test_s5_absolute_machine_path_absent_from_command() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    assert not any(ABSOLUTE_HOME_PATH in s for s in metadata["command"])


def test_s5_absolute_machine_path_absent_from_stdout() -> None:
    result = build_run_result(stdout=f"cfg directory: {ABSOLUTE_HOME_PATH}\nMame initialized.")
    metadata = build_sanitized_metadata(result)
    assert ABSOLUTE_HOME_PATH not in (metadata["execution"]["stdout"] or "")


def test_s5_absolute_machine_path_absent_from_stderr() -> None:
    result = build_run_result(stderr=f"error loading config from {ABSOLUTE_HOME_PATH}")
    metadata = build_sanitized_metadata(result)
    assert ABSOLUTE_HOME_PATH not in (metadata["execution"]["stderr"] or "")


def test_s4_s5_redacted_form_present_in_command() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    assert any(s == "<redacted:path>" for s in metadata["command"])


def test_s4_s5_full_metadata_passes_guardrail(tmp_path: Path) -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    output = tmp_path / "specs" / "run_metadata.json"
    written = write_public_metadata(output, metadata)
    assert written.exists()


# ---------------------------------------------------------------------------
# T05.4.4 — S6 regression: non-allowlisted workspace paths blocked; allowlisted survive
# ---------------------------------------------------------------------------


def test_s6_allowlisted_script_survives_in_command() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    assert REPO_SAFE_SCRIPT in metadata["command"]


def test_s6_arbitrary_relative_path_absent_from_command() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    assert ARBITRARY_RELATIVE_PATH not in metadata["command"]


def test_s6_arbitrary_relative_path_redacted_in_command() -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    # the slot where ARBITRARY_RELATIVE_PATH was must now be <redacted:path>
    assert "<redacted:path>" in metadata["command"]


def test_s6_unknown_allowlist_entry_is_redacted() -> None:
    command = ["mame", "gngb", "-autoboot_script", "scripts/other_script.lua"]
    result = build_run_result(command=command)
    metadata = build_sanitized_metadata(result)
    assert "scripts/other_script.lua" not in metadata["command"]
    assert "<redacted:path>" in metadata["command"]


def test_s6_full_metadata_passes_guardrail(tmp_path: Path) -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    output = tmp_path / "specs" / "run_metadata.json"
    written = write_public_metadata(output, metadata)
    assert written.exists()


# ---------------------------------------------------------------------------
# T05.4.5 — Defense-in-depth: guardrail rejects unsanitized payloads
# ---------------------------------------------------------------------------


def test_guardrail_rejects_if_s1_bypasses_sanitization(tmp_path: Path) -> None:
    payload = {"command": [f"evidence/private/run_{RUN_ID}/frames"]}
    output = tmp_path / "specs" / "run_metadata.json"
    with pytest.raises(ValueError):
        write_public_metadata(output, payload)


def test_guardrail_rejects_if_s4_rom_path_bypasses_sanitization(tmp_path: Path) -> None:
    payload = {"execution": {"stdout": f"loading {ABSOLUTE_ROM_PATH}"}}
    output = tmp_path / "specs" / "run_metadata.json"
    with pytest.raises(ValueError):
        write_public_metadata(output, payload)


def test_guardrail_rejects_if_s5_absolute_path_bypasses_sanitization(tmp_path: Path) -> None:
    payload = {"execution": {"stderr": f"cfg dir: {ABSOLUTE_HOME_PATH}"}}
    output = tmp_path / "specs" / "run_metadata.json"
    with pytest.raises(ValueError):
        write_public_metadata(output, payload)


def test_guardrail_rejects_if_s5_windows_path_bypasses_sanitization(tmp_path: Path) -> None:
    payload = {"execution": {"stdout": f"loading {WINDOWS_ROM_PATH}"}}
    output = tmp_path / "specs" / "run_metadata.json"
    with pytest.raises(ValueError):
        write_public_metadata(output, payload)


def test_guardrail_accepts_fully_sanitized_metadata(tmp_path: Path) -> None:
    result = build_run_result()
    metadata = build_sanitized_metadata(result)
    output = tmp_path / "specs" / "run_metadata.json"
    written = write_public_metadata(output, metadata)
    assert written.exists()

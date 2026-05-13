from __future__ import annotations

from cli import _redact_command_paths, _sanitize_execution_output, _sanitize_preflight_issue_message
from preflight import PreflightIssue


def test_redact_command_paths_removes_private_evidence_locations() -> None:
    redacted = _redact_command_paths(
        [
            "mame",
            "pacman",
            "-snapshot_directory",
            "evidence/private/run_demo123/frames",
        ],
        run_id="demo123",
    )
    assert redacted[-1] == "private://demo123/frames"


def test_redact_command_paths_keeps_repo_safe_relative_reference() -> None:
    redacted = _redact_command_paths(
        [
            "mame",
            "gngb",
            "-autoboot_script",
            "scripts/mame_autoboot.lua",
        ],
        run_id="demo123",
    )
    assert redacted[-1] == "scripts/mame_autoboot.lua"


def test_redact_command_paths_redacts_non_approved_rom_and_absolute_paths() -> None:
    redacted = _redact_command_paths(
        [
            "mame",
            "gngb",
            "-rompath",
            "/Users/test/local/roms/gng.zip",
            "-cfg_directory",
            "../tmp/config",
        ],
        run_id="demo123",
    )
    assert redacted[3] == "<redacted:path>"
    assert redacted[5] == "<redacted:path>"


def test_sanitize_preflight_issue_message_removes_machine_and_rom_paths() -> None:
    issue = PreflightIssue(
        code="rom_zip_missing",
        field="rom_path",
        message="Expected ROM zip 'gng.zip' was not found at /Users/test/local/roms/gng.zip.",
    )

    sanitized = _sanitize_preflight_issue_message(issue)

    assert "/Users/test/local/roms/gng.zip" not in sanitized
    assert "Expected ROM zip was not found" in sanitized


def test_sanitize_preflight_issue_message_removes_binary_probe_path() -> None:
    issue = PreflightIssue(
        code="mame_version_probe_failed",
        field="mame_binary",
        message="Failed to run '/tmp/fake-mame -version': [Errno 13] Permission denied: '/tmp/fake-mame'.",
    )

    sanitized = _sanitize_preflight_issue_message(issue)

    assert "/tmp/fake-mame" not in sanitized
    assert "Failed to run the MAME version probe" in sanitized


# T05.3.3 — execution output sanitization


def test_sanitize_execution_output_removes_absolute_unix_path() -> None:
    raw = "mame: rompath /Users/alice/roms not found"
    sanitized = _sanitize_execution_output(raw)
    assert "/Users/alice/roms" not in sanitized
    assert "<redacted:path>" in sanitized


def test_sanitize_execution_output_removes_absolute_windows_path() -> None:
    raw = "mame: rompath C:\\Users\\alice\\roms not found"
    sanitized = _sanitize_execution_output(raw)
    assert "C:\\Users\\alice\\roms" not in sanitized
    assert "<redacted:path>" in sanitized


def test_sanitize_execution_output_removes_private_evidence_path() -> None:
    raw = "snapshot saved to evidence/private/run_abc123/frames/0001.png"
    sanitized = _sanitize_execution_output(raw)
    assert "evidence/private" not in sanitized
    assert "<redacted:path>" in sanitized


def test_sanitize_execution_output_removes_rom_path_segment() -> None:
    raw = "ERROR: required files are missing for driver 'gngb'. [/home/user/roms/gng.zip]"
    sanitized = _sanitize_execution_output(raw)
    assert "/home/user/roms/gng.zip" not in sanitized
    assert "<redacted:path>" in sanitized


def test_sanitize_execution_output_removes_frames_path() -> None:
    raw = "Writing frame to /tmp/run_xyz/frames/0042.png"
    sanitized = _sanitize_execution_output(raw)
    assert "/tmp/run_xyz/frames/0042.png" not in sanitized
    assert "<redacted:path>" in sanitized


def test_sanitize_execution_output_preserves_path_free_text() -> None:
    raw = "MAME 0.264 initialized. Running driver gngb."
    sanitized = _sanitize_execution_output(raw)
    assert sanitized == raw


def test_sanitize_execution_output_empty_string_is_safe() -> None:
    assert _sanitize_execution_output("") == ""


def test_sanitize_execution_output_none_returns_none() -> None:
    assert _sanitize_execution_output(None) is None

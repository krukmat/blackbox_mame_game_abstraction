from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from cli import (
    _redact_command_paths,
    _sanitize_execution_output,
    _sanitize_preflight_issue_message,
    build_parser,
    handle_extract_trace,
    handle_run,
)
from preflight import PreflightIssue
from source_profiles import get_source_profile
from tests.conftest import ROOT

_INPUT_PLAN = ROOT / "plans" / "basic_controls.yaml"


def _make_run_args(**overrides) -> argparse.Namespace:
    """Build a minimal argparse.Namespace for handle_run with safe defaults."""
    defaults = dict(
        rom="gngb",
        source_profile=None,
        input_plan=_INPUT_PLAN,
        mame_binary="mame",
        working_dir=Path("."),
        rom_path=None,
        frames_to_run=None,
        seconds_to_run=None,
        dry_run=True,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


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


# ---------------------------------------------------------------------------
# T07.2 — --source-profile CLI contract tests
# ---------------------------------------------------------------------------


def test_source_profile_gng_resolves_to_gngb_driver() -> None:
    """T07.2 — get_source_profile('gng') returns profile with mame_driver == 'gngb'."""
    profile = get_source_profile("gng")
    assert profile.mame_driver == "gngb"
    assert profile.profile_id == "gng"


def test_handle_run_with_source_profile_attaches_preflight(tmp_path: Path, monkeypatch) -> None:
    """T07.2 — handle_run with source_profile='gng' produces metadata with preflight key."""
    monkeypatch.chdir(tmp_path)
    args = _make_run_args(rom="gngb", source_profile="gng")
    metadata = handle_run(args)
    assert "preflight" in metadata


def test_handle_run_preflight_profile_id_is_gng(tmp_path: Path, monkeypatch) -> None:
    """T07.2 — preflight.profile_id == 'gng' when --source-profile gng is used."""
    monkeypatch.chdir(tmp_path)
    args = _make_run_args(rom="gngb", source_profile="gng")
    metadata = handle_run(args)
    assert metadata["preflight"]["profile_id"] == "gng"


def test_handle_run_preflight_driver_is_gngb(tmp_path: Path, monkeypatch) -> None:
    """T07.2 — preflight.driver == 'gngb' when --source-profile gng is used."""
    monkeypatch.chdir(tmp_path)
    args = _make_run_args(rom="gngb", source_profile="gng")
    metadata = handle_run(args)
    assert metadata["preflight"]["driver"] == "gngb"


def test_unknown_source_profile_raises_before_run() -> None:
    """T07.2 — get_source_profile with unknown id raises ValueError with clear message."""
    with pytest.raises(ValueError, match="Unknown source profile 'nonexistent'"):
        get_source_profile("nonexistent")


def test_handle_run_exports_private_input_plan_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    metadata = handle_run(_make_run_args())

    run_id = metadata["run_id"]
    exported_plan = tmp_path / "evidence" / "private" / f"run_{run_id}" / "logs" / "input_plan.json"
    payload = json.loads(exported_plan.read_text(encoding="utf-8"))

    assert exported_plan.exists()
    assert payload[0] == {"frame": 0, "buttons": ["coin"]}


def test_extract_trace_subcommand_requires_input_plan() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["extract-trace", "--run-id", "demo"])


def test_handle_extract_trace_returns_trace_output(monkeypatch, tmp_path: Path) -> None:
    expected_output = tmp_path / "specs" / "traces" / "gng_trace.json"

    def fake_extract_run_trace(*, run_id: str, input_plan_path: Path, output_path: Path) -> Path:
        assert run_id == "demo"
        assert input_plan_path == tmp_path / "plans" / "gng_gameplay.yaml"
        assert output_path == expected_output
        return output_path

    monkeypatch.setattr("cli.extract_run_trace", fake_extract_run_trace)
    args = argparse.Namespace(
        run_id="demo",
        input_plan=tmp_path / "plans" / "gng_gameplay.yaml",
        output=expected_output,
    )

    result = handle_extract_trace(args)

    assert result == {"status": "trace_extracted", "output": str(expected_output)}

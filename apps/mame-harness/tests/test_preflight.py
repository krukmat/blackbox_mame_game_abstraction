from __future__ import annotations

from pathlib import Path

from preflight import MAME_MINIMUM_VERSION, parse_mame_version, run_preflight
from source_profiles import GNG_SOURCE_PROFILE, SourceProfile


def test_parse_mame_version_accepts_standard_output() -> None:
    assert parse_mame_version("0.287 (mame0287)") == 287
    assert parse_mame_version("0.240") == 240


def test_parse_mame_version_rejects_unexpected_output() -> None:
    assert parse_mame_version("MAME 0.287") is None
    assert parse_mame_version("not-a-version") is None


def test_preflight_fails_when_driver_contract_is_wrong(tmp_path: Path) -> None:
    bad_profile = SourceProfile(
        profile_id="gng",
        display_name="bad",
        mame_driver="gng",
        expected_rom_zip="gng.zip",
        rom_path_kind="directory_containing_rom_zip",
        rom_path_example=Path("local/roms"),
        base_input_plan=Path("plans/basic_controls.yaml"),
        default_frames_to_run=300,
        autoboot_script=Path("scripts/mame_autoboot.lua"),
        private_usage_only=True,
        public_output_boundary="private only",
        notes=(),
    )

    result = run_preflight(bad_profile, "missing-mame", tmp_path)

    assert result.ok is False
    assert result.issues[0].code == "driver_contract_mismatch"


def test_preflight_fails_when_mame_binary_is_missing(tmp_path: Path) -> None:
    result = run_preflight(GNG_SOURCE_PROFILE, "missing-mame-binary", tmp_path)

    assert result.ok is False
    assert result.issues[0].code == "mame_binary_missing"


def test_preflight_fails_when_version_is_too_old(tmp_path: Path) -> None:
    rom_zip = tmp_path / "gng.zip"
    rom_zip.write_text("placeholder")
    fake_mame = _write_fake_mame(tmp_path, "0.239 (mame0239)\n")

    result = run_preflight(GNG_SOURCE_PROFILE, str(fake_mame), tmp_path)

    assert result.ok is False
    assert result.issues[0].code == "mame_version_too_old"
    assert f"0.{MAME_MINIMUM_VERSION}" in result.issues[0].message


def test_preflight_fails_when_rom_path_is_missing(tmp_path: Path) -> None:
    fake_mame = _write_fake_mame(tmp_path, "0.287 (mame0287)\n")
    result = run_preflight(GNG_SOURCE_PROFILE, str(fake_mame), None)

    assert result.ok is False
    assert result.issues[0].code == "rom_path_missing"


def test_preflight_fails_when_rom_zip_is_missing_from_directory(tmp_path: Path) -> None:
    fake_mame = _write_fake_mame(tmp_path, "0.287 (mame0287)\n")

    result = run_preflight(GNG_SOURCE_PROFILE, str(fake_mame), tmp_path)

    assert result.ok is False
    assert result.detected_version == 287
    assert result.issues[0].code == "rom_zip_missing"


def test_preflight_accepts_directory_containing_expected_rom_zip(tmp_path: Path) -> None:
    rom_zip = tmp_path / "gng.zip"
    rom_zip.write_text("placeholder")
    fake_mame = _write_fake_mame(tmp_path, "0.287 (mame0287)\n")

    result = run_preflight(GNG_SOURCE_PROFILE, str(fake_mame), tmp_path)

    assert result.ok is True
    assert result.detected_version == 287
    assert result.rom_zip_path == rom_zip


def test_preflight_accepts_direct_rom_zip_path(tmp_path: Path) -> None:
    rom_zip = tmp_path / "gng.zip"
    rom_zip.write_text("placeholder")
    fake_mame = _write_fake_mame(tmp_path, "0.287 (mame0287)\n")

    result = run_preflight(GNG_SOURCE_PROFILE, str(fake_mame), rom_zip)

    assert result.ok is True
    assert result.rom_zip_path == rom_zip


def _write_fake_mame(tmp_path: Path, version_output: str) -> Path:
    fake_mame = tmp_path / "fake-mame"
    fake_mame.write_text(f"#!/bin/sh\necho '{version_output.strip()}'\n")
    fake_mame.chmod(0o755)
    return fake_mame

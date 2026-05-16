from __future__ import annotations

from pathlib import Path

import pytest

from source_profiles import GNG_SOURCE_PROFILE, get_source_profile


def test_gng_profile_encodes_the_local_driver_contract() -> None:
    profile = get_source_profile("gng")

    assert profile is GNG_SOURCE_PROFILE
    assert profile.mame_driver == "gngb"
    assert profile.expected_rom_zip == "gng.zip"
    assert profile.rom_path_kind == "directory_containing_rom_zip"
    assert profile.rom_path_example == Path("local/roms")


def test_gng_profile_includes_base_capture_parameters() -> None:
    profile = get_source_profile("gng")

    assert profile.base_input_plan == Path("plans/generated/gng_boot_only.yaml")
    assert profile.default_frames_to_run == 300
    assert profile.autoboot_script == Path("scripts/mame_autoboot.lua")
    assert profile.private_usage_only is True


def test_gng_profile_documents_clean_room_boundary() -> None:
    profile = get_source_profile("gng")

    assert "private observation" in profile.public_output_boundary
    assert "faithful gameplay reproduction" in profile.public_output_boundary
    assert any("gngb" in note for note in profile.notes)


def test_unknown_source_profile_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="Unknown source profile 'missing'"):
        get_source_profile("missing")

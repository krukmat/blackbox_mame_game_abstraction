from __future__ import annotations

from pathlib import Path
import tempfile

import pytest

from mapping_profiles import DeviceProfile, load_mapping_profile
from sdl_gamecontrollerdb_importer import (
    build_device_profile_payload_from_sdl_entry,
    import_sdl_gamecontrollerdb_file,
    parse_sdl_gamecontrollerdb,
    select_sdl_controller_entry,
)


def test_importer_writes_round_trippable_device_profile(tmp_path: Path) -> None:
    db_path = tmp_path / "gamecontrollerdb.txt"
    db_path.write_text(
        "03000000de280000ff11000001000000,8BitDo Pro 2,"
        "a:b0,b:b1,x:b3,y:b4,back:b10,start:b11,"
        "dpup:h0.1,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,"
        "leftshoulder:b6,rightshoulder:b7,platform:Mac OS X,\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "profiles" / "devices" / "8bitdo_pro2.yaml"

    imported = import_sdl_gamecontrollerdb_file(
        db_path=db_path,
        output_path=output_path,
    )

    assert imported.output_path == output_path
    assert imported.warnings == ()
    loaded = load_mapping_profile(output_path)
    assert isinstance(loaded, DeviceProfile)
    assert loaded.id == "8bitdo_pro_2_sdl"
    assert loaded.source == "sdl_gamecontrollerdb"
    assert loaded.device.guid == "03000000de280000ff11000001000000"
    assert loaded.raw_to_canonical["b0"] == "south"
    assert loaded.raw_to_canonical["h0.8"] == "dpad_left"


def test_importer_reports_unsupported_controls_as_warnings(tmp_path: Path) -> None:
    db_path = tmp_path / "gamecontrollerdb.txt"
    db_path.write_text(
        "03000000de280000ff11000001000000,Pad,"
        "a:b0,lefttrigger:a4,rightx:a3,guide:b12,platform:Mac OS X,\n",
        encoding="utf-8",
    )

    imported = import_sdl_gamecontrollerdb_file(
        db_path=db_path,
        output_path=tmp_path / "profiles" / "devices" / "pad.yaml",
    )

    assert imported.profile.raw_to_canonical["b0"] == "south"
    assert imported.profile.raw_to_canonical["b12"] == "pause"
    assert list(imported.warnings) == [
        "ignored unsupported SDL control 'lefttrigger'",
        "ignored unsupported SDL control 'rightx'",
    ]


def test_parser_rejects_duplicate_sdl_control_field() -> None:
    with pytest.raises(ValueError, match="defines SDL control 'a' more than once"):
        parse_sdl_gamecontrollerdb_text(
            "03000000de280000ff11000001000000,Pad,a:b0,a:b1,\n"
        )


def test_importer_rejects_duplicate_raw_binding_for_two_canonical_controls() -> None:
    entry = select_sdl_controller_entry(
        parse_sdl_gamecontrollerdb_text(
            "03000000de280000ff11000001000000,Pad,a:b0,b:b0,\n"
        )
    )

    with pytest.raises(ValueError, match="reuses raw binding 'b0'"):
        build_device_profile_payload_from_sdl_entry(entry)


def test_importer_requires_selector_when_db_contains_multiple_entries(tmp_path: Path) -> None:
    db_path = tmp_path / "gamecontrollerdb.txt"
    db_path.write_text(
        "03000000000000000000000000000000,Pad One,a:b0,\n"
        "04000000000000000000000000000000,Pad Two,a:b1,\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="contains multiple entries; pass --guid or --name"):
        import_sdl_gamecontrollerdb_file(
            db_path=db_path,
            output_path=tmp_path / "profiles" / "devices" / "pad.yaml",
        )


def test_importer_rejects_unsafe_output_path(tmp_path: Path) -> None:
    db_path = tmp_path / "gamecontrollerdb.txt"
    db_path.write_text(
        "03000000de280000ff11000001000000,Pad,a:b0,\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="blocked public output directory"):
        import_sdl_gamecontrollerdb_file(
            db_path=db_path,
            output_path=tmp_path / "specs" / "frames" / "pad.yaml",
        )


def test_parser_supports_escaped_commas_in_controller_name(tmp_path: Path) -> None:
    db_path = tmp_path / "gamecontrollerdb.txt"
    db_path.write_text(
        "03000000de280000ff11000001000000,Pad\\, Special Edition,a:b0,platform:Mac OS X,\n",
        encoding="utf-8",
    )

    entries = parse_sdl_gamecontrollerdb(db_path)

    assert entries[0].name == "Pad, Special Edition"


def parse_sdl_gamecontrollerdb_text(contents: str) -> list:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "parse_input.txt"
        path.write_text(contents, encoding="utf-8")
        return parse_sdl_gamecontrollerdb(path)

from __future__ import annotations

from pathlib import Path
import tempfile

import pytest

from mapping_profiles import DeviceProfile, load_mapping_profile
from retroarch_mapping_importer import (
    build_device_profile_payload_from_retroarch_config,
    import_retroarch_autoconfig_file,
    parse_retroarch_autoconfig,
)


def test_importer_writes_round_trippable_device_profile(tmp_path: Path) -> None:
    config_path = tmp_path / "controller.cfg"
    config_path.write_text(
        "\n".join(
            [
                'input_device = "8BitDo Pro 2"',
                'input_vendor_id = "11720"',
                'input_product_id = "6145"',
                'input_b_btn = "0"',
                'input_a_btn = "1"',
                'input_y_btn = "3"',
                'input_x_btn = "4"',
                'input_select_btn = "10"',
                'input_start_btn = "11"',
                'input_up_axis = "-1"',
                'input_down_axis = "+1"',
                'input_left_btn = "13"',
                'input_right_btn = "14"',
                'input_l_btn = "6"',
                'input_r_btn = "7"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "profiles" / "devices" / "8bitdo_pro2_retroarch.yaml"

    imported = import_retroarch_autoconfig_file(
        config_path=config_path,
        output_path=output_path,
    )

    assert imported.warnings == ()
    loaded = load_mapping_profile(output_path)
    assert isinstance(loaded, DeviceProfile)
    assert loaded.id == "8bitdo_pro_2_retroarch"
    assert loaded.source == "retroarch_autoconfig"
    assert loaded.device.guid == "vendor:11720:product:6145"
    assert loaded.raw_to_canonical["btn:0"] == "south"
    assert loaded.raw_to_canonical["btn:1"] == "east"
    assert loaded.raw_to_canonical["axis:-1"] == "dpad_up"


def test_importer_tolerates_missing_optional_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "controller.cfg"
    config_path.write_text(
        'input_b_btn = "0"\ninput_start_btn = "9"\n',
        encoding="utf-8",
    )

    imported = import_retroarch_autoconfig_file(
        config_path=config_path,
        output_path=tmp_path / "profiles" / "devices" / "pad.yaml",
    )

    assert imported.profile.device.name == "RetroArch Controller"
    assert imported.profile.device.guid is None


def test_importer_documents_retroarch_b_as_south_and_a_as_east() -> None:
    config = parse_retroarch_autoconfig_text(
        'input_b_btn = "0"\ninput_a_btn = "1"\n'
    )

    payload, warnings = build_device_profile_payload_from_retroarch_config(config)

    assert warnings == []
    assert payload["raw_to_canonical"] == {
        "btn:0": "south",
        "btn:1": "east",
    }


def test_importer_reports_unsupported_fields_as_warnings(tmp_path: Path) -> None:
    config_path = tmp_path / "controller.cfg"
    config_path.write_text(
        "\n".join(
            [
                'input_device = "Pad"',
                'input_b_btn = "0"',
                'input_l2_btn = "8"',
                'input_menu_toggle_btn = "12"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    imported = import_retroarch_autoconfig_file(
        config_path=config_path,
        output_path=tmp_path / "profiles" / "devices" / "pad.yaml",
    )

    assert imported.warnings == (
        "ignored unsupported RetroArch field 'input_l2_btn'",
        "ignored unsupported RetroArch field 'input_menu_toggle_btn'",
    )


def test_parser_rejects_malformed_config_line(tmp_path: Path) -> None:
    config_path = tmp_path / "controller.cfg"
    config_path.write_text(
        'input_b_btn "0"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must use KEY = VALUE syntax"):
        parse_retroarch_autoconfig(config_path)


def test_importer_rejects_duplicate_raw_binding(tmp_path: Path) -> None:
    config_path = tmp_path / "controller.cfg"
    config_path.write_text(
        'input_b_btn = "0"\ninput_a_btn = "0"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="reuses raw binding 'btn:0'"):
        import_retroarch_autoconfig_file(
            config_path=config_path,
            output_path=tmp_path / "profiles" / "devices" / "pad.yaml",
        )


def test_importer_rejects_unsafe_output_path(tmp_path: Path) -> None:
    config_path = tmp_path / "controller.cfg"
    config_path.write_text(
        'input_b_btn = "0"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="blocked public output directory"):
        import_retroarch_autoconfig_file(
            config_path=config_path,
            output_path=tmp_path / "specs" / "frames" / "pad.yaml",
        )


def parse_retroarch_autoconfig_text(contents: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "retroarch.cfg"
        path.write_text(contents, encoding="utf-8")
        return parse_retroarch_autoconfig(path)

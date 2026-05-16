from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from mapping_profiles import DeviceProfile, load_mapping_profile
from sdl_gamecontrollerdb_importer import write_device_profile_payload


RETROARCH_TO_CANONICAL_CONTROL = {
    "input_up_btn": "dpad_up",
    "input_up_axis": "dpad_up",
    "input_down_btn": "dpad_down",
    "input_down_axis": "dpad_down",
    "input_left_btn": "dpad_left",
    "input_left_axis": "dpad_left",
    "input_right_btn": "dpad_right",
    "input_right_axis": "dpad_right",
    "input_b_btn": "south",
    "input_a_btn": "east",
    "input_y_btn": "north",
    "input_x_btn": "west",
    "input_select_btn": "select",
    "input_start_btn": "start",
    "input_l_btn": "l1",
    "input_r_btn": "r1",
}
RETROARCH_METADATA_FIELDS = {
    "input_device",
    "input_vendor_id",
    "input_product_id",
}


@dataclass(frozen=True, slots=True)
class RetroArchAutoconfig:
    fields: dict[str, str]


@dataclass(frozen=True, slots=True)
class ImportedRetroArchDeviceProfile:
    output_path: Path
    profile: DeviceProfile
    warnings: tuple[str, ...]


def import_retroarch_autoconfig_file(
    *,
    config_path: Path,
    output_path: Path,
    profile_id: str | None = None,
) -> ImportedRetroArchDeviceProfile:
    config = parse_retroarch_autoconfig(config_path)
    payload, warnings = build_device_profile_payload_from_retroarch_config(
        config,
        profile_id=profile_id,
    )
    write_device_profile_payload(payload, output_path)
    loaded = load_mapping_profile(output_path)
    if not isinstance(loaded, DeviceProfile):
        raise ValueError("imported RetroArch profile did not round-trip as a DeviceProfile")
    return ImportedRetroArchDeviceProfile(
        output_path=output_path,
        profile=loaded,
        warnings=tuple(warnings),
    )


def parse_retroarch_autoconfig(config_path: Path) -> RetroArchAutoconfig:
    fields: dict[str, str] = {}
    for line_number, raw_line in enumerate(config_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"RetroArch autoconfig line {line_number} must use KEY = VALUE syntax")
        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"RetroArch autoconfig line {line_number} is missing a key")
        if key in fields:
            raise ValueError(f"RetroArch autoconfig defines '{key}' more than once")
        fields[key] = _strip_optional_quotes(value)

    if not fields:
        raise ValueError("RetroArch autoconfig file did not contain any settings")
    return RetroArchAutoconfig(fields=fields)


def build_device_profile_payload_from_retroarch_config(
    config: RetroArchAutoconfig,
    *,
    profile_id: str | None = None,
) -> tuple[dict[str, object], list[str]]:
    raw_to_canonical: dict[str, str] = {}
    warnings: list[str] = []
    seen_canonical: dict[str, str] = {}
    seen_raw: dict[str, str] = {}

    for key, value in config.fields.items():
        if key in RETROARCH_METADATA_FIELDS:
            continue
        canonical = RETROARCH_TO_CANONICAL_CONTROL.get(key)
        if canonical is None:
            warnings.append(f"ignored unsupported RetroArch field '{key}'")
            continue

        raw_identifier = _retroarch_binding_to_raw_identifier(key, value)
        existing_key = seen_canonical.get(canonical)
        if existing_key is not None:
            raise ValueError(
                f"RetroArch config maps canonical control '{canonical}' more than once "
                f"via '{existing_key}' and '{key}'"
            )
        existing_canonical = seen_raw.get(raw_identifier)
        if existing_canonical is not None:
            raise ValueError(
                f"RetroArch config reuses raw binding '{raw_identifier}' for canonical controls "
                f"'{existing_canonical}' and '{canonical}'"
            )

        seen_canonical[canonical] = key
        seen_raw[raw_identifier] = canonical
        raw_to_canonical[raw_identifier] = canonical

    if not raw_to_canonical:
        raise ValueError("RetroArch autoconfig does not contain any supported bindings")

    device_name = config.fields.get("input_device", "RetroArch Controller")
    vendor_id = config.fields.get("input_vendor_id")
    product_id = config.fields.get("input_product_id")
    guid = None
    if vendor_id and product_id:
        guid = f"vendor:{vendor_id}:product:{product_id}"

    generated_profile_id = profile_id or _default_profile_id(device_name)
    payload: dict[str, object] = {
        "schema_version": 1,
        "profile_type": "device_profile",
        "id": generated_profile_id,
        "source": "retroarch_autoconfig",
        "device": {
            "kind": "gamecontroller",
            "name": device_name,
            "guid": guid,
        },
        "raw_to_canonical": raw_to_canonical,
        "metadata": {
            "created_by": "retroarch_autoconfig_importer",
            "clean_room_safe": True,
        },
    }
    return payload, warnings


def _retroarch_binding_to_raw_identifier(key: str, value: str) -> str:
    if value == "":
        raise ValueError(f"RetroArch field '{key}' has an empty binding value")
    suffix = key.removeprefix("input_").removesuffix("_btn").removesuffix("_axis")
    if key.endswith("_btn"):
        return f"btn:{value}"
    if key.endswith("_axis"):
        return f"axis:{value}"
    return f"{suffix}:{value}"


def _strip_optional_quotes(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        return stripped[1:-1]
    return stripped


def _default_profile_id(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not normalized:
        return "retroarch_controller"
    return f"{normalized}_retroarch"

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import yaml

from guardrails import ensure_no_private_paths, ensure_public_output_path
from mapping_profiles import DeviceProfile, load_mapping_profile


SDL_TO_CANONICAL_CONTROL = {
    "a": "south",
    "b": "east",
    "x": "west",
    "y": "north",
    "back": "select",
    "start": "start",
    "dpup": "dpad_up",
    "dpdown": "dpad_down",
    "dpleft": "dpad_left",
    "dpright": "dpad_right",
    "leftshoulder": "l1",
    "rightshoulder": "r1",
    "guide": "pause",
}
SDL_METADATA_FIELDS = {
    "crc",
    "hint",
    "platform",
    "sdk",
    "type",
}


@dataclass(frozen=True, slots=True)
class SdlControllerEntry:
    guid: str
    name: str
    bindings: dict[str, str]


@dataclass(frozen=True, slots=True)
class ImportedSdlDeviceProfile:
    output_path: Path
    profile: DeviceProfile
    warnings: tuple[str, ...]


def import_sdl_gamecontrollerdb_file(
    *,
    db_path: Path,
    output_path: Path,
    name: str | None = None,
    guid: str | None = None,
    profile_id: str | None = None,
) -> ImportedSdlDeviceProfile:
    entries = parse_sdl_gamecontrollerdb(db_path)
    entry = select_sdl_controller_entry(entries, name=name, guid=guid)
    payload, warnings = build_device_profile_payload_from_sdl_entry(
        entry,
        profile_id=profile_id,
    )
    write_device_profile_payload(payload, output_path)
    loaded = load_mapping_profile(output_path)
    if not isinstance(loaded, DeviceProfile):
        raise ValueError("imported SDL profile did not round-trip as a DeviceProfile")
    return ImportedSdlDeviceProfile(
        output_path=output_path,
        profile=loaded,
        warnings=tuple(warnings),
    )


def parse_sdl_gamecontrollerdb(db_path: Path) -> list[SdlControllerEntry]:
    entries: list[SdlControllerEntry] = []
    for line_number, raw_line in enumerate(db_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        fields = _split_sdl_csv_fields(line)
        if len(fields) < 3:
            raise ValueError(
                f"SDL GameControllerDB entry on line {line_number} must contain guid, name, and bindings"
            )
        guid = fields[0]
        name = fields[1]
        if not guid or not name:
            raise ValueError(f"SDL GameControllerDB entry on line {line_number} is missing guid or name")

        bindings: dict[str, str] = {}
        for field in fields[2:]:
            if field == "":
                continue
            if ":" not in field:
                raise ValueError(f"SDL GameControllerDB binding '{field}' on line {line_number} is invalid")
            key, value = field.split(":", maxsplit=1)
            if key in bindings:
                raise ValueError(
                    f"SDL GameControllerDB entry '{name}' defines SDL control '{key}' more than once"
                )
            if value == "":
                raise ValueError(
                    f"SDL GameControllerDB entry '{name}' has empty binding value for SDL control '{key}'"
                )
            bindings[key] = value
        entries.append(SdlControllerEntry(guid=guid, name=name, bindings=bindings))

    if not entries:
        raise ValueError("SDL GameControllerDB file did not contain any controller entries")
    return entries


def select_sdl_controller_entry(
    entries: list[SdlControllerEntry],
    *,
    name: str | None = None,
    guid: str | None = None,
) -> SdlControllerEntry:
    if name is None and guid is None and len(entries) > 1:
        raise ValueError("SDL GameControllerDB file contains multiple entries; pass --guid or --name")

    matches = entries
    if guid is not None:
        matches = [entry for entry in matches if entry.guid == guid]
    if name is not None:
        matches = [entry for entry in matches if entry.name == name]

    if not matches:
        selector = []
        if guid is not None:
            selector.append(f"guid '{guid}'")
        if name is not None:
            selector.append(f"name '{name}'")
        raise ValueError(f"no SDL GameControllerDB entry matched {' and '.join(selector)}")

    if len(matches) > 1:
        raise ValueError("SDL GameControllerDB selection is ambiguous; refine with --guid or --name")
    return matches[0]


def build_device_profile_payload_from_sdl_entry(
    entry: SdlControllerEntry,
    *,
    profile_id: str | None = None,
) -> tuple[dict[str, object], list[str]]:
    raw_to_canonical: dict[str, str] = {}
    warnings: list[str] = []
    seen_canonical: dict[str, str] = {}
    seen_raw: dict[str, str] = {}

    for sdl_control, raw_identifier in entry.bindings.items():
        if sdl_control in SDL_METADATA_FIELDS:
            continue

        canonical = SDL_TO_CANONICAL_CONTROL.get(sdl_control)
        if canonical is None:
            warnings.append(f"ignored unsupported SDL control '{sdl_control}'")
            continue

        existing_sdl_control = seen_canonical.get(canonical)
        if existing_sdl_control is not None:
            raise ValueError(
                f"SDL entry '{entry.name}' maps canonical control '{canonical}' more than once "
                f"via '{existing_sdl_control}' and '{sdl_control}'"
            )
        existing_canonical = seen_raw.get(raw_identifier)
        if existing_canonical is not None:
            raise ValueError(
                f"SDL entry '{entry.name}' reuses raw binding '{raw_identifier}' for canonical controls "
                f"'{existing_canonical}' and '{canonical}'"
            )

        seen_canonical[canonical] = sdl_control
        seen_raw[raw_identifier] = canonical
        raw_to_canonical[raw_identifier] = canonical

    if not raw_to_canonical:
        raise ValueError(f"SDL entry '{entry.name}' does not contain any supported bindings")

    generated_profile_id = profile_id or _default_profile_id(entry.name)
    payload: dict[str, object] = {
        "schema_version": 1,
        "profile_type": "device_profile",
        "id": generated_profile_id,
        "source": "sdl_gamecontrollerdb",
        "device": {
            "kind": "gamecontroller",
            "name": entry.name,
            "guid": entry.guid,
        },
        "raw_to_canonical": raw_to_canonical,
        "metadata": {
            "created_by": "sdl_gamecontrollerdb_importer",
            "clean_room_safe": True,
        },
    }
    ensure_no_private_paths(payload)
    return payload, warnings


def write_device_profile_payload(payload: dict[str, object], output_path: Path) -> Path:
    ensure_public_output_path(output_path)
    ensure_no_private_paths(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return output_path


def _split_sdl_csv_fields(line: str) -> list[str]:
    fields: list[str] = []
    current: list[str] = []
    escaped = False

    for char in line:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == ",":
            fields.append("".join(current))
            current = []
            continue
        current.append(char)

    if escaped:
        current.append("\\")
    fields.append("".join(current))
    return fields


def _default_profile_id(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not normalized:
        return "sdl_controller"
    return f"{normalized}_sdl"

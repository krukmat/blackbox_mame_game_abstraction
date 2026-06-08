"""T20.5 / ADR-026 — RAM address-map loader and YAML→JSON exporter.

The operator authors a LOCAL, PRIVATE, uncommitted YAML address map sourced from a
community cheat database (never from ROM disassembly). The harness converts it to a
private JSON the MAME Lua bridge consumes (mirroring the input-plan YAML→JSON flow), so
no fragile YAML parser is needed in Lua.

Clean-room contract (ADR-026):
- Real addresses live only in the local YAML and the derived private JSON under
  evidence/private/; neither is committed.
- Only a placeholder `.example.yaml` is committed.
- This module emits the address map JSON for the Lua; it does not emit any public artifact.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

VALID_SIZES = {"u8", "u16"}
DEFAULT_CPU_TAG = ":maincpu"
DEFAULT_SPACE = "program"
_FIELD_NAMES = ("x", "y", "state_flags")


@dataclass(slots=True)
class MemoryField:
    addr: int
    size: str


@dataclass(slots=True)
class MemoryEntity:
    name: str
    fields: dict[str, MemoryField]


@dataclass(slots=True)
class MemoryMap:
    cpu_tag: str
    space: str
    entities: list[MemoryEntity]


def _parse_field(raw: object, ctx: str) -> MemoryField:
    if not isinstance(raw, dict) or "addr" not in raw:
        raise ValueError(f"{ctx}: field must be a mapping with 'addr'")
    addr = raw["addr"]
    if not isinstance(addr, int) or isinstance(addr, bool) or addr < 0:
        raise ValueError(f"{ctx}: addr must be a non-negative integer")
    size = str(raw.get("size", "u8"))
    if size not in VALID_SIZES:
        raise ValueError(f"{ctx}: size must be one of {sorted(VALID_SIZES)}")
    return MemoryField(addr=addr, size=size)


def parse_memory_map(data: object) -> MemoryMap:
    if not isinstance(data, dict):
        raise ValueError("memory map must be a mapping")
    raw_entities = data.get("entities")
    if not isinstance(raw_entities, list) or not raw_entities:
        raise ValueError("memory map must declare a non-empty 'entities' list")

    entities: list[MemoryEntity] = []
    for index, raw in enumerate(raw_entities):
        if not isinstance(raw, dict) or "name" not in raw:
            raise ValueError(f"entity {index} must be a mapping with 'name'")
        raw_fields = raw.get("fields")
        if not isinstance(raw_fields, dict) or not raw_fields:
            raise ValueError(f"entity '{raw['name']}' must declare a non-empty 'fields' mapping")
        fields: dict[str, MemoryField] = {}
        for fname, fraw in raw_fields.items():
            if fname not in _FIELD_NAMES:
                raise ValueError(
                    f"entity '{raw['name']}': unsupported field '{fname}' "
                    f"(allowed: {list(_FIELD_NAMES)})"
                )
            fields[fname] = _parse_field(fraw, f"entity '{raw['name']}' field '{fname}'")
        entities.append(MemoryEntity(name=str(raw["name"]), fields=fields))

    return MemoryMap(
        cpu_tag=str(data.get("cpu_tag", DEFAULT_CPU_TAG)),
        space=str(data.get("space", DEFAULT_SPACE)),
        entities=entities,
    )


def load_memory_map(path: Path) -> MemoryMap:
    return parse_memory_map(yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {})


def memory_map_to_json_payload(memory_map: MemoryMap) -> dict[str, Any]:
    return {
        "cpu_tag": memory_map.cpu_tag,
        "space": memory_map.space,
        "entities": [
            {
                "name": entity.name,
                "fields": {
                    fname: {"addr": field.addr, "size": field.size}
                    for fname, field in entity.fields.items()
                },
            }
            for entity in memory_map.entities
        ],
    }


def export_memory_map_json(yaml_path: Path, json_path: Path) -> Path:
    """Convert a local YAML address map to the private JSON the Lua bridge reads."""
    memory_map = load_memory_map(yaml_path)
    payload = memory_map_to_json_payload(memory_map)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload), encoding="utf-8")
    return json_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Convert a local YAML RAM address map to private JSON.")
    parser.add_argument("--yaml", required=True, type=Path)
    parser.add_argument("--json", required=True, type=Path)
    args = parser.parse_args()
    out = export_memory_map_json(args.yaml, args.json)
    # Count only — never echo addresses (ADR-026 clause 2 / ADR-003).
    mm = load_memory_map(args.yaml)
    print(f"memory_map: {len(mm.entities)} entities exported")
    _ = out


if __name__ == "__main__":
    main()

"""T30.3 / ADR-028 — Integration bundle loader and validator.

Loads the local private integration bundle YAML, validates it against
integration_bundle.schema.json, and exposes typed Python objects for
downstream use (T30.4 memory tap wiring, T30.5 calibration).

Clean-room contract (ADR-026 / ADR-028):
  - Real addresses live only in the local YAML (gitignored) and derived
    private JSON artifacts under evidence/private/.
  - This module never emits addresses or raw values to public output.
  - Public output stays numbers-only (abstract mechanics).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_SCHEMA_PATH = Path(__file__).parent.parent.parent / "packages" / "schemas" / "integration_bundle.schema.json"

VALID_TYPES = {"u8", "u16", "s8", "s16"}
VALID_ENCODINGS = {"binary", "bcd8", "bcd16"}
VALID_OPS = {"decreased_to_zero", "increased", "decreased", "equals", "not_equals", "changed"}


# ---------------------------------------------------------------------------
# Typed model
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Variable:
    name: str
    address: int
    type: str
    encoding: str = "binary"
    entity: str | None = None
    axis: str | None = None
    source: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class EventCondition:
    variable: str
    op: str
    value: int | None = None


@dataclass(slots=True)
class ScenarioEvent:
    name: str
    condition: EventCondition
    notes: str | None = None


@dataclass(slots=True)
class ScenarioEntity:
    name: str
    variables: list[str]
    active_flag_variable: str | None = None


@dataclass(slots=True)
class Scenario:
    entities: list[ScenarioEntity]
    events: list[ScenarioEvent]


@dataclass(slots=True)
class IntegrationBundle:
    schema_version: str
    game_id: str
    mame_driver: str
    rom_sha256: str
    cpu_tag: str
    address_space: str
    variables: list[Variable]
    scenario: Scenario
    savestate_path: str | None = None
    notes: str | None = None

    def variable_by_name(self, name: str) -> Variable | None:
        for v in self.variables:
            if v.name == name:
                return v
        return None

    def to_memory_map_payload(self) -> dict[str, Any]:
        """Emit the Lua-compatible memory map payload (private — no public output)."""
        return {
            "cpu_tag": self.cpu_tag,
            "space": self.address_space,
            "entities": [
                {
                    "name": entity.name,
                    "fields": {
                        axis: {"addr": v.address, "size": v.type}
                        for var_name in entity.variables
                        if (v := self.variable_by_name(var_name)) is not None
                        if (axis := v.axis or var_name) is not None
                    },
                }
                for entity in self.scenario.entities
            ],
        }


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_variable(raw: dict, index: int) -> Variable:
    name = raw.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"variable[{index}]: 'name' must be a non-empty string")
    addr = raw.get("address")
    if not isinstance(addr, int) or isinstance(addr, bool) or addr < 0 or addr > 0xFFFF:
        raise ValueError(f"variable '{name}': address must be integer 0–65535")
    type_ = raw.get("type", "u8")
    if type_ not in VALID_TYPES:
        raise ValueError(f"variable '{name}': type must be one of {sorted(VALID_TYPES)}")
    encoding = raw.get("encoding", "binary")
    if encoding not in VALID_ENCODINGS:
        raise ValueError(f"variable '{name}': encoding must be one of {sorted(VALID_ENCODINGS)}")
    return Variable(
        name=name,
        address=addr,
        type=type_,
        encoding=encoding,
        entity=raw.get("entity"),
        axis=raw.get("axis"),
        source=raw.get("source"),
        notes=raw.get("notes"),
    )


def _parse_scenario(raw: dict) -> Scenario:
    raw_entities = raw.get("entities", [])
    entities = []
    for re in raw_entities:
        entities.append(ScenarioEntity(
            name=str(re["name"]),
            variables=list(re.get("variables", [])),
            active_flag_variable=re.get("active_flag_variable"),
        ))
    raw_events = raw.get("events", [])
    events = []
    for rev in raw_events:
        cond_raw = rev["condition"]
        cond = EventCondition(
            variable=str(cond_raw["variable"]),
            op=str(cond_raw["op"]),
            value=cond_raw.get("value"),
        )
        if cond.op not in VALID_OPS:
            raise ValueError(f"event '{rev['name']}': op must be one of {sorted(VALID_OPS)}")
        events.append(ScenarioEvent(
            name=str(rev["name"]),
            condition=cond,
            notes=rev.get("notes"),
        ))
    return Scenario(entities=entities, events=events)


def parse_integration_bundle(data: dict) -> IntegrationBundle:
    required = ("schema_version", "game_id", "mame_driver", "rom_sha256", "cpu_tag", "address_space", "variables", "scenario")
    for key in required:
        if key not in data:
            raise ValueError(f"integration bundle missing required key: '{key}'")

    raw_vars = data["variables"]
    if not isinstance(raw_vars, list) or not raw_vars:
        raise ValueError("'variables' must be a non-empty list")
    variables = [_parse_variable(rv, i) for i, rv in enumerate(raw_vars)]

    # Validate no duplicate variable names.
    names = [v.name for v in variables]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        raise ValueError(f"duplicate variable names: {sorted(dupes)}")

    scenario = _parse_scenario(data["scenario"])

    # Validate scenario variable references resolve.
    var_name_set = {v.name for v in variables}
    for entity in scenario.entities:
        for vname in entity.variables:
            if vname not in var_name_set:
                raise ValueError(f"scenario entity '{entity.name}' references unknown variable '{vname}'")
    for event in scenario.events:
        if event.condition.variable not in var_name_set:
            raise ValueError(f"scenario event '{event.name}' references unknown variable '{event.condition.variable}'")

    return IntegrationBundle(
        schema_version=str(data["schema_version"]),
        game_id=str(data["game_id"]),
        mame_driver=str(data["mame_driver"]),
        rom_sha256=str(data["rom_sha256"]),
        cpu_tag=str(data["cpu_tag"]),
        address_space=str(data["address_space"]),
        variables=variables,
        scenario=scenario,
        savestate_path=data.get("savestate_path"),
        notes=data.get("notes"),
    )


def load_integration_bundle(path: Path) -> IntegrationBundle:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"integration bundle at {path} must be a YAML mapping")
    return parse_integration_bundle(raw)


def export_memory_map_json(bundle: IntegrationBundle, json_path: Path) -> Path:
    """Write the Lua-compatible memory map JSON to a private path."""
    payload = bundle.to_memory_map_payload()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload), encoding="utf-8")
    return json_path

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from guardrails import ensure_no_private_paths
from input_planner import VALID_ACTIONS


VALID_CANONICAL_CONTROLS = {
    "dpad_left",
    "dpad_right",
    "dpad_up",
    "dpad_down",
    "south",
    "east",
    "west",
    "north",
    "start",
    "select",
    "l1",
    "r1",
    "pause",
    "noop",
}
SUPPORTED_PROFILE_TYPES = {
    "device_profile",
    "controller_profile",
    "game_action_profile",
    "input_sequence",
}


@dataclass(frozen=True, slots=True)
class ProfileMetadata:
    clean_room_safe: bool
    created_by: str | None = None


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    kind: str
    name: str
    guid: str | None = None


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    schema_version: int
    profile_type: str
    id: str
    source: str
    device: DeviceInfo
    raw_to_canonical: dict[str, str]
    metadata: ProfileMetadata


@dataclass(frozen=True, slots=True)
class ControlConstraints:
    required: tuple[str, ...]
    optional: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ControllerProfile:
    schema_version: int
    profile_type: str
    id: str
    canonical_controls: tuple[str, ...]
    constraints: ControlConstraints
    metadata: ProfileMetadata


@dataclass(frozen=True, slots=True)
class GameActionProfile:
    schema_version: int
    profile_type: str
    id: str
    source_profile: str
    driver: str
    canonical_to_action: dict[str, str]
    allowed_actions: tuple[str, ...]
    metadata: ProfileMetadata


@dataclass(frozen=True, slots=True)
class InputSequenceStep:
    control: str
    frames: int
    notes: str = ""


@dataclass(frozen=True, slots=True)
class InputSequence:
    schema_version: int
    profile_type: str
    id: str
    steps: tuple[InputSequenceStep, ...]


MappingProfile = DeviceProfile | ControllerProfile | GameActionProfile | InputSequence


def load_mapping_profile(path: Path) -> MappingProfile:
    data = _load_yaml_mapping(path)
    _ensure_public_profile_payload_safe(data)
    profile_type = _detect_profile_type(data)

    if profile_type == "device_profile":
        return _load_device_profile(data)
    if profile_type == "controller_profile":
        return _load_controller_profile(data)
    if profile_type == "game_action_profile":
        return _load_game_action_profile(data)
    if profile_type == "input_sequence":
        return _load_input_sequence(data)

    raise AssertionError(f"unhandled profile_type: {profile_type}")


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"mapping profile must be a YAML object: {path}")
    return loaded


def _ensure_public_profile_payload_safe(payload: dict[str, Any]) -> None:
    ensure_no_private_paths(payload)
    for value in _iter_strings(payload):
        if "private://" in value:
            raise ValueError("mapping profiles must not contain private:// evidence handles")


def _iter_strings(payload: Any) -> list[str]:
    if isinstance(payload, dict):
        values: list[str] = []
        for value in payload.values():
            values.extend(_iter_strings(value))
        return values
    if isinstance(payload, list):
        values: list[str] = []
        for item in payload:
            values.extend(_iter_strings(item))
        return values
    if isinstance(payload, str):
        return [payload]
    return []


def _detect_profile_type(data: dict[str, Any]) -> str:
    profile_type = data.get("profile_type")
    sequence_type = data.get("sequence_type")

    if profile_type is None and sequence_type == "input_sequence":
        return "input_sequence"
    if not isinstance(profile_type, str):
        raise ValueError("mapping profile must declare profile_type")
    if profile_type not in SUPPORTED_PROFILE_TYPES:
        supported = ", ".join(sorted(SUPPORTED_PROFILE_TYPES))
        raise ValueError(f"unsupported profile_type: {profile_type}. Expected one of: {supported}")
    if profile_type == "input_sequence" and sequence_type not in (None, "input_sequence"):
        raise ValueError("input_sequence sequence_type must be 'input_sequence' when present")
    return profile_type


def _load_device_profile(data: dict[str, Any]) -> DeviceProfile:
    schema_version = _require_schema_version(data)
    profile_type = _require_string(data, "profile_type")
    profile_id = _require_string(data, "id")
    source = _require_string(data, "source")

    device = _require_mapping(data, "device")
    device_info = DeviceInfo(
        kind=_require_string(device, "kind"),
        name=_require_string(device, "name"),
        guid=_optional_string_or_none(device, "guid"),
    )

    raw_to_canonical = _require_string_mapping(data, "raw_to_canonical")
    _ensure_unique_values(raw_to_canonical, "raw_to_canonical")
    for canonical in raw_to_canonical.values():
        _validate_canonical_control(canonical, "raw_to_canonical")

    metadata = _load_metadata(_require_mapping(data, "metadata"))
    return DeviceProfile(
        schema_version=schema_version,
        profile_type=profile_type,
        id=profile_id,
        source=source,
        device=device_info,
        raw_to_canonical=raw_to_canonical,
        metadata=metadata,
    )


def _load_controller_profile(data: dict[str, Any]) -> ControllerProfile:
    schema_version = _require_schema_version(data)
    profile_type = _require_string(data, "profile_type")
    profile_id = _require_string(data, "id")

    canonical_controls = _require_string_list(data, "canonical_controls", min_items=1)
    _ensure_unique_list(canonical_controls, "canonical_controls")
    for control in canonical_controls:
        _validate_canonical_control(control, "canonical_controls")

    constraints_data = _require_mapping(data, "constraints")
    required_controls = _require_string_list(constraints_data, "required")
    optional_controls = _require_string_list(constraints_data, "optional")
    _ensure_unique_list(required_controls, "constraints.required")
    _ensure_unique_list(optional_controls, "constraints.optional")
    overlap = sorted(set(required_controls) & set(optional_controls))
    if overlap:
        joined = ", ".join(overlap)
        raise ValueError(f"constraints.required and constraints.optional overlap: {joined}")
    declared_controls = set(canonical_controls)
    for control in required_controls + optional_controls:
        _validate_canonical_control(control, "constraints")
        if control not in declared_controls:
            raise ValueError(f"constraint control '{control}' is not declared in canonical_controls")

    metadata = _load_metadata(_require_mapping(data, "metadata"))
    return ControllerProfile(
        schema_version=schema_version,
        profile_type=profile_type,
        id=profile_id,
        canonical_controls=tuple(canonical_controls),
        constraints=ControlConstraints(
            required=tuple(required_controls),
            optional=tuple(optional_controls),
        ),
        metadata=metadata,
    )


def _load_game_action_profile(data: dict[str, Any]) -> GameActionProfile:
    schema_version = _require_schema_version(data)
    profile_type = _require_string(data, "profile_type")
    profile_id = _require_string(data, "id")
    source_profile = _require_string(data, "source_profile")
    driver = _require_string(data, "driver")

    canonical_to_action = _require_string_mapping(data, "canonical_to_action")
    for control, action in canonical_to_action.items():
        _validate_canonical_control(control, "canonical_to_action")
        _validate_action(action, "canonical_to_action")

    allowed_actions = _require_string_list(data, "allowed_actions", min_items=1)
    _ensure_unique_list(allowed_actions, "allowed_actions")
    for action in allowed_actions:
        _validate_action(action, "allowed_actions")
    undeclared_actions = sorted(set(canonical_to_action.values()) - set(allowed_actions))
    if undeclared_actions:
        joined = ", ".join(undeclared_actions)
        raise ValueError(f"canonical_to_action uses actions not declared in allowed_actions: {joined}")

    metadata = _load_metadata(_require_mapping(data, "metadata"))
    return GameActionProfile(
        schema_version=schema_version,
        profile_type=profile_type,
        id=profile_id,
        source_profile=source_profile,
        driver=driver,
        canonical_to_action=canonical_to_action,
        allowed_actions=tuple(allowed_actions),
        metadata=metadata,
    )


def _load_input_sequence(data: dict[str, Any]) -> InputSequence:
    schema_version = _require_schema_version(data)
    profile_type = "input_sequence"
    profile_id = _require_string(data, "id")

    steps_data = data.get("steps")
    if not isinstance(steps_data, list) or not steps_data:
        raise ValueError("input_sequence must declare a non-empty steps list")

    steps: list[InputSequenceStep] = []
    for index, raw_step in enumerate(steps_data):
        if not isinstance(raw_step, dict):
            raise ValueError(f"input_sequence step {index} must be an object")
        control = _require_string(raw_step, "control", context=f"input_sequence step {index}")
        _validate_canonical_control(control, f"input_sequence step {index}")
        frames = _require_int(raw_step, "frames", context=f"input_sequence step {index}")
        if frames < 1:
            raise ValueError(f"input_sequence step {index} frames must be >= 1")
        steps.append(
            InputSequenceStep(
                control=control,
                frames=frames,
                notes=str(raw_step.get("notes", "")),
            )
        )

    return InputSequence(
        schema_version=schema_version,
        profile_type=profile_type,
        id=profile_id,
        steps=tuple(steps),
    )


def _load_metadata(data: dict[str, Any]) -> ProfileMetadata:
    clean_room_safe = data.get("clean_room_safe")
    if not isinstance(clean_room_safe, bool):
        raise ValueError("metadata.clean_room_safe must be a boolean")
    created_by = _optional_string_or_none(data, "created_by")
    return ProfileMetadata(clean_room_safe=clean_room_safe, created_by=created_by)


def _require_schema_version(data: dict[str, Any]) -> int:
    version = data.get("schema_version")
    if not isinstance(version, int):
        raise ValueError("schema_version must be an integer")
    if version != 1:
        raise ValueError(f"unsupported schema_version: {version}. Expected 1")
    return version


def _require_mapping(data: dict[str, Any], field: str) -> dict[str, Any]:
    value = data.get(field)
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _require_string_mapping(data: dict[str, Any], field: str) -> dict[str, str]:
    value = data.get(field)
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{field} must be a non-empty object")
    normalized: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"{field} keys must be non-empty strings")
        if not isinstance(item, str) or not item:
            raise ValueError(f"{field} values must be non-empty strings")
        normalized[key] = item
    return normalized


def _require_string_list(data: dict[str, Any], field: str, *, min_items: int = 0) -> list[str]:
    value = data.get(field)
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if len(value) < min_items:
        raise ValueError(f"{field} must contain at least {min_items} item(s)")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError(f"{field} entries must be non-empty strings")
        normalized.append(item)
    return normalized


def _require_string(data: dict[str, Any], field: str, *, context: str | None = None) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        prefix = f"{context} " if context else ""
        raise ValueError(f"{prefix}{field} must be a non-empty string")
    return value


def _optional_string_or_none(data: dict[str, Any], field: str) -> str | None:
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string or null")
    return value


def _require_int(data: dict[str, Any], field: str, *, context: str | None = None) -> int:
    value = data.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        prefix = f"{context} " if context else ""
        raise ValueError(f"{prefix}{field} must be an integer")
    return value


def _validate_canonical_control(control: str, context: str) -> None:
    if control not in VALID_CANONICAL_CONTROLS:
        allowed = ", ".join(sorted(VALID_CANONICAL_CONTROLS))
        raise ValueError(f"{context} contains unsupported canonical control '{control}'. Allowed: {allowed}")


def _validate_action(action: str, context: str) -> None:
    if action not in VALID_ACTIONS:
        allowed = ", ".join(sorted(VALID_ACTIONS))
        raise ValueError(f"{context} contains unsupported action '{action}'. Allowed: {allowed}")


def _ensure_unique_list(values: list[str], context: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        raise ValueError(f"{context} contains duplicate entries: {joined}")


def _ensure_unique_values(values: dict[str, str], context: str) -> None:
    reverse: dict[str, str] = {}
    for raw_input, canonical in values.items():
        previous = reverse.get(canonical)
        if previous is not None:
            raise ValueError(
                f"{context} assigns canonical control '{canonical}' more than once: {previous}, {raw_input}"
            )
        reverse[canonical] = raw_input

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from mapping_profiles import ControllerProfile, DeviceProfile, load_mapping_profile
from sdl_gamecontrollerdb_importer import write_device_profile_payload


HARNESS_DIR = Path(__file__).resolve().parent
ROOT = HARNESS_DIR.parents[1]
DEFAULT_DEVICE_PRESET = "none"
DEFAULT_CONTROLLER_PRESET = "arcade_2button"
DEVICE_PRESET_PATHS = {
    "keyboard_default": ROOT / "profiles" / "devices" / "keyboard_default.yaml",
}
CONTROLLER_PRESET_PATHS = {
    "arcade_2button": ROOT / "profiles" / "controllers" / "arcade_2button.yaml",
}
DEVICE_KIND_CHOICES = {
    "keyboard": "keyboard",
    "controller": "gamecontroller",
    "arcade stick": "arcade_stick",
    "arcade_stick": "arcade_stick",
    "manual": "manual",
}


@dataclass(frozen=True, slots=True)
class MapInitWizardResult:
    output_path: Path
    profile: DeviceProfile
    next_validate_command: str
    next_compile_command: str


def run_map_init_wizard(
    *,
    input_stream: TextIO,
    output_stream: TextIO,
    output_path: Path | None = None,
    controller_preset: str | None = None,
    device_preset: str | None = None,
) -> MapInitWizardResult:
    chosen_device_type = _prompt_choice(
        input_stream=input_stream,
        output_stream=output_stream,
        prompt="Device type [keyboard/controller/arcade stick/manual]: ",
        choices=("keyboard", "controller", "arcade stick", "manual"),
        default="keyboard",
    )
    chosen_device_preset = device_preset or _prompt_choice(
        input_stream=input_stream,
        output_stream=output_stream,
        prompt="Device preset [none/keyboard_default]: ",
        choices=("none", "keyboard_default"),
        default=DEFAULT_DEVICE_PRESET,
    )
    if chosen_device_preset == "keyboard_default" and DEVICE_KIND_CHOICES[chosen_device_type] != "keyboard":
        raise ValueError("device preset 'keyboard_default' is only valid for device type 'keyboard'")

    chosen_controller_preset = controller_preset or _prompt_choice(
        input_stream=input_stream,
        output_stream=output_stream,
        prompt="Controller preset [arcade_2button]: ",
        choices=("arcade_2button",),
        default=DEFAULT_CONTROLLER_PRESET,
    )
    controller_profile = _load_controller_preset(chosen_controller_preset)
    preset_profile = _load_device_preset(chosen_device_preset)

    profile_id = _prompt_non_empty(
        input_stream=input_stream,
        output_stream=output_stream,
        prompt="Profile id: ",
    )
    device_name = _prompt_non_empty(
        input_stream=input_stream,
        output_stream=output_stream,
        prompt="Device name: ",
    )
    device_guid = _prompt_optional(
        input_stream=input_stream,
        output_stream=output_stream,
        prompt="Device guid (optional): ",
    )
    chosen_output_path = output_path or Path(
        _prompt_non_empty(
            input_stream=input_stream,
            output_stream=output_stream,
            prompt="Output path: ",
        )
    )

    raw_to_canonical = _collect_bindings(
        input_stream=input_stream,
        output_stream=output_stream,
        controller_profile=controller_profile,
        preset_profile=preset_profile,
    )
    payload = {
        "schema_version": 1,
        "profile_type": "device_profile",
        "id": profile_id,
        "source": "map_init_wizard",
        "device": {
            "kind": DEVICE_KIND_CHOICES[chosen_device_type],
            "name": device_name,
            "guid": device_guid or None,
        },
        "raw_to_canonical": raw_to_canonical,
        "metadata": {
            "created_by": "map_init_wizard",
            "clean_room_safe": True,
        },
    }
    write_device_profile_payload(payload, chosen_output_path)
    loaded = load_mapping_profile(chosen_output_path)
    if not isinstance(loaded, DeviceProfile):
        raise ValueError("wizard output did not round-trip as a DeviceProfile")

    next_validate = (
        "apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map validate "
        f"--profile {chosen_output_path}"
    )
    next_compile = (
        "apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map compile "
        f"--device {chosen_output_path} "
        f"--controller {CONTROLLER_PRESET_PATHS[chosen_controller_preset]} "
        "--game profiles/games/gngb/default_actions.yaml "
        "--sequence plans/sequences/gng_smoke_sequence.yaml "
        f"--out plans/generated/{profile_id}_compiled.yaml"
    )

    output_stream.write("\nProfile written.\n")
    output_stream.write(f"Validate next: {next_validate}\n")
    output_stream.write(f"Compile next: {next_compile}\n")
    return MapInitWizardResult(
        output_path=chosen_output_path,
        profile=loaded,
        next_validate_command=next_validate,
        next_compile_command=next_compile,
    )


def _collect_bindings(
    *,
    input_stream: TextIO,
    output_stream: TextIO,
    controller_profile: ControllerProfile,
    preset_profile: DeviceProfile | None,
) -> dict[str, str]:
    preset_defaults = _invert_preset_bindings(preset_profile)
    raw_to_canonical: dict[str, str] = {}
    assigned_raw_to_control: dict[str, str] = {}

    for control in controller_profile.constraints.required:
        raw_binding = _prompt_binding(
            input_stream=input_stream,
            output_stream=output_stream,
            control=control,
            required=True,
            default=preset_defaults.get(control),
        )
        _record_binding(
            raw_to_canonical=raw_to_canonical,
            assigned_raw_to_control=assigned_raw_to_control,
            raw_binding=raw_binding,
            control=control,
            output_stream=output_stream,
            input_stream=input_stream,
        )

    for control in controller_profile.constraints.optional:
        if control == "noop":
            continue
        raw_binding = _prompt_binding(
            input_stream=input_stream,
            output_stream=output_stream,
            control=control,
            required=False,
            default=preset_defaults.get(control),
        )
        if raw_binding == "":
            continue
        _record_binding(
            raw_to_canonical=raw_to_canonical,
            assigned_raw_to_control=assigned_raw_to_control,
            raw_binding=raw_binding,
            control=control,
            output_stream=output_stream,
            input_stream=input_stream,
        )

    return raw_to_canonical


def _record_binding(
    *,
    raw_to_canonical: dict[str, str],
    assigned_raw_to_control: dict[str, str],
    raw_binding: str,
    control: str,
    output_stream: TextIO,
    input_stream: TextIO,
) -> None:
    while True:
        existing = assigned_raw_to_control.get(raw_binding)
        if existing is None:
            assigned_raw_to_control[raw_binding] = control
            raw_to_canonical[raw_binding] = control
            return
        output_stream.write(
            f"duplicate raw binding '{raw_binding}' already assigned to '{existing}'. Enter a different binding for {control}: "
        )
        output_stream.flush()
        retry = input_stream.readline()
        if retry == "":
            raise ValueError("map init wizard input ended unexpectedly")
        raw_binding = retry.rstrip("\n").strip()
        if raw_binding == "":
            raise ValueError(f"duplicate raw binding '{existing}' for control '{control}' was not resolved")


def _prompt_binding(
    *,
    input_stream: TextIO,
    output_stream: TextIO,
    control: str,
    required: bool,
    default: str | None,
) -> str:
    while True:
        suffix = "required" if required else "optional; blank to skip"
        if default:
            prompt = f"Bind {control} [{suffix}] (default {default}): "
        else:
            prompt = f"Bind {control} [{suffix}]: "
        answer = _read_line(input_stream=input_stream, output_stream=output_stream, prompt=prompt)
        normalized = answer.strip()
        if normalized == "" and default is not None:
            return default
        if normalized == "":
            if required:
                output_stream.write(f"{control} is required.\n")
                continue
            return ""
        return normalized


def _prompt_choice(
    *,
    input_stream: TextIO,
    output_stream: TextIO,
    prompt: str,
    choices: tuple[str, ...],
    default: str,
) -> str:
    valid = {choice.lower(): choice for choice in choices}
    while True:
        answer = _read_line(input_stream=input_stream, output_stream=output_stream, prompt=prompt).strip().lower()
        if answer == "":
            return default
        if answer in valid:
            return valid[answer]
        output_stream.write(f"Expected one of: {', '.join(choices)}\n")


def _prompt_non_empty(
    *,
    input_stream: TextIO,
    output_stream: TextIO,
    prompt: str,
) -> str:
    while True:
        answer = _read_line(input_stream=input_stream, output_stream=output_stream, prompt=prompt).strip()
        if answer:
            return answer
        output_stream.write("Value is required.\n")


def _prompt_optional(
    *,
    input_stream: TextIO,
    output_stream: TextIO,
    prompt: str,
) -> str:
    return _read_line(input_stream=input_stream, output_stream=output_stream, prompt=prompt).strip()


def _read_line(
    *,
    input_stream: TextIO,
    output_stream: TextIO,
    prompt: str,
) -> str:
    output_stream.write(prompt)
    output_stream.flush()
    line = input_stream.readline()
    if line == "":
        raise ValueError("map init wizard input ended unexpectedly")
    return line.rstrip("\n")


def _invert_preset_bindings(profile: DeviceProfile | None) -> dict[str, str]:
    if profile is None:
        return {}
    return {canonical: raw for raw, canonical in profile.raw_to_canonical.items()}


def _load_device_preset(name: str) -> DeviceProfile | None:
    if name == "none":
        return None
    loaded = load_mapping_profile(DEVICE_PRESET_PATHS[name])
    if not isinstance(loaded, DeviceProfile):
        raise ValueError(f"device preset '{name}' did not load as DeviceProfile")
    return loaded


def _load_controller_preset(name: str) -> ControllerProfile:
    loaded = load_mapping_profile(CONTROLLER_PRESET_PATHS[name])
    if not isinstance(loaded, ControllerProfile):
        raise ValueError(f"controller preset '{name}' did not load as ControllerProfile")
    return loaded

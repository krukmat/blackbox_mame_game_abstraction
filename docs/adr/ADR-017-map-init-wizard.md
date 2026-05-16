# ADR-017 — Prompt-Based `map init` Wizard

## Status
Accepted

## Date
2026-05-16

## Context

ADR-014 established the layered mapping model. ADR-015 and ADR-016 added SDL and RetroArch importers so existing controller configs can be normalized into `device_profile` YAML.

There is still one bootstrap gap: a contributor with no reusable external config still has to hand-author YAML to create a valid `device_profile`. That is unnecessary friction now that the device-profile contract is stable.

The repository needs a first interactive flow for creating `device_profile` files, but it must not:

- add a new profile type
- depend on platform-specific real-time input capture
- introduce private evidence handling or MAME execution
- bypass the existing loader validation and public-output guardrails

## Decision

Add a minimal prompt-based `map init` wizard that guides a user through creating a valid `device_profile`.

### Interaction Model

The first version is a line-oriented CLI prompt flow, not a GUI or TUI framework.

It asks for:

- device type
- optional device preset
- controller preset
- profile id
- device display name
- optional GUID
- output path
- raw bindings for required and optional canonical controls

### Preset Policy

The first version exposes:

- `keyboard_default` as an optional device-binding preset
- `arcade_2button` as the default controller-shape preset

Presets only prefill or constrain wizard input. The output is still a standard `device_profile`.

### Validation Policy

The wizard must:

- enforce all required controls from the selected controller profile
- allow optional controls to be skipped
- reject duplicate raw bindings
- write only to public-safe output paths
- validate the generated YAML through the existing `load_mapping_profile()` path after writing

### Output Policy

The wizard writes a normal `device_profile` with:

- `source: map_init_wizard`
- `metadata.clean_room_safe: true`
- optional `metadata.created_by: map_init_wizard`

It also prints the next validation command and a compile example command.

## Consequences

**Positive**

- Contributors can create valid `device_profile` YAML without hand-authoring files.
- The wizard stays inside the existing profile model and validation boundary.
- Duplicate raw bindings and missing required controls are caught at input time.

**Negative**

- The first version is text-prompt only and requires manual entry of raw binding identifiers.
- Preset coverage is minimal.
- The compile example still needs the caller to choose a game action profile and sequence.

## Alternatives Considered

**Real-time input capture wizard**

Rejected for the first version because OS-level input capture would add substantial complexity and platform coupling.

**GUI or TUI framework**

Rejected because the immediate need is a simple deterministic bootstrap flow, not a richer interface stack.

**Keep importers only**

Rejected because importers do not help users who do not already have SDL or RetroArch controller configs.

## Related

- [ADR-003](./ADR-003-public-output-blocklist.md)
- [ADR-014](./ADR-014-layered-input-mapping.md)
- [ADR-015](./ADR-015-sdl-gamecontrollerdb-importer.md)
- [ADR-016](./ADR-016-retroarch-autoconfig-importer.md)
- [docs/plans/layered_input_mapping_plan.md](../plans/layered_input_mapping_plan.md)
- `apps/mame-harness/cli.py`
- `apps/mame-harness/mapping_profiles.py`


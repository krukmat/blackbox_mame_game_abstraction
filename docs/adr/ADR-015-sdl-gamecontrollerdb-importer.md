# ADR-015 — SDL GameControllerDB Importer to Device Profiles

## Status
Accepted

## Date
2026-05-16

## Context

ADR-014 established the layered input mapping model and the `device_profile` contract as the public hardware-facing layer. That contract now exists, is tested, and compiles through the existing deterministic input-plan pipeline.

The next friction point is first-use controller setup. Contributors with an existing SDL-compatible controller often already have mappings in SDL GameControllerDB format, but the repository currently requires hand-authoring `device_profile` YAML. That duplicates work and makes controller onboarding slower than necessary.

This importer must preserve the existing clean-room and compatibility constraints:

- imported output is still a public `device_profile`
- imported output must pass the same path/payload guardrails as hand-authored profiles
- the importer must not introduce a new execution path or bypass the existing loader validation
- unsupported SDL controls must not silently become canonical controls the repo does not understand

## Decision

Add an SDL GameControllerDB importer that converts a selected SDL controller entry into the repository's `device_profile` YAML format.

### Input Surface

The importer reads SDL GameControllerDB text entries from a public text file and selects one entry by exact GUID, exact controller name, or the only entry in the file.

The first implementation supports a file-based CLI flow:

```text
map import-sdl --db <file> --out <yaml> [--guid <guid>] [--name <name>] [--profile-id <id>]
```

### Output Surface

The importer writes a standard `device_profile`:

- `profile_type: device_profile`
- `source: sdl_gamecontrollerdb`
- `device.kind: gamecontroller`
- `device.name` and `device.guid` from the selected SDL entry
- `raw_to_canonical` generated from supported SDL bindings only
- `metadata.clean_room_safe: true`

The written YAML must then be validated by the existing `load_mapping_profile()` path.

### Canonical Mapping Policy

The first importer maps only the SDL control names that fit the existing canonical controller vocabulary:

- `dpup` -> `dpad_up`
- `dpdown` -> `dpad_down`
- `dpleft` -> `dpad_left`
- `dpright` -> `dpad_right`
- `a` -> `south`
- `b` -> `east`
- `x` -> `west`
- `y` -> `north`
- `back` -> `select`
- `start` -> `start`
- `leftshoulder` -> `l1`
- `rightshoulder` -> `r1`
- `guide` -> `pause`

Unsupported SDL controls are ignored with explicit warnings returned by the importer and CLI result. They are not silently remapped.

### Validation Policy

The importer fails explicitly when:

- the SDL file contains no selectable entries
- selectors are ambiguous or match nothing
- a supported SDL control appears more than once for the same canonical control
- two supported SDL controls resolve to the same raw physical binding
- the output path is not allowed for public artifacts
- the generated YAML fails existing `device_profile` validation

## Consequences

**Positive**

- Contributors can bootstrap controller profiles from a common existing format instead of authoring YAML manually.
- The importer reuses the existing `device_profile` contract rather than introducing a parallel profile type.
- Unsupported SDL controls remain visible through warnings instead of being dropped silently.
- Clean-room guarantees remain enforced by the same public-output guardrails and loader validation path.

**Negative**

- The first importer supports only the subset of SDL controls that map cleanly to the current canonical vocabulary.
- Some SDL entries with extra analog, trigger, stick-click, or vendor-specific controls will import partially and report warnings.
- Name and GUID matching are exact in the first implementation; no fuzzy search or interactive picker is provided.

## Alternatives Considered

**Import SDL directly into controller or game-action profiles**

Rejected because SDL GameControllerDB describes physical controller layout, not game semantics. `device_profile` is the correct layer.

**Fail on any unsupported SDL control**

Rejected because many valid SDL mappings include extra controls irrelevant to the current canonical vocabulary. A warning-based partial import is more practical while still remaining explicit.

**Store the original SDL line verbatim in the profile**

Rejected because it adds opaque format baggage to the public profile and duplicates the stable normalized representation the repo already adopted in ADR-014.

## Related

- [ADR-003](./ADR-003-public-output-blocklist.md)
- [ADR-009](./ADR-009-input-plan-determinism.md)
- [ADR-014](./ADR-014-layered-input-mapping.md)
- [docs/plans/layered_input_mapping_plan.md](../plans/layered_input_mapping_plan.md)
- `apps/mame-harness/mapping_profiles.py`
- `apps/mame-harness/cli.py`


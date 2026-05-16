# ADR-015 — SDL GameControllerDB Importer

tags: #adr #input #mapping #sdl #controller

Source: `docs/adr/ADR-015-sdl-gamecontrollerdb-importer.md`
Plan: `docs/plans/layered_input_mapping_plan.md`

## Decision

Add `map import-sdl` to convert an SDL GameControllerDB entry into the existing public `device_profile` format.

```text
SDL GameControllerDB entry
  -> selected controller entry
  -> canonical control subset
  -> device_profile YAML
  -> existing mapping loader / compiler path
```

## Why

After ADR-014, the stable public hardware layer already exists as `device_profile`. The remaining friction is manual YAML authoring for controllers that already have SDL mappings.

The importer reduces setup work without changing the execution boundary or introducing a new profile type.

## Rules

- Output stays a normal `device_profile`.
- Public-output guardrails still apply.
- Existing `load_mapping_profile()` remains the validator.
- Unsupported SDL controls are ignored with explicit warnings.
- Duplicate canonical bindings or duplicate raw physical bindings fail.

## Supported SDL Controls

- `dpup`, `dpdown`, `dpleft`, `dpright`
- `a`, `b`, `x`, `y`
- `back`, `start`
- `leftshoulder`, `rightshoulder`
- `guide`

These map to the existing canonical vocabulary only. No new canonical controls are introduced by this importer.

## Deferred

- fuzzy entry search
- interactive selection
- broader analog/trigger/stick-click support
- RetroArch importer

## Related

- [[ADR-003 Public Output Blocklist]]
- [[ADR-009 Input Plan Determinism]]
- [[ADR-014 Layered Input Mapping]]
- [[Input Plan]]


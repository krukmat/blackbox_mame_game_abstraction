# ADR-016 — RetroArch Autoconfig Importer

tags: #adr #input #mapping #retroarch #controller

Source: `docs/adr/ADR-016-retroarch-autoconfig-importer.md`
Plan: `docs/plans/layered_input_mapping_plan.md`

## Decision

Add `map import-retroarch` to convert a RetroArch autoconfig `.cfg` file into the existing public `device_profile` format.

```text
RetroArch autoconfig
  -> supported input fields
  -> canonical control subset
  -> device_profile YAML
  -> existing mapping loader / compiler path
```

## A/B Convention

The importer uses one fixed convention and does not guess:

- `input_b_btn` -> `south`
- `input_a_btn` -> `east`

This matches the typical RetroPad/Nintendo-style face-button naming orientation.

## Rules

- Output stays a normal `device_profile`.
- Existing public-output guardrails still apply.
- Existing `load_mapping_profile()` remains the validator.
- Unsupported fields are ignored with explicit warnings.
- Duplicate canonical mappings or duplicate raw bindings fail.

## Supported Fields

- `input_up_btn`, `input_up_axis`
- `input_down_btn`, `input_down_axis`
- `input_left_btn`, `input_left_axis`
- `input_right_btn`, `input_right_axis`
- `input_a_btn`, `input_b_btn`, `input_x_btn`, `input_y_btn`
- `input_select_btn`, `input_start_btn`
- `input_l_btn`, `input_r_btn`

## Deferred

- broader trigger/stick/hotkey coverage
- RetroArch execution backend
- wizard integration

## Related

- [[ADR-003 Public Output Blocklist]]
- [[ADR-014 Layered Input Mapping]]
- [[ADR-015 SDL GameControllerDB Importer]]


# GNG-MAP-02 - Author GNG Layered Runtime Artifacts

## Status

✅ Done — 2026-05-17

## Objective

Make the layered GNG artifacts the public source of truth for boot and gameplay sequencing.

## Scope

- add or revise GNG `input_sequence` files for:
  - boot-only runtime behavior
  - automated gameplay capture behavior
- keep `profiles/games/gngb/default_actions.yaml` aligned with those sequences
- define stable output targets under `plans/generated/` for:
  - boot-only runtime plan
  - gameplay runtime plan
- preserve the current calibrated boot timings in the new sequence source until ADR-018 implementation supersedes them

## Out Of Scope

- repointing scripts or docs to the new generated plan paths
- changing the controller-profile abstraction
- changing the compiler contract
- production boot-calibration implementation

## Dependencies

- [GNG-MAP-01](./GNG-MAP-01-legacy-gng-plan-decomposition.md)

## Reasoning Grade

`High`

## Effort Grade

`Medium`

## Recommended Model

`GPT-5.5`

## Acceptance Criteria

- GNG boot and gameplay are expressed as layered public artifacts rather than authored semantic runtime plans
- the sequences use only controls/actions supported by the current layered compiler and `input_planner`
- generated-plan target paths are named and stable
- no public artifact contains ROM paths, evidence references, frame paths, or absolute machine paths

## Implemented Artifacts

### Canonical source-of-truth sequences

- `plans/sequences/gng_boot_only.yaml`
- `plans/sequences/gng_gameplay.yaml`

These files now express the GNG runtime intent through canonical controls instead of direct semantic actions.

### Stable generated runtime targets

- `plans/generated/gng_boot_only.yaml`
- `plans/generated/gng_gameplay.yaml`

These generated plans preserve the existing runtime-facing names while moving the editable source of truth into the layered model.

## Decisions Carried Forward From GNG-MAP-01

- preserved boot timing sequence exactly:
  - `noop x 950`
  - `select x 10`
  - `noop x 60`
  - `start x 5`
  - `noop x 480`
- preserved the manual takeover seam in boot-only:
  - `noop x 9999`
- preserved gameplay observation ordering and durations from the legacy authored plan
- kept `profiles/games/gngb/default_actions.yaml` unchanged because the existing canonical mappings already cover all required GNG runtime actions

## Canonical Control Translation Applied

| Canonical control | Semantic action |
|---|---|
| `select` | `insert_coin` |
| `start` | `press_start` |
| `dpad_right` | `move_right` |
| `south` | `jump` |
| `east` | `fire` |
| `noop` | `noop` |

## Verification

- `map validate` succeeds for:
  - `plans/sequences/gng_boot_only.yaml`
  - `plans/sequences/gng_gameplay.yaml`
- `map compile` succeeds for:
  - `plans/generated/gng_boot_only.yaml`
  - `plans/generated/gng_gameplay.yaml`
- automated tests confirm:
  - the new runtime sequences compile to the same action/frame/notes steps as `plans/gng_boot_only.yaml` and `plans/gng_gameplay.yaml`
  - the checked-in generated plans match the legacy behavioral contract

## Notes For GNG-MAP-03

- parity verification can now treat the layered source files and generated outputs as established artifacts
- the compile stack currently still depends on `profiles/devices/keyboard_default.yaml` as a validation input because the compiler requires a concrete `device_profile`
- operational surfaces are intentionally unchanged here:
  - `.env.example`
  - `blackbox.local.example.yaml`
  - helper scripts
  - bootstrap docs

## Reference Documents

- [This Task File](./GNG-MAP-02-author-gng-layered-runtime-artifacts.md)
- [Parent Plan](../../plans/gng_layered_mapping_adoption_plan.md)
- [Layered Input Mapping Plan](../../plans/layered_input_mapping_plan.md)
- [README.md](../../../README.md)
- [AGENTS.md](../../../AGENTS.md)
- [CLAUDE.md](../../../CLAUDE.md)
- [ADR-005](../../adr/ADR-005-source-profile-pattern.md)
- [ADR-009](../../adr/ADR-009-input-plan-determinism.md)
- [ADR-014](../../adr/ADR-014-layered-input-mapping.md)
- [ADR-018](../../adr/ADR-018-boot-calibration-public-contract.md)
- [Input Plan](../../obsidian/Input%20Plan.md)
- [Source Profile](../../obsidian/Source%20Profile.md)
- [Layered Input Mapping](../../mapping.md)
- [Bootstrap Setup](../../bootstrap.md)

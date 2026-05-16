# GNG-MAP-05 - Regression Closure And Boot-Calibration Seam

## Status

✅ Done — 2026-05-17

## Objective

Close the GNG mapping migration with regression coverage and a documented handoff point to the ADR-018 boot-calibration contract.

## Scope

- add or update regression tests for generated GNG plan integrity and path safety
- verify that one clear GNG mapping path is documented across planning and bootstrap docs
- document how future `boot_calibration.yaml` output will replace or regenerate the GNG boot sequence without reintroducing authored-plan drift
- identify any remaining technical debt from the adoption

## Out Of Scope

- implementing production boot calibration
- adding a new calibration artifact schema if none is already approved
- changing the public/private boundary

## Dependencies

- [GNG-MAP-04](./GNG-MAP-04-operational-surface-adoption.md)

## Reasoning Grade

`High`

## Effort Grade

`Medium`

## Recommended Model

`GPT-5.5`

## Acceptance Criteria

- tests cover the adopted generated GNG plans and their public-safe paths
- the repo no longer documents two competing GNG mapping paradigms as if both were canonical
- the future calibration replacement path is explicit, bounded by ADR-018, and does not require a second GNG-specific mapping model

## Regression Coverage Added

`apps/mame-harness/tests/test_mapping_compiler.py` now covers the adopted checked-in GNG generated plans directly.

Added regression assertions:

- `plans/generated/gng_boot_only.yaml` is an allowed public output path
- `plans/generated/gng_gameplay.yaml` is an allowed public output path
- both generated-plan payloads pass `ensure_no_private_paths(...)`
- both generated plans continue to match the accepted legacy behavioral contract

These checks sit alongside the existing parity tests so path-safety regressions and behavioral regressions fail independently.

## Canonical GNG Mapping Path

The repo now documents one operationally canonical GNG mapping path:

```text
profiles/games/gngb/default_actions.yaml
  -> plans/sequences/gng_boot_only.yaml or plans/sequences/gng_gameplay.yaml
  -> plans/generated/gng_boot_only.yaml or plans/generated/gng_gameplay.yaml
  -> input_planner.py
  -> private per-frame JSON
  -> scripts/mame_autoboot.lua
  -> MAME
```

Documented meaning:

- `plans/sequences/...` = editable layered source of truth
- `plans/generated/...` = runtime-facing public plans

This contract is now stated in:

- `docs/mapping.md`
- `docs/bootstrap.md`
- `README.md`
- `CLAUDE.md`
- `apps/mame-harness/source_profiles.py`

Historical task files and migration notes may still mention `plans/gng_boot_only.yaml` and `plans/gng_gameplay.yaml`, but they are no longer described as canonical runtime surfaces.

## Boot-Calibration Seam

The future calibration seam is now explicit and remains bounded by ADR-018:

- current boot timing still lives as fixed waits in the layered GNG sequence/generation path
- a future public `profiles/games/gngb/boot_calibration.yaml` may become the timing source
- that artifact would regenerate or replace the boot-specific fixed waits in the same `sequence -> generated plan -> planner -> Lua -> MAME` boundary
- calibration must not introduce screenshots, frame paths, crop paths, pixel-comparison reports, or a second GNG-specific runtime model

This seam is now documented consistently in:

- `docs/boot_calibration_spike.md`
- `docs/tasks/layered_input_mapping/MAP-11-boot-calibration-spike.md`
- `docs/mapping.md`
- [ADR-018](../../adr/ADR-018-boot-calibration-public-contract.md)

## Remaining Technical Debt

The migration is complete, but these follow-ups remain intentionally open:

- the compiler still requires a concrete `device_profile` even for committed GNG runtime-plan generation
- legacy authored semantic plans remain in the repo as migration-reference artifacts
- generated runtime plans are committed artifacts; automatic regeneration policy is not yet formalized
- production `boot_calibration.yaml` generation is still unimplemented and remains future work under ADR-018

## Verification

- targeted tests passed:
  - `apps/mame-harness/tests/test_mapping_compiler.py`
  - `apps/mame-harness/tests/test_source_profiles.py`
- result:
  - `16 passed`

## Reference Documents

- [This Task File](./GNG-MAP-05-regression-closure-and-boot-calibration-seam.md)
- [Parent Plan](../../plans/gng_layered_mapping_adoption_plan.md)
- [Layered Input Mapping Plan](../../plans/layered_input_mapping_plan.md)
- [README.md](../../../README.md)
- [AGENTS.md](../../../AGENTS.md)
- [CLAUDE.md](../../../CLAUDE.md)
- [ADR-009](../../adr/ADR-009-input-plan-determinism.md)
- [ADR-014](../../adr/ADR-014-layered-input-mapping.md)
- [ADR-018](../../adr/ADR-018-boot-calibration-public-contract.md)
- [Input Plan](../../obsidian/Input%20Plan.md)
- [GNG Integration Plan](../../obsidian/GNG%20Integration%20Plan.md)
- [Bootstrap Setup](../../bootstrap.md)
- [Layered Input Mapping](../../mapping.md)

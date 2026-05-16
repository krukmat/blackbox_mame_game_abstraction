# GNG-MAP-04 - Operational Surface Adoption

## Status

✅ Done — 2026-05-17

## Objective

Switch the real GNG workflow to the layered-derived generated-plan paths without changing the runtime boundary.

## Scope

- update `.env.example`
- update `blackbox.local.example.yaml`
- update `docs/bootstrap.md`
- update helper scripts that currently point at authored GNG semantic plans
- review stale source-profile and documentation references such as `base_input_plan`
- keep contributor-facing instructions aligned with the new canonical GNG mapping path

## Out Of Scope

- adding a new runtime command
- rewriting `scripts/mame_autoboot.lua`
- changing MAME runner behavior
- implementing automatic recompilation on every script launch unless that becomes strictly necessary

## Dependencies

- [GNG-MAP-03](./GNG-MAP-03-compile-and-verify-gng-generated-plans.md)

## Reasoning Grade

`High`

## Effort Grade

`Medium`

## Recommended Model

`GPT-5.5`

## Acceptance Criteria

- bootstrap surfaces point at layered-derived generated plans rather than legacy authored semantic plans
- no public-facing doc tells contributors to use the stale path after migration
- if `SourceProfile.base_input_plan` remains unchanged, that decision is documented explicitly; if it changes, tests and docs are updated coherently
- runtime behavior remains on the same planner -> Lua -> MAME boundary

## Operational Surfaces Updated

### Bootstrap config defaults

- `.env.example`
  - `BLACKBOX_BOOT_PLAN=plans/generated/gng_boot_only.yaml`
  - `BLACKBOX_TRACE_INPUT_PLAN=plans/generated/gng_gameplay.yaml`
- `blackbox.local.example.yaml`
  - `boot_plan: plans/generated/gng_boot_only.yaml`
  - `trace_input_plan: plans/generated/gng_gameplay.yaml`

### Helper scripts

- `scripts/launch_manual_capture_autoboot.sh`
  - boot-plan default now points at `plans/generated/gng_boot_only.yaml`
  - script comments now describe the generated runtime plan as the exported source
- `scripts/extract_frames.sh`
  - trace-input-plan default now points at `plans/generated/gng_gameplay.yaml`

### Contributor-facing docs

- `docs/bootstrap.md`
  - now explains that generated plans are the runtime-facing defaults
  - distinguishes runtime paths from layered editable sequence sources
- `README.md`
  - full pipeline examples now use `plans/generated/gng_gameplay.yaml`
- `CLAUDE.md`
  - bootstrap table, script description, and plans reference now point at generated GNG runtime plans

## SourceProfile Decision

`SourceProfile.base_input_plan` was changed from `plans/basic_controls.yaml` to `plans/generated/gng_boot_only.yaml`.

Reason:

- the old value no longer reflected the real GNG operational path
- the generated boot plan is now the canonical runtime-facing default for source-profile-driven GNG observation
- this keeps the source profile aligned with the contributor bootstrap surfaces without changing the runtime boundary itself

Follow-up applied here:

- `apps/mame-harness/tests/test_source_profiles.py` updated to assert the new default
- `docs/obsidian/Source Profile.md` updated to keep the architectural note aligned with implementation

## Boundary Check

The runtime boundary remains unchanged:

```text
generated public input plan YAML
  -> input_planner.py
  -> private per-frame JSON
  -> scripts/mame_autoboot.lua
  -> MAME
```

This task changed operational defaults and documentation only. It did not rewrite the planner, Lua injector, or MAME runner.

## Verification

- targeted regression tests passed:
  - `apps/mame-harness/tests/test_source_profiles.py`
  - `apps/mame-harness/tests/test_mapping_compiler.py`
- test result:
  - `14 passed`

## Notes For GNG-MAP-05

- the operational GNG path now points at layered-derived generated plans
- remaining historical task records may still reference the legacy authored plans for past-phase context, but contributor-facing runtime guidance no longer treats them as canonical
- the next task should focus on regression closure and the explicit ADR-018 boot-calibration seam

## Reference Documents

- [This Task File](./GNG-MAP-04-operational-surface-adoption.md)
- [Parent Plan](../../plans/gng_layered_mapping_adoption_plan.md)
- [Layered Input Mapping Plan](../../plans/layered_input_mapping_plan.md)
- [GNG Source Integration Plan](../../plans/gng_source_integration_plan.md)
- [README.md](../../../README.md)
- [AGENTS.md](../../../AGENTS.md)
- [CLAUDE.md](../../../CLAUDE.md)
- [ADR-005](../../adr/ADR-005-source-profile-pattern.md)
- [ADR-009](../../adr/ADR-009-input-plan-determinism.md)
- [ADR-014](../../adr/ADR-014-layered-input-mapping.md)
- [Source Profile](../../obsidian/Source%20Profile.md)
- [GNG Integration Plan](../../obsidian/GNG%20Integration%20Plan.md)
- [Bootstrap Setup](../../bootstrap.md)
- [Layered Input Mapping](../../mapping.md)

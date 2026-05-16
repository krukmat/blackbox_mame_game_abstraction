# GNG-MAP-03 - Compile And Verify GNG Generated Plans

## Status

✅ Done — 2026-05-17

## Objective

Produce generated GNG runtime plans that are behaviorally equivalent to the current accepted GNG plans.

## Scope

- compile the layered GNG inputs through the existing compiler
- verify generated plans parse through `input_planner.load_input_plan()`
- compare generated boot/gameplay plans against current accepted GNG runtime expectations
- add tests for action ordering, frame counts, and public-output safety of generated plans

## Out Of Scope

- switching scripts or docs to those new paths
- changing runtime execution code
- introducing per-device runtime variance

## Dependencies

- [GNG-MAP-02](./GNG-MAP-02-author-gng-layered-runtime-artifacts.md)

## Reasoning Grade

`High`

## Effort Grade

`Medium`

## Recommended Model

`GPT-5.5`

## Acceptance Criteria

- generated boot and gameplay plans are parseable by the current planner
- generated plans preserve the accepted GNG action ordering and frame counts
- tests make parity failures explicit
- the task makes clear whether the current compiler's `device_profile` requirement remains a validation-only dependency for committed GNG generated plans

## Execution Note

This task was materially completed as part of `GNG-MAP-02`.

Reason:

- `GNG-MAP-02` authored the canonical GNG sequences
- compiled the runtime-facing generated plans
- added parity tests against the accepted legacy plans

No additional runtime implementation was required here beyond documenting the verification outcome.

## Verified Artifacts

### Layered source inputs

- `plans/sequences/gng_boot_only.yaml`
- `plans/sequences/gng_gameplay.yaml`

### Generated runtime plans

- `plans/generated/gng_boot_only.yaml`
- `plans/generated/gng_gameplay.yaml`

### Accepted legacy comparison targets

- `plans/gng_boot_only.yaml`
- `plans/gng_gameplay.yaml`

## Verification Outcome

- generated boot and gameplay plans parse successfully through `input_planner.load_input_plan()`
- generated plans preserve the same:
  - action ordering
  - frame counts
  - step notes
- generated plans remain public-safe outputs under `plans/generated/`
- parity failures are now explicit in automated tests rather than implicit in script behavior

## Tests And Coverage

The verification is captured in `apps/mame-harness/tests/test_mapping_compiler.py`.

Covered assertions:

- GNG runtime sequences compile successfully through the current compiler
- compiled GNG runtime sequences match the accepted legacy plan steps exactly
- checked-in generated GNG plans match the accepted legacy plan behavior exactly
- generated YAML remains parseable by the existing planner
- unsafe public output paths remain rejected by the compiler guardrails

## Device Profile Dependency Decision

The current compiler's `device_profile` requirement remains a validation-only dependency for committed GNG generated plans.

That means:

- the authoritative GNG runtime behavior lives in:
  - `profiles/games/gngb/default_actions.yaml`
  - `plans/sequences/gng_boot_only.yaml`
  - `plans/sequences/gng_gameplay.yaml`
- a concrete `device_profile` is still required to run the existing compiler
- the resulting committed runtime plans do not materially vary by device once canonical controls are validated

This dependency remains intentionally unchanged here and is not treated as a runtime architecture decision for GNG.

## Notes For GNG-MAP-04

- parity is now established for the generated plans
- the remaining migration work is operational, not behavioral
- `.env.example`, `blackbox.local.example.yaml`, helper scripts, bootstrap docs, README/CLAUDE references, and `SourceProfile.base_input_plan` still point at stale legacy surfaces and must be reviewed next

## Reference Documents

- [This Task File](./GNG-MAP-03-compile-and-verify-gng-generated-plans.md)
- [Parent Plan](../../plans/gng_layered_mapping_adoption_plan.md)
- [Layered Input Mapping Plan](../../plans/layered_input_mapping_plan.md)
- [README.md](../../../README.md)
- [AGENTS.md](../../../AGENTS.md)
- [CLAUDE.md](../../../CLAUDE.md)
- [ADR-009](../../adr/ADR-009-input-plan-determinism.md)
- [ADR-014](../../adr/ADR-014-layered-input-mapping.md)
- [Input Plan](../../obsidian/Input%20Plan.md)
- [Layered Input Mapping](../../mapping.md)
- [Bootstrap Setup](../../bootstrap.md)

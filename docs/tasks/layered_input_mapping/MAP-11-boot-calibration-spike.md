# MAP-11 - Boot Calibration Spike

## Status

Completed — 2026-05-16

## Purpose

Design a calibration spike that reduces fragile hand-authored boot timing in the MAME harness without weakening the clean-room boundary and without introducing public visual artifacts.

`MAP-03` through `MAP-10` stabilized the layered input mapping model, import paths, and manual wizard flow. The remaining gap in this phase is still operational: boot timing is brittle and currently depends on fixed frame counts carried through the GNG layered sequence and generated-plan path.

This task is a spike first, not a production rewrite. Its job is to define what a safe calibration workflow would look like, what public outputs are allowed, what must remain private, and whether a follow-up implementation requires another ADR.

## Reference Reasoning

`High`

Reasoning basis:

- the task touches the private/public clean-room boundary directly
- it operates near timing, observation, and possible evidence-derived behavior
- a poor design could accidentally introduce screenshot-based logic, pixel comparison, or public leakage of private calibration evidence
- the task must separate allowed abstract timing outputs from forbidden media-derived outputs before any implementation can be considered safe

## Scope

- define the problem statement for boot calibration in the current mapping/bootstrap flow
- identify the current fragile points in hand-authored boot plans and fixed-frame waits
- define a safe spike proposal for calibration inputs, processing steps, and public outputs
- explicitly define which artifacts remain private and which outputs may be public
- define what is forbidden:
  - screenshots
  - public frame references
  - pixel comparison as a validation method
  - public video-derived artifacts
- determine whether the proposed next implementation step requires a new ADR
- document the proposed workflow, risks, and validation gates

## Out of Scope

- implementing automatic screen-state detection
- implementing screenshot capture or public image outputs
- modifying `scripts/mame_autoboot.lua`
- replacing `input_planner.py`
- replacing the MAME execution boundary
- introducing a RetroArch or non-MAME runtime
- calibrating multiple games generically in this task
- any production implementation beyond spike-level design and documentation

## Inputs

- `docs/plans/layered_input_mapping_plan.md`
- current bootstrap flow:
  - `.env.example`
  - `blackbox.local.example.yaml`
  - `docs/bootstrap.md`
  - `apps/mame-harness/cli.py`
  - `scripts/launch_manual_capture_autoboot.sh`
  - `scripts/mame_autoboot.lua`
- existing boot/input plans:
  - `plans/sequences/gng_boot_only.yaml`
  - `plans/sequences/gng_gameplay.yaml`
  - `plans/generated/gng_boot_only.yaml`
  - `plans/generated/gng_gameplay.yaml`
- prior timing-related task context:
  - `docs/tasks/gng_source_integration/T10.3-timing-calibration.md`

## Deliverables

- this task file completed and current
- a spike document or equivalent written proposal describing:
  - the calibration goal
  - allowed public outputs
  - forbidden outputs
  - private-only evidence surfaces
  - candidate command/workflow shape
  - guardrails and validation strategy
  - ADR requirement decision
- any required follow-up ADR if the spike establishes a new architectural pattern

Completed deliverables:

- [Boot Calibration Spike](../../boot_calibration_spike.md)
- [ADR-018](../../adr/ADR-018-boot-calibration-public-contract.md)

## Dependencies

- `MAP-10`

## Blocks

- any future implementation task for boot calibration

## Acceptance Criteria

- the spike clearly states which calibration artifacts may be public and which must remain private
- the spike does not permit screenshots, videos, frame paths, crop paths, or pixel comparisons as public outputs
- the proposed public outputs are abstract only
- the spike explains how it would fit the existing execution path without rewriting the runtime boundary
- the spike explicitly states whether a follow-up implementation requires a new ADR
- the task file contains enough context and references for another agent to continue without ambiguity

Outcome:

- public calibration output is constrained to an abstract `boot_calibration` artifact plus optional generated input plan YAML
- screenshots, videos, frame paths, crop paths, OCR dumps, and per-frame visual logs remain private-only or forbidden
- the recommended MVP is a hybrid manual-confirmation `calibrate-boot` flow that preserves the current planner -> Lua -> MAME path
- follow-up implementation does require an ADR; that decision is recorded in [ADR-018](../../adr/ADR-018-boot-calibration-public-contract.md)

## Effort

`M`

## Recommended Model

`GPT-5.5`

## Reference Documents

- [Layered Input Mapping Plan](../../plans/layered_input_mapping_plan.md)
- [Layered Input Mapping Tasks README](./README.md)
- [README.md](../../../README.md)
- [AGENTS.md](../../../AGENTS.md)
- [CLAUDE.md](../../../CLAUDE.md)
- [Bootstrap Setup](../../bootstrap.md)
- [Layered Input Mapping](../../mapping.md)
- [Boot Calibration Spike](../../boot_calibration_spike.md)
- [ADR-003](../../adr/ADR-003-public-output-blocklist.md)
- [ADR-018](../../adr/ADR-018-boot-calibration-public-contract.md)
- [ADR-014](../../adr/ADR-014-layered-input-mapping.md)
- [Input Plan](../../obsidian/Input%20Plan.md)
- [T10.3 - Timing Calibration](../gng_source_integration/T10.3-timing-calibration.md)
- [GNG Source Integration Tasks README](../gng_source_integration/README.md)

## Implementation Notes

- treat this as a design spike unless the scope is materially expanded by a new approved task file
- prefer documenting concrete calibration stages and failure modes over speculative automation
- if a follow-up implementation would inspect private visual evidence, keep that evidence private and describe only abstract/timing outputs publicly

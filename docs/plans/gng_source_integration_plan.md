# GNG Source Integration Plan

## Purpose

Use the local `gng.zip` ROM set and the existing MAME installation as a private observation source for this repository's clean-room abstraction workflow.

The immediate goal is not a faithful Ghosts'n Goblins port. The immediate goal is to make `gng` a reproducible, legally bounded input source that can feed private evidence capture and a first public abstract mechanics spec.

## Stage Objective

Deliver a working `gng` source profile with:

- deterministic MAME configuration
- private-only capture outputs
- public metadata redaction
- preflight validation for MAME and ROM inputs
- one initial private capture run
- one initial public abstract mechanics artifact

## Scope Boundary

### In Scope

- Python 3.11 execution normalization for this repo
- `gng` source profile definition
- MAME and ROM preflight validation
- runner error handling hardening
- public metadata redaction hardening
- contract tests for `gng` integration
- CLI integration for a profile-driven `gng` run
- one real private capture
- one first-pass public abstract mechanics schema and output
- RN prototype hookup to the abstract spec

### Out of Scope

- faithful game migration
- pixel-perfect validation
- public screenshots, videos, save states, or sprite outputs
- generalized multi-game plugin architecture
- full ROM manifest decoder parity with the separate `gng` project
- advanced CV/ML inference
- full stage scripting, enemy catalog, or progression parity

## Dependency Order

The tasks below must execute in this order because each later task depends on a stabilized contract from the earlier tasks.

1. `T01` Python 3.11 Runtime Normalization
2. `T02` GNG Source Profile Definition
3. `T03` MAME and ROM Preflight Validation
4. `T04` MAME Runner Hardening
5. `T05` Public Metadata Redaction Hardening
6. `T06` GNG Contract Test Coverage
7. `T07` CLI Source Profile Integration
8. `T08` Initial Private GNG Capture
9. `T09` First Abstract Observation Schema
10. `T10` Private Evidence to Public Abstract Spec Transformation (T10.1–T10.6)
11. `T10.4` Public Artifact Generation + Guardrails Verification *(gate for T11)*
12. `T11.1` Abstract Mechanics Loader (TypeScript YAML)
13. `T11.2` Trace Episode Extractor
14. `T11.3` Physics Calibration from Trace
15. `T10.7` Tracker Continuity Fix *(remediation — unblocks T11.4 calibration quality)*
    - `T10.7` ST1/ST2 ✅ (merged) — `max_frame_jump_px` + `MIN_GROUND_STREAK`
    - `T10.7.A` ✅ Visual-Anchored Calibration *(supersedes T10.7 ST3/ST4 — pivot to human-validated picker per ADR-019; jumpVelocity=0.4668/s, gravity=0.1167/s², t_peak error=0%)*
    - `T10.7.B` ✅ Entity-ID Collision Fix *(allow_player=False for remaining_regions; zero duplicate player frames in run_t10_7_jumps trace)*
    - `T10.7.C` Walk-Segment Picker — controlled locomotion calibration *(ADR-019 pattern; resolves 1.8709/s vs 13.4935/s conflict)*
    - `T10.7.D` Projectile Velocity Decision ✅ *(Option B selected — surrogate rejected)*
    - `T10.7.E` Projectile In-Flight Tracking *(new ADR-020; real projectile measurement required before sync)*
    - `T10.7 ST5` Propagate all calibrated values to mechanics YAML + regenerate episodes *(blocked on T10.7.C + T10.7.E)*
16. `T10.8` Enemy Tracking Continuity (Stage 1 Screen 1) *(new ADR-021; persistent enemy IDs required before T11.2 quality)*
    - `T10.8.1` Enemy Signature Catalog and Calibration (zombi, crow)
    - `T10.8.2` EntityTracker Generalization + ArthurTracker Wrapper
    - `T10.8.3` trace_extractor Integration (persistent IDs + lifecycle events)
    - `T10.8.4` Regression Test Suite for Enemy Tracking
    - `T10.8.5` Trace Regeneration and Quality Validation
    - `T10.8.6` ADR-021 Publication and Documentation Updates
17. `T10.9` Boss and Devil Tracking (Stage 1 Full Sweep) *(new ADR-022; closes stage-1 trace coverage and resolves ADR-013 MOG2 scroll-reset Known Gap)*
    - `T10.9.1` Scroll Detection + MOG2 Reset (ADR-022)
    - `T10.9.2` Red Arremer Signature Calibration
    - `T10.9.3` Cyclops Boss Signature Calibration
    - `T10.9.4` EntityTracker Integration + Regression Tests
    - `T10.9.5` Trace Regeneration, Validation, and Documentation
18. `T11.4` Episode-Driven Scene in RN Prototype
19. `T11.5` Clean-Room Verification

## Dependency Rationale

- `T01` must come first because the repo already declares Python `>=3.11`, and any test or CLI contract work is unreliable if contributors invoke the wrong interpreter.
- `T02` must come before `T03` because the preflight rules depend on a canonical statement of what `gng` means in this repo.
- `T03` must come before `T04` because the runner should consume structured preflight results instead of embedding ad hoc checks.
- `T04` must come before `T05` because the runner output shape must stabilize before public redaction rules can be finalized.
- `T05` must come before `T06` so tests encode the final public-safety contract.
- `T06` must come before `T07` so CLI integration uses already-tested primitives.
- `T07` must come before `T08` so the first real capture uses the intended profile path rather than manual flags.
- `T08` must come before `T09` and `T10` because the first public abstraction should be grounded in real private evidence, not assumptions.
- `T10.4` must come before all T11 subtasks because it produces the quality-gated `gng_trace.json` that T11.2 and T11.3 require. A fresh MAME capture is required — the pre-T10.6 evidence is insufficient for physics calibration.
- `T11.1` must come before `T11.3` because the TypeScript mechanics types must exist before PhysicsSystem can be updated with calibrated values.
- `T11.2` must come before `T11.4` because episode data must exist before the scene can be built from it.
- `T11.3` must come before `T11.4` because PhysicsSystem must use calibrated values in the episode scene.
- `T10.7` (Tracker Continuity Fix) is inserted after `T11.3` and before `T11.4` as a remediation branch. `T11.3` surfaced an inconsistency in the calibrated jump constants caused by tracker noise (174 `jump_start` events, most of them detector artifacts). Without `T10.7`, the calibration values are mathematically valid but physically inconsistent (predicted `t_peak ≈ 0.36 frames` vs observed `≈ 16 frames`). `T10.7` does not require a new MAME capture — it re-extracts trace from existing `run_t10_4_01` frames after fixing `ArthurTracker` and `_infer_events`. See `docs/plans/T10.7-tracker-continuity-fix.md`.
- `T10.7.A` (Visual-Anchored Calibration) supersedes T10.7 ST3/ST4. After ST1/ST2 merged, the trace still contained residual noise (30/30 `jump_start` gate not met). Rather than chase the residual source through further trace cleanup, T10.7.A pivots to a human-validated picker pattern (formalized in [ADR-019](../adr/ADR-019-human-validated-calibration-candidates.md)): `apps/mame-harness/visual_jump_picker.py` surfaces candidates, the operator validates against private PNGs, `physics_calibrator` consumes accepted IDs. See `docs/plans/T10.7.A-visual-calibration-pivot.md`.
- `T10.7.B` (Entity-ID Collision Fix) was inserted after T10.7.A ST.A3a execution revealed that the picker output is still corrupted by a `trace_extractor` bug: `_entity_type_from_box` returns `"player"` for any blob with player-sized area, producing duplicate `entity_id="player"` entries that bypass per-entity debounce. T10.7.B adds an `allow_player` flag and updates the two `remaining_regions` callsites in `extract_trace`. T10.7.A ST.A3b is blocked on this fix. See `docs/plans/T10.7.B-entity-id-collision-fix.md`.
- `T10.7.C` (Walk-Segment Picker) is inserted after T10.7.B because it requires a clean trace (no duplicate player entries) for reliable segment detection. T10.7.A produced jump/gravity values but `locomotion_velocity_x` remains unreliable: the calibration YAML has 1.8709/s (n=83 from a jump-only trace, few walking frames) while the mechanics YAML has 13.4935/s (n=1228 from T11.3, noisy method). Both are inconsistent and untrustworthy. T10.7.C applies the ADR-019 picker pattern to a walk-only capture to produce a direct, human-validated `Δx/frame` measurement. See `docs/tasks/gng_source_integration/T10.7.C-locomotion-calibration.md`.
- `T10.7.D` (Projectile Velocity Decision) ran in parallel with T10.7.C and resolved in favor of Option B. The repository will not preserve a surrogate projectile constant as calibrated public output. See `docs/tasks/gng_source_integration/T10.7.D-projectile-velocity-decision.md`.
- `T10.7.E` (Projectile In-Flight Tracking) is added as the implementation consequence of that decision. It introduces a calibration-scoped projectile continuity path plus an ADR-019 picker workflow so `projectile_velocity_x` can be measured from real projectile motion rather than player movement. See `docs/tasks/gng_source_integration/T10.7.E-projectile-in-flight-tracking.md` and `docs/adr/ADR-020-projectile-in-flight-tracking.md`.
- `T10.7 ST5` (mechanics YAML full sync + episode regeneration) is now blocked on T10.7.C and T10.7.E. It must not propagate a partial set of values while locomotion remains unresolved or projectile calibration remains surrogate-based.
- `T10.8` (Enemy Tracking Continuity) is inserted after T10.7.E and before T11.2 because it resolves the ADR-013 Known Gap "Cross-frame enemy ID continuity is not implemented." Without persistent enemy IDs, T11.2 episode extraction emits inflated `spawn` counts and no per-enemy lifecycle, which degrades every downstream consumer (validation, T12 encounter grammar). T10.8 generalizes `ArthurTracker` into a reusable `EntityTracker` (ADR-021) and calibrates `EnemySignature` bounds for zombi and crow via the ADR-019 picker pattern. Scope is limited to stage 1 screen 1 (no camera scroll); boss tracking is deferred to T10.9. See `docs/plans/T10.8-enemy-tracking-continuity.md`.
- `T10.9` (Boss and Devil Tracking) is inserted after T10.8 and before T11.2 because it closes stage-1 trace coverage by adding the Red Arremer and the stage-1 boss (cyclops). It also resolves the ADR-013 Known Gap "MOG2 background model must be reset when the camera scrolls" via the new `ScrollDetector` (ADR-022) — a precondition for any post-scroll detection. T10.9 reuses the `EntityTracker` infrastructure from T10.8 and the picker calibration pattern from T10.8.1 / T10.7.A / T10.7.C / T10.7.E. Stage 2+ tracking remains out of scope. See `docs/plans/T10.9-boss-and-devil-tracking.md`.
- `T11.5` must be last in the T11 chain because it audits the full import graph after all other changes are in place.

## Deliverables

- a canonical `gng` source profile
- MAME/ROM preflight module
- hardened Python runner contract
- public metadata redaction coverage for local sensitive paths
- task-level automated tests
- one successful private capture directory under `evidence/private`
- one first public abstract mechanics artifact
- one RN prototype scene driven by the public abstract mechanics artifact

## Reasoning Reference Scale

Each task in this stage must declare its reference reasoning level.

- `Low`: bounded local change, limited ambiguity, mostly mechanical implementation
- `Medium`: cross-module reasoning, contract alignment, moderate ambiguity, test design required
- `High`: architectural or boundary-sensitive work, evidence interpretation, abstraction design, or legal/clean-room risk

The reasoning reference is not optional metadata. It is part of the task definition and should be used to judge whether the task is being executed with the appropriate care.

## Exit Criteria

This stage is complete only when all of the following are true:

- `gng` can be launched through a profile-driven repo command
- the repo forces the correct MAME driver choice for the local `gng.zip` set
- public outputs contain no local absolute paths, ROM paths, frame paths, crop paths, or direct evidence references beyond sanctioned private handles
- at least one real private capture run has completed successfully
- at least one public abstract mechanics artifact exists and contains only clean-room-safe information
- the RN prototype consumes that artifact without depending on ROMs, MAME, or private evidence paths

## Task Index

- [T01 - Python 3.11 Runtime Normalization](../tasks/gng_source_integration/T01-python-3.11-runtime-normalization.md) ✅
- [T02 - GNG Source Profile Definition](../tasks/gng_source_integration/T02-gng-source-profile-definition.md) ✅
- [T03 - MAME and ROM Preflight Validation](../tasks/gng_source_integration/T03-mame-and-rom-preflight-validation.md) ✅
- [T04 - MAME Runner Hardening](../tasks/gng_source_integration/T04-mame-runner-hardening.md) ✅
- [T05 - Public Metadata Redaction Hardening](../tasks/gng_source_integration/T05-public-metadata-redaction-hardening.md) ✅
- [T06 - GNG Contract Test Coverage](../tasks/gng_source_integration/T06-gng-contract-test-coverage.md) ✅
- [T07 - CLI Source Profile Integration](../tasks/gng_source_integration/T07-cli-source-profile-integration.md) ✅
- [T08 - Initial Private GNG Capture](../tasks/gng_source_integration/T08-initial-private-gng-capture.md) ✅
- [T09 - First Abstract Observation Schema](../tasks/gng_source_integration/T09-first-abstract-observation-schema.md) ✅
- [T10 - Private Evidence to Public Abstract Spec Transformation](../tasks/gng_source_integration/T10-private-evidence-to-public-abstract-spec-transformation.md) ✅ (T10.1–T10.6 complete)
- [T10.4 - Public Artifact Generation + Guardrails Verification](../tasks/gng_source_integration/T10.4-public-artifact-generation.md) ✅
- [T10.8 - Enemy Tracking Continuity (Stage 1 Screen 1)](../tasks/gng_source_integration/T10.8-enemy-tracking-continuity.md) 🔲 Planned
  - [T10.8.1 - Enemy Signature Catalog and Calibration](../tasks/gng_source_integration/T10.8.1-enemy-signature-catalog.md)
  - [T10.8.2 - EntityTracker Generalization](../tasks/gng_source_integration/T10.8.2-entity-tracker-generalization.md)
  - [T10.8.3 - trace_extractor Integration](../tasks/gng_source_integration/T10.8.3-trace-extractor-integration.md)
  - [T10.8.4 - Regression Test Suite](../tasks/gng_source_integration/T10.8.4-regression-tests.md)
  - [T10.8.5 - Trace Regeneration and Quality Validation](../tasks/gng_source_integration/T10.8.5-trace-regeneration.md)
  - [T10.8.6 - ADR-021 Publication and Documentation Updates](../tasks/gng_source_integration/T10.8.6-adr-and-docs.md)
- [T10.9 - Boss and Devil Tracking (Stage 1 Full Sweep)](../tasks/gng_source_integration/T10.9-boss-and-devil-tracking.md) 🔲 Planned
  - [T10.9.1 - Scroll Detection + MOG2 Reset](../tasks/gng_source_integration/T10.9.1-scroll-detection-mog2-reset.md)
  - [T10.9.2 - Red Arremer Signature Calibration](../tasks/gng_source_integration/T10.9.2-red-arremer-signature.md)
  - [T10.9.3 - Cyclops Boss Signature Calibration](../tasks/gng_source_integration/T10.9.3-cyclops-boss-signature.md)
  - [T10.9.4 - EntityTracker Integration + Regression Tests](../tasks/gng_source_integration/T10.9.4-entity-tracker-integration.md)
  - [T10.9.5 - Trace Regeneration, Validation, and Documentation](../tasks/gng_source_integration/T10.9.5-trace-regeneration-and-docs.md)
- [T11 - RN Prototype Hookup](../tasks/gng_source_integration/T11-rn-prototype-hookup.md) 🔄 In Progress
  - [T11.1 - Abstract Mechanics Loader](../tasks/gng_source_integration/T11-rn-prototype-hookup.md#t111--abstract-mechanics-loader-typescript-yaml) ✅
  - [T11.2 - Trace Episode Extractor](../tasks/gng_source_integration/T11-rn-prototype-hookup.md#t112--trace-episode-extractor) ✅
  - [T11.3 - Physics Calibration from Trace](../tasks/gng_source_integration/T11.3-physics-calibration.md) 🔲 **← current**
  - [T11.3 - Physics Calibration from Trace](../tasks/gng_source_integration/T11-rn-prototype-hookup.md#t113--physics-calibration-from-trace)
  - [T11.4 - Episode-Driven Scene in RN Prototype](../tasks/gng_source_integration/T11-rn-prototype-hookup.md#t114--episode-driven-scene-in-rn-prototype)
  - [T11.5 - Clean-Room Verification](../tasks/gng_source_integration/T11-rn-prototype-hookup.md#t115--clean-room-verification)

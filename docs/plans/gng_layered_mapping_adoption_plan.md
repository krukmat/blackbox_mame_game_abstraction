# GNG Layered Mapping Adoption Plan

## Purpose

Define how the existing `gng` observation workflow moves onto the layered input mapping model without changing the current MAME execution boundary.

This plan is specifically about adopting the new mapping paradigm for the already-existing GNG work. It does not introduce a new game, a new runtime, or a new clean-room boundary.

## Why This Plan Exists

Layered input mapping is already implemented in the repo, but the active GNG operational path still relies on hand-authored semantic plans:

- `plans/gng_boot_only.yaml`
- `plans/gng_gameplay.yaml`
- `.env.example` and `blackbox.local.example.yaml` pointing at those plans
- `scripts/launch_manual_capture_autoboot.sh` and `scripts/extract_frames.sh` reading those paths directly

That leaves GNG split across two paradigms:

- the new layered mapping model for public mapping artifacts
- the older direct semantic-plan model for real GNG capture workflows

The goal of this plan is to remove that split while preserving the working `gng -> gngb` source-profile contract and the existing planner -> Lua -> MAME runtime path.

## Phase Objective

Represent GNG runtime inputs through the layered model:

```text
device profile
  -> controller profile
  -> gngb game action profile
  -> gng input sequence
  -> compiled public input plan YAML
  -> input_planner.py
  -> private per-frame JSON
  -> scripts/mame_autoboot.lua
  -> MAME
```

For GNG specifically:

- `gng` remains the source profile id
- `gngb` remains the MAME driver contract from ADR-005
- `profiles/games/gngb/default_actions.yaml` remains the semantic action layer
- new `input_sequence` artifacts replace the authored semantic GNG plans as the editable source of truth
- compiled plans under `plans/generated/` become the runtime-facing public artifacts used by scripts and local bootstrap config

## Non-Negotiable Constraints

- Do not change the `gng` source profile driver contract: `gng.zip` must still launch with `gngb`.
- Do not rewrite `input_planner.py`, `scripts/mame_autoboot.lua`, or the MAME runner as part of this adoption.
- Do not weaken public-output guardrails or introduce private evidence references into public mapping artifacts.
- Do not make the runtime depend on a specific physical controller profile.
- Do not encode ROM paths, screenshots, crops, frame paths, or `private://` references in any public mapping artifact.
- Preserve the current calibrated GNG boot timings unless and until a later boot-calibration implementation supersedes them through the ADR-018 contract.

## Planning Decision

For GNG, the new paradigm should be applied at the `game_action_profile + input_sequence` layer, not at the physical device layer.

Reason:

- GNG automated observation uses semantic arcade actions injected by Lua, not live user hardware input.
- The `device_profile` layer is still useful for validation and for human-operated compile workflows, but it is not the authoritative place to express GNG boot and gameplay behavior.
- The authoritative editable GNG inputs should therefore become:
  - `profiles/games/gngb/default_actions.yaml`
  - `plans/sequences/gng_boot_only.yaml` or equivalent sequence file
  - `plans/sequences/gng_gameplay.yaml` or equivalent sequence file

The generated runtime artifacts should then live under `plans/generated/`.

## Current-State Risks

- `SourceProfile.base_input_plan` still points at `plans/basic_controls.yaml`, which no longer reflects the real GNG operating path.
- `.env.example`, `blackbox.local.example.yaml`, and helper scripts still assume hand-authored semantic GNG plans are canonical.
- The current compiler requires a `device_profile` even though compiled runtime plans do not materially vary by device once canonical controls are validated.
- Boot timing is still encoded directly in public plans. ADR-018 already defines the future public contract for replacing those fixed waits with a clean-room-safe calibration artifact, but that implementation is not yet the active runtime.

## Dependency Analysis

The work is ordered around contract preservation:

1. Decompose the existing GNG plans into layered responsibilities before changing any paths or docs.
2. Author layered GNG sequences and compile them to generated plans before switching operational surfaces.
3. Repoint bootstrap config, scripts, and source-profile references only after generated plans exist and match current behavior.
4. Close with regression coverage and an explicit boot-calibration seam so the GNG path does not fork again later.

Dependency graph:

```text
GNG-MAP-01
  ↓
GNG-MAP-02
  ↓
GNG-MAP-03
  ↓
GNG-MAP-04
  ↓
GNG-MAP-05
```

## Task Order

### GNG-MAP-01 - Legacy GNG Plan Decomposition

- Objective: map the current GNG operational inputs to the layered model and define which public artifact owns each concern.
- Scope: inventory `gng_boot_only` and `gng_gameplay`; classify semantic actions, fixed waits, source-profile assumptions, and script consumers; define the migration matrix from legacy plan steps to `game_action_profile`, `input_sequence`, compiled plan, and later `boot_calibration`.
- Out of scope: editing runtime files, changing plan paths, changing scripts.
- Dependencies: completed ADR-014 implementation; completed GNG timing calibration context from T10.3.
- Reasoning grade: High
- Effort grade: Low
- Recommended model: GPT-5.5
- Acceptance criteria: every step in the two current GNG plans is accounted for in the layered model; unresolved ownership questions are documented explicitly; no implementation files are changed beyond planning/task docs.

### GNG-MAP-02 - Author GNG Layered Runtime Artifacts

- Objective: make the layered GNG artifacts the public source of truth for boot and gameplay sequencing.
- Scope: add or revise GNG `input_sequence` files for boot-only and gameplay capture; keep `profiles/games/gngb/default_actions.yaml` aligned with those sequences; define stable generated-plan output paths under `plans/generated/`.
- Out of scope: switching scripts or local config to those generated paths yet.
- Dependencies: GNG-MAP-01.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: GPT-5.5
- Acceptance criteria: layered GNG sequences express the full current boot and gameplay behavior without using unsupported actions; the artifact layout is deterministic and public-safe; the semantic action layer stays compatible with `input_planner.VALID_ACTIONS`.

### GNG-MAP-03 - Compile And Verify GNG Generated Plans

- Objective: produce generated GNG runtime plans that are behaviorally equivalent to the current authored plans.
- Scope: compile the layered GNG inputs through the existing compiler; compare generated output against the current runtime expectations; add tests proving generated plans parse through `load_input_plan()` and preserve the calibrated GNG step ordering and frame counts.
- Out of scope: changing bootstrap docs or scripts before parity is verified.
- Dependencies: GNG-MAP-02.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: GPT-5.5
- Acceptance criteria: generated boot and gameplay plans are parseable, public-safe, and equivalent in action ordering and frame counts to the accepted GNG runtime behavior.

### GNG-MAP-04 - Operational Surface Adoption

- Objective: switch the real GNG workflow to the generated-plan paths with minimal runtime disruption.
- Scope: update `.env.example`, `blackbox.local.example.yaml`, bootstrap docs, helper scripts, and any stale source-profile/documentation references so the operational GNG path points at layered-derived generated plans; decide whether `SourceProfile.base_input_plan` should now point at the generated boot plan or another documented default.
- Out of scope: introducing a new runtime command, changing the Lua injector, or adding auto-regeneration logic unless strictly necessary.
- Dependencies: GNG-MAP-03.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: GPT-5.5
- Acceptance criteria: a new contributor reading bootstrap docs lands on the layered-derived GNG path, not the legacy authored-plan path; no operational surface points to removed or stale GNG plan artifacts.

### GNG-MAP-05 - Regression Closure And Boot-Calibration Seam

- Objective: close the migration with tests, documentation, and an explicit handoff point to ADR-018 boot calibration work.
- Scope: add regression tests for generated-plan safety and GNG path resolution; document how future `boot_calibration.yaml` output will replace or regenerate the boot sequence without reintroducing hand-authored semantic plan drift.
- Out of scope: implementing production boot calibration.
- Dependencies: GNG-MAP-04.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: GPT-5.5
- Acceptance criteria: the repo documents one clear GNG mapping path under the new paradigm; tests cover generated GNG plan integrity; the calibration follow-up seam is explicit and does not require a second GNG-specific mapping architecture.

## Reference Documents

- [This Plan](./gng_layered_mapping_adoption_plan.md)
- [Layered Input Mapping Plan](./layered_input_mapping_plan.md)
- [GNG Source Integration Plan](./gng_source_integration_plan.md)
- [README.md](../../README.md)
- [AGENTS.md](../../AGENTS.md)
- [CLAUDE.md](../../CLAUDE.md)
- [ADR-005](../adr/ADR-005-source-profile-pattern.md)
- [ADR-009](../adr/ADR-009-input-plan-determinism.md)
- [ADR-014](../adr/ADR-014-layered-input-mapping.md)
- [ADR-018](../adr/ADR-018-boot-calibration-public-contract.md)
- [Input Plan](../obsidian/Input%20Plan.md)
- [Source Profile](../obsidian/Source%20Profile.md)
- [GNG Integration Plan](../obsidian/GNG%20Integration%20Plan.md)
- [Bootstrap Setup](../bootstrap.md)
- [Layered Input Mapping](../mapping.md)

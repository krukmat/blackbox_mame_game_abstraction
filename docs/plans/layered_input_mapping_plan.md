# Layered Input Mapping Plan

## Purpose

Define the documentation and execution plan for introducing layered input mapping to the MAME harness.

This plan is documentation-only until its tasks are executed. It does not implement schemas, profiles, loaders, compilers, CLI commands, importers, wizard flows, boot calibration, or MAME runner changes.

The immediate goal is to reduce first-run mapping friction while preserving the existing clean-room boundary and the current MAME execution path.

## Phase Objective

Deliver a compatibility layer that separates physical input mapping from canonical controller vocabulary and game-specific semantic actions, then compiles those layers into the existing deterministic input plan format.

Target architecture:

```text
physical device profile
        ↓
canonical controller profile
        ↓
game action profile
        ↓
compiled input plan
        ↓
existing frame-level JSON / Lua / MAME execution
```

The first implementation PR must preserve the existing execution path:

```text
layered public profiles
        ↓
generated public input plan YAML
        ↓
apps/mame-harness/input_planner.py
        ↓
private per-frame JSON
        ↓
scripts/mame_autoboot.lua
        ↓
MAME
```

## Scope Boundary

### In Scope

- repository orientation and audit before implementation
- adopting the incoming layered input mapping ADR into the repo ADR sequence
- JSON Schemas for `device_profile`, `controller_profile`, `game_action_profile`, and `input_sequence`
- minimal sample profiles for keyboard, an arcade two-button controller, and the `gngb` first sample
- minimal smoke input sequence that uses canonical controls
- profile loading and validation
- guardrail checks for public profile and generated plan safety
- compiler from layered profiles to the current input plan YAML format
- CLI commands for `map validate` and `map compile`
- contributor documentation for the mapping model
- first-PR review focused on clean-room safety and backward compatibility
- a later portability phase for environment config and doctor/preflight support
- later optional importers and guided setup after the core profile model stabilizes

### Out of Scope

- rewriting the MAME runner
- changing `scripts/mame_autoboot.lua`
- replacing `input_planner.py` as the execution boundary
- changing the private/public clean-room boundary
- adding ROMs, screenshots, videos, audio, save states, frame dumps, crops, sprites, or image-to-image workflows
- public outputs containing absolute local paths, ROM paths, frame paths, crop paths, or private evidence paths
- SDL GameControllerDB importer in the first PR
- RetroArch autoconfig importer in the first PR
- `map init` wizard in the first PR
- boot calibration in the first PR
- clone-specific implementation or source-level reproduction
- generalized multi-game plugin architecture

## Non-Negotiable Constraints

- Public mapping profiles are clean-room public artifacts. They may contain abstract control mappings only.
- Generated input plans must be parseable by `apps/mame-harness/input_planner.py`.
- Missing or unknown mappings must fail fast with actionable errors. Silent fallback to `noop` is not acceptable for required controls because it can hide broken captures.
- `gngb` is the first supported sample, not a hardcoded architecture assumption.
- New public writers must use existing guardrail conventions or an equivalent guardrail-aware path and payload check.
- Existing input plans must continue to work unchanged.
- Existing CLI commands must continue to work unchanged.

## MAP-00 Compatibility Findings

- The generated target format remains the current YAML contract: top-level `plan_name`, `game_id`, and `steps`, with `steps[*]` limited to `action`, `frames`, and optional `notes`.
- Compatibility must be checked through `apps/mame-harness/input_planner.py::load_input_plan`, not schema validation alone.
- The first implementation PR must respect the current Lua execution surface. `pause` exists in `input_planner.VALID_ACTIONS` but is not presently injected by `scripts/mame_autoboot.lua`, so it is not part of the safe first-PR mapping contract.

## Dependency Analysis

The work is ordered by contract stabilization:

1. Documentation and ADR adoption must happen first because the mapping layer introduces a new reusable architectural pattern.
2. Schemas and sample profiles must exist before loader validation can be implemented or tested against real fixtures.
3. Loader validation must exist before the compiler, because compilation must consume validated profile objects rather than raw YAML dictionaries.
4. The compiler must exist before CLI integration, because `map compile` should be a thin command wrapper around tested primitives.
5. Documentation must follow the working CLI and file layout so it describes the implemented contract rather than an aspirational one.
6. Portability, importers, wizard setup, and boot calibration depend on the profile model being stable and are intentionally deferred.

Dependency graph:

```text
MAP-00
  ↓
MAP-01
  ↓
MAP-02
  ↓
MAP-03
  ↓
MAP-04
  ↓
MAP-05
  ↓
MAP-06
  ↓
MAP-07
  ↓
MAP-08 / MAP-09 / MAP-10
  ↓
MAP-11
```

## Phase And Task Order

### MAP-00 - Repository Orientation and Baseline Audit

- Objective: verify the current input plan, CLI, guardrail, source profile, preflight, runner, and Lua contracts before any code or documentation changes.
- Scope: read `input_planner.py`, `cli.py`, `guardrails.py`, `metadata_writer.py`, `source_profiles.py`, `preflight.py`, `mame_runner.py`, `scripts/mame_autoboot.lua`, schemas, and relevant tests; run a focused baseline test subset; produce a concise technical summary of integration points and target plan format.
- Out of scope: implementation, documentation edits, ADR authoring.
- Dependencies: none.
- Reasoning grade: High
- Effort grade: Low
- Recommended model: capable reasoning model
- Acceptance criteria: audit confirms the generated plan target format; focused tests pass or failures are documented as pre-existing blockers; integration points are named; no files are changed.

### MAP-01 - Documentation Phase and ADR Adoption

- Objective: establish the authoritative architecture and plan before implementation, based on the orientation findings from MAP-00.
- Scope: this parent plan; create `docs/adr/ADR-014-layered-input-mapping.md` from the incoming ADR content; create the corresponding Obsidian note; update ADR indexes in `AGENTS.md`, `CLAUDE.md`, `docs/obsidian/README.md`, and `docs/obsidian/00 - Project Overview.md`.
- Out of scope: schemas, profile files, Python modules, CLI commands.
- Dependencies: MAP-00.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: capable reasoning model
- Acceptance criteria: ADR numbering follows the repo sequence; the plan and ADR clearly state scope, limits, dependency order, and clean-room constraints; no implementation files are changed except documentation indexes.

### MAP-02 - Schemas and Minimal Public Fixtures

- Objective: add the smallest stable public contract for layered mapping.
- Scope: create schema files for `device_profile`, `controller_profile`, `game_action_profile`, and `input_sequence`; add sample YAML files under `profiles/` and `plans/sequences/`; create output directory `plans/generated/`.
- Out of scope: Python loader, compiler, CLI integration, SDL/RetroArch importers, wizard.
- Dependencies: MAP-01.
- Reasoning grade: High
- Effort grade: Low
- Recommended model: high-reasoning model
- Acceptance criteria: fixtures contain no absolute paths, private evidence paths, ROM paths, media references, frame paths, or crop paths; `gngb` sample maps canonical controls only to actions supported by `input_planner.VALID_ACTIONS`.

### MAP-03 - Mapping Profile Loader and Validation

- Objective: load and validate layered mapping YAML safely.
- Scope: add `apps/mame-harness/mapping_profiles.py`; validate profile kind, required fields, duplicate controls, invalid canonical controls, missing game action mappings, absolute paths, private path markers, and blocked public payload content.
- Out of scope: compilation, CLI, importers, wizard.
- Dependencies: MAP-02.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: high-reasoning model
- Acceptance criteria: tests cover valid samples, invalid `profile_type`, missing fields, duplicate controls, invalid controls, absolute paths, and private evidence markers with actionable errors.

### MAP-04 - Compatibility Compiler to Existing Input Plan

- Objective: compile validated layered profiles and input sequences into the existing YAML input plan format.
- Scope: add `apps/mame-harness/mapping_compiler.py`; resolve sequence controls through controller and game action profiles; emit `plan_name`, `game_id`, and `steps`; ensure output passes public path and payload guardrails.
- Out of scope: changes to `input_planner.py` unless a tiny compatibility helper is unavoidable; changes to MAME runner or Lua.
- Dependencies: MAP-03.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: high-reasoning model
- Acceptance criteria: sample profiles compile a smoke plan; unknown controls fail; missing mappings fail; generated YAML is parseable by `load_input_plan`; generated output contains only supported semantic actions.

### MAP-05 - CLI Commands `map validate` and `map compile`

- Objective: expose the mapping workflow through the existing harness CLI.
- Scope: extend `apps/mame-harness/cli.py` in the current argparse style; add `map validate --profile`; add `map compile --device --controller --game --sequence --out`; create safe parent directories for generated outputs.
- Out of scope: executing MAME, reading ROMs, private evidence access, importers, wizard.
- Dependencies: MAP-04.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: high-reasoning model
- Acceptance criteria: CLI tests cover valid validation, invalid validation, compilation output, output parseability, unsafe output rejection, and unchanged existing CLI behavior.

### MAP-06 - Contributor Documentation and First-PR Review

- Objective: document the implemented first-PR workflow and review it before moving to later automation.
- Scope: create `docs/mapping.md`; add a short README pointer; update agent guidance only if necessary; run first-PR review against the incoming review prompt.
- Out of scope: portability config, importers, wizard, boot calibration.
- Dependencies: MAP-05.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: capable reasoning model
- Acceptance criteria: docs explain the four layers, quickstart commands, public artifact constraints, deferred work, and the fact that MAME execution remains unchanged; review findings are resolved or explicitly deferred.

### MAP-07 - Portable Environment Config and Doctor

- Objective: reduce local-machine assumptions after the core mapping model is stable.
- Scope: add environment/config examples, replace hardcoded local paths where appropriate, add a doctor/preflight command or extension that checks MAME, ffmpeg, ROM path configuration, and writable private evidence directories; create `docs/bootstrap.md` explaining first-time contributor setup without exposing local machine paths.
- Out of scope: controller importers, wizard, boot calibration.
- Dependencies: MAP-06.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: capable reasoning model
- Acceptance criteria: local paths are documented as private config, not public artifacts; doctor output is redacted or path-safe; existing run/preflight behavior remains compatible; `docs/bootstrap.md` exists and explains setup without hardcoded machine paths.

### MAP-08 - SDL GameControllerDB Importer

- Objective: convert SDL controller mapping data into the repo's `device_profile` format.
- Scope: parser/importer module, CLI import command, round-trip tests, duplicate/unknown control validation.
- Out of scope: changing canonical controller vocabulary unless a real supported SDL control requires it and is documented.
- Dependencies: MAP-07.
- Reasoning grade: Medium
- Effort grade: Medium
- Recommended model: capable reasoning model
- Acceptance criteria: importer creates clean-room-safe device profiles; unsupported controls fail or are explicitly ignored with warnings; no raw local paths or private evidence references are written.

### MAP-09 - RetroArch Autoconfig Importer

- Objective: convert RetroArch autoconfig files into the repo's `device_profile` format.
- Scope: parser/importer module, CLI import command, tests against minimal fixtures.
- Out of scope: adopting RetroArch as the execution backend.
- Dependencies: MAP-07.
- Reasoning grade: Medium
- Effort grade: Medium
- Recommended model: capable reasoning model
- Acceptance criteria: importer produces valid device profiles; unsupported fields do not leak paths or private config; generated profiles pass the same validation as manual profiles.

### MAP-10 - CLI Wizard `map init`

- Objective: guide first-use manual mapping after the profile model and importers are stable.
- Scope: interactive CLI flow for choosing device type, binding required controls, detecting duplicates, validating output, and saving a device profile.
- Out of scope: GUI, TUI framework, MAME execution, screenshots, controller telemetry capture from private evidence.
- Dependencies: MAP-07; may optionally depend on MAP-08 or MAP-09 for presets.
- Reasoning grade: Medium
- Effort grade: Medium
- Recommended model: capable reasoning model
- Acceptance criteria: wizard writes only public-safe YAML profiles; duplicate bindings fail; required controls are enforced; generated profiles compile through MAP-05.

### MAP-11 - Boot Calibration Spike

- Objective: explore reducing fragile hand-authored boot frame timings without weakening clean-room boundaries.
- Scope: design a calibration command that stores only abstract timing/state metadata publicly while keeping video, screenshots, and raw observations private.
- Out of scope: automatic screen-state segmentation as a production feature; public screenshots or pixel comparisons; source-specific level scripting.
- Dependencies: MAP-06; stronger recommendation to wait until MAP-07 is complete.
- Reasoning grade: High
- Effort grade: High
- Recommended model: high-reasoning model
- Acceptance criteria: spike document defines allowed public calibration outputs, forbidden evidence outputs, validation strategy, and whether a future implementation needs another ADR.

## First PR Definition Of Done

The first implementation PR is complete only when MAP-00 through MAP-06 are complete and all of the following are true:

- existing tests pass
- new tests pass
- sample layered profiles compile into a generated input plan
- generated input plan is parseable by the existing input planner
- CLI supports `map validate` and `map compile`
- documentation explains the mapping layers and clean-room limits
- public artifacts contain no ROMs, screenshots, audio, sprites, videos, frame dumps, crop paths, absolute local paths, or private evidence paths
- MAME execution path remains unchanged

## Later Phase Exit Criteria

MAP-07 is complete when a contributor can verify local setup through config/doctor tooling without exposing local machine paths in public artifacts.

MAP-08 through MAP-10 are complete when a contributor can import or create a device profile without manually authoring raw YAML and still compile through the same first-PR compiler.

MAP-11 is complete when boot calibration has a documented, clean-room-safe design boundary and a clear decision on whether to implement it.

## Reference Documents

- Current task file: `docs/new reqs/blackbox_mame_mapping_handoff_updated/README.md`
- Parent plan file: `docs/plans/layered_input_mapping_plan.md`
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `apps/mame-harness/README.md`
- `docs/plans/gng_source_integration_plan.md`
- `docs/new reqs/blackbox_mame_mapping_handoff_updated/EXECUTION_ORDER.md`
- `docs/new reqs/blackbox_mame_mapping_handoff_updated/docs/ADR-0001-layered-input-mapping.md`
- `docs/new reqs/blackbox_mame_mapping_handoff_updated/prompts/00_repository_orientation.md`
- `docs/new reqs/blackbox_mame_mapping_handoff_updated/prompts/01_create_schemas_and_sample_profiles.md`
- `docs/new reqs/blackbox_mame_mapping_handoff_updated/prompts/02_add_mapping_profile_loader_and_validation.md`
- `docs/new reqs/blackbox_mame_mapping_handoff_updated/prompts/03_add_compiler_to_existing_input_plan.md`
- `docs/new reqs/blackbox_mame_mapping_handoff_updated/prompts/04_add_cli_map_validate_and_compile.md`
- `docs/new reqs/blackbox_mame_mapping_handoff_updated/prompts/05_documentation_update.md`
- `docs/new reqs/blackbox_mame_mapping_handoff_updated/prompts/11_first_pr_review_prompt.md`
- `docs/adr/ADR-001-clean-room-layered-architecture.md`
- `docs/adr/ADR-002-private-evidence-uri-scheme.md`
- `docs/adr/ADR-003-public-output-blocklist.md`
- `docs/adr/ADR-004-mame-runner-structured-results.md`
- `docs/adr/ADR-005-source-profile-pattern.md`
- `docs/adr/ADR-009-input-plan-determinism.md`
- `docs/obsidian/00 - Project Overview.md`
- `docs/obsidian/Guardrails.md`
- `docs/obsidian/Private vs Public Boundary.md`
- `docs/obsidian/Input Plan.md`
- `docs/obsidian/MAME Runner.md`
- `docs/obsidian/Source Profile.md`
- `docs/obsidian/Preflight.md`
- `apps/mame-harness/input_planner.py`
- `apps/mame-harness/cli.py`
- `apps/mame-harness/guardrails.py`
- `apps/mame-harness/metadata_writer.py`
- `apps/mame-harness/source_profiles.py`
- `apps/mame-harness/preflight.py`
- `apps/mame-harness/mame_runner.py`
- `scripts/mame_autoboot.lua`
- `packages/schemas/input_plan.schema.json`
- `apps/mame-harness/tests/test_input_planner.py`
- `apps/mame-harness/tests/test_cli.py`
- `apps/mame-harness/tests/test_public_artifact_guardrails.py`

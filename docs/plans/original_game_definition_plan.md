# Original Game Definition Plan

## Purpose

Define the new public phase after T10/T11 that turns clean-room abstract mechanics into a clearly original mobile game direction. This plan is documentation-only until its tasks are executed. It does not implement code, schemas, specs, or React Native changes.

## Phase Objective

Deliver a public game-definition layer for **Signal Garden**, a working original product direction that uses abstract mechanics as input while avoiding source names, levels, visual identity, encounter order, stage framing, and expressive structure.

T10 and T11 remain the clean-room demo boundary:

- T10 produces calibrated public abstract mechanics and traces.
- T11 proves the RN prototype can consume public data safely.
- T12 defines what original game the prototype should become.

RN must not advance from clean-room mechanics playback into product-like implementation until T12 defines the public game direction, scenario transformation policy, and validation gates.

## Scope Boundary

### In Scope

- gameplay pillars
- product direction
- encounter grammar
- scene recipe abstraction
- mechanics-to-scenario transformation rules
- progression and difficulty model
- theme translation guidance for new original assets
- originality and design-intent validation gates
- task-level planning and canonical documentation

### Out of Scope

- ROM outputs
- screenshots, videos, audio, save states, crops, or sprites
- image-to-image derivation
- exact source level recreation
- clone-specific implementation
- RN production implementation before the phase is executed
- executable schemas or specs as part of this documentation pass

## Dependency Order

The tasks below are ordered by execution dependency. Do not start a task if any declared dependency is incomplete.

### T12.0 - Original Game Definition ADRs and Phase Plan

- Task file: [T12.0-adrs-and-phase-plan.md](../tasks/original_game_definition/T12.0-adrs-and-phase-plan.md)
- Objective: document the new architecture before implementation.
- Scope: verify ADR-010, ADR-011; author `signal_garden_phase_plan.md`; update all ADR indexes.
- Out of scope: schemas, RN implementation, final product polish.
- Dependencies: T11.5 complete.
- Reasoning grade: High
- Effort grade: M
- Recommended model: Sonnet
- Acceptance criteria: ADR indexes are updated; `signal_garden_phase_plan.md` exists with dependency order, constraints, and known risks; no new public artifact permits private evidence.

### T12.1 - Public Mechanics Capability Review

- Task file: [T12.1-public-mechanics-capability-review.md](../tasks/original_game_definition/T12.1-public-mechanics-capability-review.md)
- Objective: classify which abstract mechanics can safely inform Signal Garden and which carry clone risk.
- Scope: produce `specs/game/gng_mechanics_affordance_map.yaml` with safe affordances, clone risks, and design freedom notes.
- Out of scope: final encounters or theme details.
- Dependencies: T12.0, T10.4, T11.
- Reasoning grade: High
- Effort grade: S
- Recommended model: Sonnet
- Acceptance criteria: every mechanic in `gng_abstract_mechanics.yaml` has an entry; no entry encodes source names or exact encounter timing; affordance map guides T12.2 without further design decisions.

### T12.2 - Product Direction and Gameplay Pillars

- Task file: [T12.2-product-direction-and-gameplay-pillars.md](../tasks/original_game_definition/T12.2-product-direction-and-gameplay-pillars.md)
- Objective: define the original game concept for Signal Garden.
- Scope: author `specs/game/signal_garden_design_brief.yaml` with pillars, core loop, player verbs, tone, naming rules, and anti-source constraints.
- Out of scope: asset files, final branding, monetization, full narrative.
- Dependencies: T12.1.
- Reasoning grade: High
- Effort grade: M
- Recommended model: Sonnet
- Acceptance criteria: brief has all required fields; contains no source names, stage names, enemy names, or visual callbacks; specific enough to guide T12.3 without additional design decisions.

### T12.3 - Encounter Grammar Schema

- Task file: [T12.3-encounter-grammar-schema.md](../tasks/original_game_definition/T12.3-encounter-grammar-schema.md)
- Objective: define how abstract roles combine into original encounter patterns.
- Scope: author `packages/schemas/encounter_grammar.schema.json` and `specs/encounters/encounter_grammar.yaml` with ≥ 5 patterns, each with a required divergence constraint.
- Out of scope: exact source encounter reproduction, real asset generation, procedural generation engine.
- Dependencies: T12.2.
- Reasoning grade: High
- Effort grade: M
- Recommended model: Sonnet
- Acceptance criteria: schema validates all examples; every pattern has a divergence constraint; no source names in role labels or pattern names.

### T12.4 - Scene Recipe and Transformation Rules

- Task file: [T12.4-scene-recipe-and-transformation-rules.md](../tasks/original_game_definition/T12.4-scene-recipe-and-transformation-rules.md)
- Objective: define how observed abstract patterns become newly authored Signal Garden scenes.
- Scope: author `packages/schemas/scene_recipe.schema.json`, `specs/transforms/mechanics_to_scene_rules.yaml`, and `specs/scenes/signal_garden_scene_recipes.yaml` with ≥ 3 recipes.
- Out of scope: copying source levels, using screenshots, using exact spawn coordinates, implementing RN rendering.
- Dependencies: T12.3.
- Reasoning grade: High
- Effort grade: M
- Recommended model: Sonnet
- Acceptance criteria: ≥ 3 recipes exist; each has a non-empty divergence note; no recipe encodes source stage structure or pixel coordinates; guardrails pass.

### T12.5 - Progression and Difficulty Model

- Task file: [T12.5-progression-and-difficulty-model.md](../tasks/original_game_definition/T12.5-progression-and-difficulty-model.md)
- Objective: define how Signal Garden scenes ramp into a playable vertical slice.
- Scope: author `packages/schemas/progression.schema.json` and `specs/progression/signal_garden_progression.yaml` with difficulty bands and scene sequence.
- Out of scope: full campaign, source stage parity, boss recreation.
- Dependencies: T12.4, T12.2.
- Reasoning grade: Medium
- Effort grade: M
- Recommended model: Sonnet
- Acceptance criteria: `scene_sequence` references only T12.4 recipe IDs; no source stage order or pacing labels; tuning ranges present.

### T12.6 - Theme Translation and Asset Recipe Enrichment

- Task file: [T12.6-theme-translation-and-asset-recipe-enrichment.md](../tasks/original_game_definition/T12.6-theme-translation-and-asset-recipe-enrichment.md)
- Objective: align asset recipes with Signal Garden product direction.
- Scope: extend public recipes with `signal_garden_role`, `shape_notes`, ≥ 3 varied `theme_variants`; author new recipes for any T12.3 roles lacking coverage.
- Out of scope: generated images, sprite creation, image-to-image workflows.
- Dependencies: T12.2, T12.3, T12.5.
- Reasoning grade: High
- Effort grade: M
- Recommended model: Sonnet
- Acceptance criteria: every encounter role has a recipe; all five ADR-007 prohibited similarity rules present; `human_review_required: true` on every recipe; guardrails pass.

### T12.7 - RN Original Vertical Slice Hookup

- Task file: [T12.7-rn-original-vertical-slice-hookup.md](../tasks/original_game_definition/T12.7-rn-original-vertical-slice-hookup.md)
- Objective: turn the RN prototype from mechanics playback into a playable Signal Garden scenario.
- Scope: implement recipe loader, progression loader, scene builder from recipes, one complete playable scene with calibrated physics and placeholder geometry.
- Out of scope: production art, app-store polish, source-faithful stages.
- Dependencies: T12.4, T12.5, T12.6, T11.
- Reasoning grade: High
- Effort grade: L
- Recommended model: Sonnet
- Acceptance criteria: one scene playable end-to-end; no hardcoded positions remain; import graph contains no private paths; all tests pass.

### T12.8 - Originality and Design-Intent Validation Gate

- Task file: [T12.8-originality-and-design-intent-validation-gate.md](../tasks/original_game_definition/T12.8-originality-and-design-intent-validation-gate.md)
- Objective: verify the vertical slice is clean-room safe and design-complete.
- Scope: author `packages/validation/tests/test_signal_garden_originality.py` covering six validation categories; populate validation evidence.
- Out of scope: pixel comparison, screenshot tests against source, automated legal determination.
- Dependencies: T12.7.
- Reasoning grade: High
- Effort grade: M
- Recommended model: Sonnet
- Acceptance criteria: all six validation categories pass; no T12 artifact fails a guardrail; full test suites green.

## Proposed Public Artifacts

These artifacts are recommended for future T12 execution. They are not created by this documentation pass.

| Tentative path | Task | Purpose | Consumer | Clean-room safety |
|----------------|------|---------|----------|-------------------|
| `specs/game/gng_mechanics_affordance_map.yaml` | T12.1 | safe affordances, clone risks, design freedom per mechanic | T12.2 brief, planning | abstract affordances only |
| `specs/game/signal_garden_design_brief.yaml` | T12.2 | product identity, gameplay pillars, core loop, naming/theme constraints | RN prototype, asset generation, planning | original theme and abstract design intent only |
| `specs/encounters/encounter_grammar.yaml` | T12.3 | role-based encounter composition rules | RN prototype, validation, planning | abstract roles and timing bands only |
| `specs/scenes/signal_garden_scene_recipes.yaml` | T12.4 | original scene recipes for the vertical slice | RN prototype, validation | newly authored scenes with divergence notes |
| `specs/transforms/mechanics_to_scene_rules.yaml` | T12.4 | mechanics-to-scenario transformation policy | validation, planning | encodes required divergence, not source expressive content |
| `specs/progression/signal_garden_progression.yaml` | T12.5 | difficulty bands and scene sequence | RN prototype, validation | original progression over abstract recipes |
| `packages/schemas/encounter_grammar.schema.json` | T12.3 | validate encounter grammar | validation, planning | schema fields are abstract |
| `packages/schemas/scene_recipe.schema.json` | T12.4 | validate scene recipes | validation, planning | schema fields are abstract |
| `packages/schemas/progression.schema.json` | T12.5 | validate progression model | validation, planning | schema fields are abstract |

## Task Index

- [T12.0 - ADRs and Phase Plan](../tasks/original_game_definition/T12.0-adrs-and-phase-plan.md) 🔲
- [T12.1 - Public Mechanics Capability Review](../tasks/original_game_definition/T12.1-public-mechanics-capability-review.md) 🔲
- [T12.2 - Product Direction and Gameplay Pillars](../tasks/original_game_definition/T12.2-product-direction-and-gameplay-pillars.md) 🔲
- [T12.3 - Encounter Grammar Schema](../tasks/original_game_definition/T12.3-encounter-grammar-schema.md) 🔲
- [T12.4 - Scene Recipe and Transformation Rules](../tasks/original_game_definition/T12.4-scene-recipe-and-transformation-rules.md) 🔲
- [T12.5 - Progression and Difficulty Model](../tasks/original_game_definition/T12.5-progression-and-difficulty-model.md) 🔲
- [T12.6 - Theme Translation and Asset Recipe Enrichment](../tasks/original_game_definition/T12.6-theme-translation-and-asset-recipe-enrichment.md) 🔲
- [T12.7 - RN Original Vertical Slice Hookup](../tasks/original_game_definition/T12.7-rn-original-vertical-slice-hookup.md) 🔲
- [T12.8 - Originality and Design-Intent Validation Gate](../tasks/original_game_definition/T12.8-originality-and-design-intent-validation-gate.md) 🔲

## Reference Documents

- [T11-rn-prototype-hookup.md](../tasks/gng_source_integration/T11-rn-prototype-hookup.md)
- [gng_source_integration_plan.md](./gng_source_integration_plan.md)
- [docs/tasks/original_game_definition/README.md](../tasks/original_game_definition/README.md)
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `docs/adr/README.md`
- `docs/obsidian/00 - Project Overview.md`
- `docs/obsidian/GNG Integration Plan.md`
- `docs/obsidian/React Native Prototype.md`
- `docs/obsidian/Behavioral Validation.md`
- `docs/obsidian/Asset Factory.md`
- `docs/obsidian/Public Original Game Definition Layer.md`
- `docs/adr/ADR-001-clean-room-layered-architecture.md`
- `docs/adr/ADR-003-public-output-blocklist.md`
- `docs/adr/ADR-007-asset-recipe-originality-contract.md`
- `docs/adr/ADR-008-behavioral-validation-no-pixel-comparison.md`
- `docs/adr/ADR-010-public-original-game-definition-layer.md`
- `docs/adr/ADR-011-mechanics-to-scenario-transformation-originality-validation.md`
- `specs/mechanics/gng_abstract_mechanics.yaml`
- `packages/schemas/gng_mechanics.schema.json`
- `packages/schemas/trace.schema.json`

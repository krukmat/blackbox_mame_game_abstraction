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

- Objective: document the new architecture before implementation.
- Scope: ADR-010, ADR-011, Obsidian summaries, and this parent plan.
- Out of scope: schemas, RN implementation, final product polish.
- Dependencies: T10/T11 contracts as planning inputs.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: GPT-5.5
- Acceptance criteria: ADR indexes are updated; the plan includes dependency order and reference documents; no new public artifact permits private evidence.

### T12.1 - Public Mechanics Capability Review

- Objective: classify which T10/T11 mechanics can safely inform the new game.
- Scope: map locomotion, jump, projectile, gravity, and entity events to reusable design affordances and forbidden clone risks.
- Out of scope: final encounters or theme details.
- Dependencies: T12.0, T10.4, T11.
- Reasoning grade: High
- Effort grade: Low
- Recommended model: GPT-5.5
- Acceptance criteria: review names only abstract mechanics and explicitly excludes source level structure, names, enemies, visual framing, and exact encounter timing.

### T12.2 - Product Direction and Gameplay Pillars

- Objective: define the original game concept.
- Scope: create a public design brief for Signal Garden with audience, pillars, core loop, player verbs, tone, naming rules, and anti-source identity constraints.
- Out of scope: asset files, final branding, monetization, full narrative.
- Dependencies: T12.1.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: GPT-5.5
- Acceptance criteria: brief defines committed jumps, readable timing pressure, pulse-based interaction, compact mobile scenes, and signal-garden identity; contains no source names, stage names, enemy names, or visual callbacks.

### T12.3 - Encounter Grammar Schema

- Objective: define how abstract roles combine into original encounter patterns.
- Scope: add a schema and example grammar for traversal beats, patrollers, airborne pressure, hazards, pulse targets, safe zones, and timing windows.
- Out of scope: exact source encounter reproduction, real asset generation, procedural generation engine.
- Dependencies: T12.2.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: GPT-5.5
- Acceptance criteria: grammar validates role-based YAML/JSON; examples are source-neutral; every encounter rule includes at least one required divergence constraint.

### T12.4 - Scene Recipe and Transformation Rules

- Objective: define how observed abstract patterns become newly authored scenes.
- Scope: create scene recipe schema plus rules such as scale normalization, role substitution, timing-band reuse, layout re-authoring, order variation, and no coordinate/sequence copying.
- Out of scope: copying source levels, using screenshots, using exact spawn coordinates, implementing RN rendering.
- Dependencies: T12.3.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: GPT-5.5
- Acceptance criteria: at least three clean-room scene recipes exist; each cites abstract mechanic inputs only; guardrails pass; no recipe encodes source stage structure or exact frame/path evidence.

### T12.5 - Progression and Difficulty Model

- Objective: define how scenes ramp into a playable vertical slice.
- Scope: specify difficulty bands, encounter sequencing, failure/retry assumptions, timing pressure curves, and mobile session length.
- Out of scope: full campaign, source stage parity, boss recreation.
- Dependencies: T12.4.
- Reasoning grade: Medium
- Effort grade: Medium
- Recommended model: GPT-5.4
- Acceptance criteria: progression model orders scenes by abstract skill demand; includes tuning ranges; validates against scene recipes; avoids source-specific stage order or pacing labels.

### T12.6 - Theme Translation and Asset Recipe Enrichment

- Objective: align asset recipes with the new product direction.
- Scope: extend public recipes with Signal Garden role language, shape/readability needs, and varied theme prompts while preserving ADR-007 prohibited similarity rules and `human_review_required: true`.
- Out of scope: generated images, sprite creation, image-to-image workflows.
- Dependencies: T12.2, T12.3, T12.5.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: GPT-5.5
- Acceptance criteria: every recipe remains abstract, includes all five prohibited similarity rules, uses no original image paths, and maps roles to new identity terms rather than source identity terms.

### T12.7 - RN Original Vertical Slice Hookup

- Objective: turn the RN prototype from mechanics playback into an original scenario prototype.
- Scope: make RN consume the public design brief, encounter grammar, scene recipes, progression model, and enriched asset recipes; implement one playable Signal Garden vertical slice with placeholder or original-safe geometry.
- Out of scope: production art, app-store polish, source-faithful stages.
- Dependencies: T12.4, T12.5, T12.6, T11.
- Reasoning grade: High
- Effort grade: High
- Recommended model: GPT-5.5
- Acceptance criteria: RN imports only public specs; no MAME/private dependency exists; first playable scene follows T12 recipes; presentation is independently themed and not source-framed.

### T12.8 - Originality and Design-Intent Validation Gate

- Objective: verify the vertical slice is clean-room safe and design-complete.
- Scope: add validation cases for mechanics compliance, encounter grammar conformance, scene divergence, naming/theme safety, and public-output guardrails.
- Out of scope: pixel comparison, screenshot tests against source, automated legal determination.
- Dependencies: T12.7.
- Reasoning grade: High
- Effort grade: Medium
- Recommended model: GPT-5.5
- Acceptance criteria: tests reject private paths, media extensions, source names, source-like scene identifiers, and missing originality guards; trace validation remains abstract per ADR-008.

## Proposed Public Artifacts

These artifacts are recommended for future T12 execution. They are not created by this documentation pass.

| Tentative path | Purpose | Consumer | Clean-room safety |
|----------------|---------|----------|-------------------|
| `specs/game/signal_garden_design_brief.yaml` | product identity, gameplay pillars, core loop, naming/theme constraints | RN prototype, asset generation, planning | original theme and abstract design intent only |
| `specs/encounters/encounter_grammar.yaml` | role-based encounter composition rules | RN prototype, validation, planning | abstract roles and timing bands only |
| `specs/scenes/signal_garden_scene_recipes.yaml` | original scene recipes for the vertical slice | RN prototype, validation | newly authored scenes with divergence notes |
| `specs/transforms/mechanics_to_scene_rules.yaml` | mechanics-to-scenario transformation policy | validation, planning | encodes required divergence, not source expressive content |
| `specs/progression/signal_garden_progression.yaml` | difficulty bands and scene sequence | RN prototype, validation | original progression over abstract recipes |
| `packages/schemas/game_design.schema.json` | validate game design brief | validation, planning | schema fields are abstract |
| `packages/schemas/encounter_grammar.schema.json` | validate encounter grammar | validation, planning | schema fields are abstract |
| `packages/schemas/scene_recipe.schema.json` | validate scene recipes | validation, planning | schema fields are abstract |
| `packages/schemas/progression.schema.json` | validate progression model | validation, planning | schema fields are abstract |

## Reference documents

- Current task file: `docs/tasks/gng_source_integration/T11-rn-prototype-hookup.md`
- Parent plan file: `docs/plans/gng_source_integration_plan.md`
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `docs/adr/README.md`
- `docs/tasks/gng_source_integration/README.md`
- `docs/tasks/gng_source_integration/T09-first-abstract-observation-schema.md`
- `docs/tasks/gng_source_integration/T10-private-evidence-to-public-abstract-spec-transformation.md`
- `docs/obsidian/00 - Project Overview.md`
- `docs/obsidian/GNG Integration Plan.md`
- `docs/obsidian/React Native Prototype.md`
- `docs/obsidian/Behavioral Validation.md`
- `docs/obsidian/Asset Factory.md`
- `docs/obsidian/Private vs Public Boundary.md`
- `docs/obsidian/Guardrails.md`
- `docs/adr/ADR-001-clean-room-layered-architecture.md`
- `docs/adr/ADR-003-public-output-blocklist.md`
- `docs/adr/ADR-006-vision-layer-numeric-only-output.md`
- `docs/adr/ADR-007-asset-recipe-originality-contract.md`
- `docs/adr/ADR-008-behavioral-validation-no-pixel-comparison.md`
- `docs/adr/ADR-009-input-plan-determinism.md`
- `docs/adr/ADR-010-public-original-game-definition-layer.md`
- `docs/adr/ADR-011-mechanics-to-scenario-transformation-originality-validation.md`
- `specs/mechanics/gng_abstract_mechanics.yaml`
- `packages/schemas/gng_mechanics.schema.json`
- `packages/schemas/trace.schema.json`

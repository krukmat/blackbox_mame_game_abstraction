# Original Game Definition Tasks

This directory contains the execution task files for the T12 Original Game Definition phase (Signal Garden).

Parent plan: [Original Game Definition Plan](../../plans/original_game_definition_plan.md)

## Execution Order

1. [`T12.0`](./T12.0-adrs-and-phase-plan.md) — Original Game Definition ADRs and Phase Plan
2. [`T12.1`](./T12.1-public-mechanics-capability-review.md) — Public Mechanics Capability Review
3. [`T12.2`](./T12.2-product-direction-and-gameplay-pillars.md) — Product Direction and Gameplay Pillars
4. [`T12.3`](./T12.3-encounter-grammar-schema.md) — Encounter Grammar Schema
5. [`T12.4`](./T12.4-scene-recipe-and-transformation-rules.md) — Scene Recipe and Transformation Rules
6. [`T12.5`](./T12.5-progression-and-difficulty-model.md) — Progression and Difficulty Model
7. [`T12.6`](./T12.6-theme-translation-and-asset-recipe-enrichment.md) — Theme Translation and Asset Recipe Enrichment
8. [`T12.7`](./T12.7-rn-original-vertical-slice-hookup.md) — RN Original Vertical Slice Hookup
9. [`T12.8`](./T12.8-originality-and-design-intent-validation-gate.md) — Originality and Design-Intent Validation Gate

## Dependency Graph

```
T12.0
  ↓
T12.1
  ↓
T12.2
  ↓
T12.3
  ↓
T12.4 ──→ T12.7
T12.5 ──↗    ↓
T12.6 ───→ T12.8
```

T12.3, T12.4, T12.5 are sequential.
T12.6 depends on T12.2, T12.3, and T12.5.
T12.7 depends on T12.4, T12.5, T12.6, and T11.
T12.8 depends on T12.7.

## Dependency Rule

Do not start a task if any of its declared dependencies in the task file are incomplete.

## Phase Boundary

This phase starts only after T11.5 (clean-room verification) has passed. T11 proves the RN prototype can consume public data safely — T12 defines what original game it becomes.

T12 does not authorize clone-specific implementation. All outputs must remain abstract or independently authored. No task may introduce ROMs, screenshots, videos, original sprites, audio captures, save states, frame paths, crop paths, exact source levels, source names, or source visual identity.

# Original Game Definition Tasks

This directory contains the task index for the T12 Original Game Definition phase.

Parent plan: [Original Game Definition Plan](../../plans/original_game_definition_plan.md)

## Execution Order

1. `T12.0` - Original Game Definition ADRs and Phase Plan
2. `T12.1` - Public Mechanics Capability Review
3. `T12.2` - Product Direction and Gameplay Pillars
4. `T12.3` - Encounter Grammar Schema
5. `T12.4` - Scene Recipe and Transformation Rules
6. `T12.5` - Progression and Difficulty Model
7. `T12.6` - Theme Translation and Asset Recipe Enrichment
8. `T12.7` - RN Original Vertical Slice Hookup
9. `T12.8` - Originality and Design-Intent Validation Gate

## Dependency Rule

Do not start a task if any of its declared dependencies in the parent plan are incomplete.

## Phase Boundary

This phase starts only after T10 has produced public calibrated abstract mechanics and T11 has proven the RN prototype can consume public data safely.

T12 does not authorize clone-specific implementation. All outputs must remain abstract or independently authored, and no task may introduce ROMs, screenshots, videos, original sprites, audio captures, save states, frame paths, crop paths, exact source levels, source names, or source visual identity.

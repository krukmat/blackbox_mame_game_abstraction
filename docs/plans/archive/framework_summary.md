# blackbox_mame_game_abstraction — Summary

## Objective

Explore a game available only through MAME, capture its observable behavior, infer abstract gameplay rules, and use those abstractions to build a new independent React Native game.

## Core pipeline

```text
MAME game
  → automated observation
  → evidence dataset
  → behavior inference
  → abstract mechanics spec
  → new theme + new assets
  → independent React Native implementation
  → behavioral validation against MAME
```

## Key distinction

This is not a MAME porting project.

It is a black-box reconstruction and abstraction project.

The system should not copy original code, original assets, original audio, names, characters, levels or presentation.

## Main phases

```text
Phase 0 — Legal/scope guardrails
Phase 1 — MAME automation harness
Phase 2 — Dataset capture: frames + inputs + states
Phase 3 — Visual entity detection
Phase 4 — Game state machine inference
Phase 5 — Physics/collision/scoring inference
Phase 6 — Clean-room functional spec
Phase 7 — React Native implementation
Phase 8 — Golden-master validation against MAME
```

## Recommended architecture

```text
apps/
  mame-harness/
  rn-prototype/

packages/
  schemas/
  vision/
  inference/
  asset-factory/
  validation/

docs/
  architecture.md
  legal_guardrails.md
  exploration_strategy.md
  clean_room_process.md
  react_native_implementation_plan.md

specs/
  mechanics/
  entities/
  levels/
  assets/
  validation/

evidence/
  private/
```

## Asset principle

Do not extract sprites as reusable output.

Instead:

```text
detect visual candidates internally
derive redacted metadata
infer gameplay role
generate abstract asset recipes
create new original assets
validate originality
```

## Validation principle

Do not validate pixel-perfect similarity.

Validate:

```text
movement similarity
collision outcome similarity
event sequence similarity
state transition similarity
scoring rule similarity
pacing similarity
```

Also validate:

```text
visual dissimilarity
theme dissimilarity
naming dissimilarity
asset originality
```

## Implemented baseline

- Phase 1: deterministic MAME command builder, capture-session provisioning, input-plan expansion, and save-state metadata registry.
- Phase 3: pure-Python frame manifest and differ placeholders that emit only redacted numeric motion stats.
- Phase 5: asset recipe generation from redacted entity candidates only.
- Phase 6: deterministic TypeScript prototype scaffold for the independent mobile implementation.
- Phase 7: behavioral trace diffing and clean-room validation reports.

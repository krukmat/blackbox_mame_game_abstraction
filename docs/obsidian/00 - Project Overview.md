# blackbox_mame_game_abstraction — Project Overview

## Mission

Build a clean-room framework that observes a game running in MAME, extracts abstract mechanics through private evidence capture, and produces an independent original mobile game in React Native — without ever cloning, porting, or reusing copyrighted expressive content.

## The Core Pipeline

```
MAME observation (private)
  → private evidence (frames, video, logs) — gitignored, never public
  → redacted entity candidates (numeric only, no image paths)
  → abstract asset recipes (with anti-similarity rules)
  → public original game definition (pillars, encounter grammar, scene recipes)
  → new original theme + art
  → React Native game (new assets, new identity)
```

## The Hard Rule

> Observable behavior → abstract spec → new assets → new theme → independent implementation

Never:

> Original sprite → modified sprite → reused asset

## Key Concepts

- [[Visual Architecture]] — Five Mermaid diagrams covering pipeline, layers, guardrails, data flow, and task status
- [[Private vs Public Boundary]] — the most important architectural decision in the project
- [[Guardrails]] — how the boundary is enforced in code
- [[Source Profile]] — canonical game observation configuration
- [[MAME Runner]] — deterministic run execution and preflight
- [[Input Plan]] — reproducible frame-level action sequences
- [[Vision Layer]] — private-only frame analysis → numeric entity candidates
- [[Asset Factory]] — abstract entity candidates → original asset recipes
- [[Behavioral Validation]] — trace-based behavior comparison, no pixel matching
- [[React Native Prototype]] — spec-driven TypeScript game engine
- [[Public Original Game Definition Layer]] — T12 bridge from abstract mechanics to an original game direction
- [[Original Game Definition Phase]] — T12 task order and phase boundary

## Repository Layout

```
apps/
  mame-harness/      CLI, runner, capture, input planning, metadata writer
  rn-prototype/      TypeScript game engine (consumes public specs only)
packages/
  vision/            Private frame manifest + motion analysis
  asset-factory/     Abstract recipe generation
  validation/        Behavioral diff + reports
  schemas/           JSON schemas for all public artifacts
  inference/         (deferred) mechanics inference layer
docs/
  adr/               Architecture Decision Records
  obsidian/          This vault
  plans/             Feature-level implementation plans
  tasks/             Task-level implementation documents
plans/               Input plan YAML files
specs/               Public output artifacts (tracked)
  game/              (planned T12) original game design brief
  encounters/        (planned T12) role-based encounter grammar
  scenes/            (planned T12) original scene recipes
  transforms/        (planned T12) mechanics-to-scenario transformation rules
  progression/       (planned T12) difficulty and scene sequence
evidence/private/    Private evidence (gitignored)
```

## ADR Index

| Decision | Why it matters |
|----------|---------------|
| [[ADR-001 Clean-Room Layered Architecture]] | Four-layer separation with enforcement at write time |
| [[ADR-002 Private URI Scheme]] | How evidence sessions are referenced without leaking paths |
| [[ADR-003 Public Output Blocklist]] | Three-layer blocklist: extension, directory, path marker |
| [[ADR-004 MAME Runner Structured Results]] | Typed result objects replace exception-driven flow |
| [[ADR-005 Source Profile Pattern]] | Canonical game config (handles gng/gngb driver disambiguation) |
| [[ADR-006 Vision Layer Numeric Output]] | Vision layer never emits paths, only numbers |
| [[ADR-007 Asset Recipe Originality Contract]] | Anti-similarity rules and human review gate in every recipe |
| [[ADR-008 Behavioral Validation No Pixels]] | Trace comparison instead of screenshot comparison |
| [[ADR-009 Input Plan Determinism]] | YAML-defined reproducible frame sequences |
| [[ADR-010 Public Original Game Definition Layer]] | Public layer for pillars, product direction, encounter grammar, scene recipes, and progression |
| [[ADR-011 Mechanics-to-Scenario Transformation and Originality Validation]] | Rules for transforming abstract mechanics into original scenarios without copying expressive structure |
| [[ADR-012 Entity Signature-Based Player Identification]] | Geometric signature (height, center_y) to isolate the player entity from frame diffs; multi-region FrameDiffer; ArthurTracker |

## Current Phase

**GNG Source Integration** (T01–T11) — see [[GNG Integration Plan]].

Tasks T01–T07 are implemented (Python normalization, source profile, preflight, runner hardening, redaction, tests, CLI integration). T08–T11 (real capture, abstract schema, transformation, RN hookup) are planned.

**Original Game Definition** (T12) is the documented next phase after T10/T11. It defines Signal Garden as a working original direction and adds a public game-definition layer before RN moves beyond clean-room mechanics playback. See [[Original Game Definition Phase]], [[Public Original Game Definition Layer]], and `docs/plans/original_game_definition_plan.md`.

## Legal Status

- No ROMs committed.
- No screenshots, video, or audio committed.
- `evidence/private/` is gitignored.
- All public outputs pass `ensure_no_private_paths` at write time.
- Asset recipes require `human_review_required: true` before any generated art is accepted.

See [[Legal Guardrails]] for the full list of constraints.

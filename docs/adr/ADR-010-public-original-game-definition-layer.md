# ADR-010 — Public Original Game Definition Layer

## Status
Accepted

## Date
2026-05-14

## Context

The current clean-room pipeline can observe a source game privately, extract abstract mechanics, produce public traces and asset recipes, and feed a React Native prototype. That is enough to demonstrate a safe technical flow, but it does not yet answer the product question: what original game is being made from the abstract behavior?

Without a deliberate public game-definition layer, the React Native prototype can drift into one of two bad outcomes:

- a mechanics playback demo with no independent product direction
- a clone-shaped implementation that indirectly follows the source game's encounter structure, level logic, visual framing, or identity

The project needs a public layer between calibrated mechanics and runtime implementation. That layer must define original gameplay intent while consuming only clean-room-safe artifacts.

## Decision

Introduce a **Public Original Game Definition Layer** after T10/T11 and before any production-like React Native prototype work.

This layer is public and may consume only:

- abstract mechanics specs
- abstract traces
- entity archetypes
- asset recipes with the ADR-007 originality contract
- validation reports that contain no private paths or media references

It must define:

- gameplay pillars
- product direction and working identity
- player verbs and core loop
- encounter grammar
- scene or level recipe abstractions
- progression and difficulty model
- theme translation rules for new original assets
- constraints that prevent clone-specific implementation

The first working product direction is **Signal Garden**: an original mobile arcade-action prototype about navigating readable signal fields, committed jumps, timing pressure, and pulse-like interactions. This name is a working direction for public planning only. It is intentionally separate from the observed source game's names, characters, stage identity, visual framing, and expressive themes.

The layer must not contain:

- ROM references
- frame, crop, screenshot, video, audio, or save-state references
- original sprite descriptions
- original enemy, player, weapon, or stage names
- exact source level structure
- exact source encounter order
- source visual framing or product identity

## Consequences

**Positive**

- The project can move from clean-room mechanics extraction to an actual original game concept without relying on implicit design decisions.
- React Native work after T11 has a product/design contract to consume instead of interpreting raw mechanics directly.
- Asset generation can become theme-aware while preserving the ADR-007 originality guard.
- Future contributors have a documented boundary for what belongs in public game design artifacts.

**Negative**

- This adds another public artifact layer that must be documented, validated, and kept in sync with schemas and runtime consumers.
- Some design work becomes blocking before production-like RN work can proceed.
- The layer must be reviewed carefully because public design artifacts can still become clone-shaped even when they contain no private file paths.

## Alternatives Considered

**Let the RN prototype define the game implicitly.** Rejected because implementation details would become product decisions without a clean-room review point.

**Use asset recipes as the product direction.** Rejected because ADR-007 recipes define original asset constraints, not gameplay pillars, encounter structure, or progression.

**Keep T11 as the end state.** Rejected because T11 proves the pipeline, but it does not define a new original game.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- [ADR-007](./ADR-007-asset-recipe-originality-contract.md)
- [ADR-008](./ADR-008-behavioral-validation-no-pixel-comparison.md)
- [ADR-011](./ADR-011-mechanics-to-scenario-transformation-originality-validation.md)
- [Original Game Definition Plan](../plans/original_game_definition_plan.md)
- [React Native Prototype](../obsidian/React%20Native%20Prototype.md)

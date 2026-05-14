# T09 - First Abstract Observation Schema

## Status

🔄 In Progress

## Subtask Status

| Subtask | Title | Status |
|---------|-------|--------|
| T09.1 | Mechanics Inventory | ✅ Done — 2026-05-13 |
| T09.2 | Schema Field Definitions | 🔲 Planned |
| T09.3 | Clean-room Boundary Review | 🔲 Planned |
| T09.4 | Schema File + Examples | 🔲 Planned |

## Subtask Files

- [T09.1-mechanics-inventory.md](T09.1-mechanics-inventory.md)
- [T09.2-schema-field-definitions.md](T09.2-schema-field-definitions.md)
- [T09.3-clean-room-boundary-review.md](T09.3-clean-room-boundary-review.md)
- [T09.4-schema-file-and-examples.md](T09.4-schema-file-and-examples.md)

## Purpose

Define the first public abstraction boundary for the mechanics we want to extract from `gng`.

## Reference Reasoning

`High`

Reasoning basis:

- the task defines the first real clean-room abstraction boundary between private evidence and public design data
- it requires deciding what mechanics information is essential while excluding copyrighted or source-specific representation
- errors here can make later outputs either too weak to use or too close to the original source

## Scope

- define a public schema or documented structure for:
- locomotion
- jump arc observations
- projectile attack timing
- gravity and collision state changes
- minimal entity event traces
- keep the artifact strictly abstract

## Out of Scope

- full game ruleset coverage
- full stage layout representation
- enemy-specific catalog parity
- visual asset descriptions tied to original characters or scenery

## Inputs

- private evidence from `T08`
- current schema conventions in `packages/schemas`

## Deliverables

- one public schema or spec format for first-pass mechanics extraction
- field definitions and allowed public data examples

## Dependencies

- `T08`

## Blocks

- `T10`

## Acceptance Criteria

- the schema contains no frame paths, crop paths, or ROM references
- the schema can represent the first mechanics slice needed by the RN prototype
- the schema is explicit enough to prevent direct evidence leakage

## Implementation Notes

- bias toward a small mechanics slice that can actually be populated from the first capture

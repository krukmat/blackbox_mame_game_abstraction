# Architecture Decision Records

This directory contains the ADRs for the `blackbox_mame_game_abstraction` project.

ADRs record significant architectural and design decisions, including the context, the decision, the consequences, and known limitations. They are the primary reference for understanding *why* the system is built the way it is.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](./ADR-001-clean-room-layered-architecture.md) | Clean-Room Layered Architecture | Accepted |
| [ADR-002](./ADR-002-private-evidence-uri-scheme.md) | `private://` URI Scheme for Evidence References | Accepted |
| [ADR-003](./ADR-003-public-output-blocklist.md) | Public Output Extension and Directory Blocklist | Accepted |
| [ADR-004](./ADR-004-mame-runner-structured-results.md) | MAME Runner Structured Result Objects | Accepted |
| [ADR-005](./ADR-005-source-profile-pattern.md) | Source Profile Pattern for Game Observation Inputs | Accepted |
| [ADR-006](./ADR-006-vision-layer-numeric-only-output.md) | Vision Layer Emits Numeric Output Only | Accepted |
| [ADR-007](./ADR-007-asset-recipe-originality-contract.md) | Asset Recipe Originality Contract | Accepted |
| [ADR-008](./ADR-008-behavioral-validation-no-pixel-comparison.md) | Behavioral Validation Without Pixel Comparison | Accepted |
| [ADR-009](./ADR-009-input-plan-determinism.md) | Input Plan Determinism and YAML Definition | Accepted |

## Format

Each ADR follows the format:

- **Status**: `Proposed` | `Accepted` | `Deprecated` | `Superseded by ADR-XXX`
- **Date**: ISO 8601 date when the decision was recorded
- **Context**: What situation required a decision
- **Decision**: What was decided
- **Consequences**: Positive and negative outcomes, known limitations
- **Related**: Links to code, tasks, and other ADRs

## Key Relationships

```
ADR-001 (architecture)
  ├── ADR-002 (private:// URI)
  ├── ADR-003 (blocklist)
  ├── ADR-006 (vision numeric output)
  └── ADR-008 (no pixel validation)

ADR-004 (runner results)
  └── ADR-005 (source profiles)

ADR-006 (vision)
  └── ADR-007 (asset recipes)
```

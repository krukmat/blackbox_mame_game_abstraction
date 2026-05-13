# Visual Architecture

tags: #architecture #diagrams #overview

Source: `docs/visual-architecture.md`

## Overview

Five Mermaid diagrams that explain the project from different angles. Open `docs/visual-architecture.md` in VS Code or GitHub to render them interactively.

## Diagrams

| # | Diagram | What it shows |
|---|---------|--------------|
| 1 | Clean-Room Pipeline | Full pipeline from MAME observation to React Native prototype |
| 2 | Four-Layer Architecture | Layer stack with module assignments and data flow direction |
| 3 | Guardrails Enforcement | Sequence of three-layer write-time checks |
| 4 | Frame to Spec | How a private PGM frame becomes a public numeric JSON |
| 5 | GNG Task Progress | T01–T11 status with dependency chain |

## Key Takeaways

- The **private/public boundary** is enforced programmatically at write time, not by convention. See [[Guardrails]].
- The **vision layer** is the last layer that knows frame paths. Its output type has no path field by design. See [[Vision Layer]].
- The **asset recipe** always ships with 5 prohibited similarity rules and `human_review_required: true`. See [[Asset Factory]].
- The **behavioral validation** compares abstract traces, never pixels. See [[Behavioral Validation]].

## Related

- [[Private vs Public Boundary]]
- [[Guardrails]]
- [[Vision Layer]]
- [[Asset Factory]]
- [[Behavioral Validation]]
- [[ADR-001 Clean-Room Layered Architecture]]
- [[ADR-003 Public Output Blocklist]]
- [[ADR-006 Vision Layer Numeric Output]]
- [[GNG Integration Plan]]

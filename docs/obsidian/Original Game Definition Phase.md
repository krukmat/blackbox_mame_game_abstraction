# Original Game Definition Phase

tags: #plan #tasks #t12 #game-design

Source: `docs/plans/original_game_definition_plan.md`

## Goal

Define the original public game direction that follows T10/T11. T10/T11 prove the clean-room mechanics pipeline; T12 decides what original game the React Native prototype should become.

The working direction is Signal Garden: a mobile arcade-action prototype built from abstract mechanics, original scenario rules, and newly authored theme language.

## Task Order

| Task | Title | Purpose |
|------|-------|---------|
| T12.0 | Original Game Definition ADRs and Phase Plan | document the architecture and phase |
| T12.1 | Public Mechanics Capability Review | identify reusable abstract mechanics and clone risks |
| T12.2 | Product Direction and Gameplay Pillars | define Signal Garden's public design brief |
| T12.3 | Encounter Grammar Schema | define role-based encounter composition |
| T12.4 | Scene Recipe and Transformation Rules | define original scenes and transformation policy |
| T12.5 | Progression and Difficulty Model | define vertical-slice ramp and difficulty bands |
| T12.6 | Theme Translation and Asset Recipe Enrichment | align recipes with original theme language |
| T12.7 | RN Original Vertical Slice Hookup | consume T12 specs in the RN prototype |
| T12.8 | Originality and Design-Intent Validation Gate | validate mechanics conformance and originality divergence |

## Boundary

T12 uses public abstract artifacts only. It must not use private evidence, media captures, source names, source visual identity, exact source level layouts, or exact source encounter order.

## Related

- [[Public Original Game Definition Layer]]
- [[ADR-010 Public Original Game Definition Layer]]
- [[ADR-011 Mechanics-to-Scenario Transformation and Originality Validation]]
- [[React Native Prototype]]
- [[GNG Integration Plan]]

# ADR-011 — Mechanics-to-Scenario Transformation and Originality Validation

## Status
Accepted

## Date
2026-05-14

## Context

ADR-008 defines behavioral validation without pixel comparison. ADR-007 defines asset recipe originality requirements. Those decisions keep public artifacts safe, but they do not define how observed abstract mechanics become new playable scenarios.

The risk is structural copying. A public artifact can avoid private paths, screenshots, sprites, and names while still reproducing a source game's expressive encounter order, level rhythm, or scene framing too closely.

The project needs explicit transformation and validation rules for moving from:

```text
observed abstract mechanics
→ transformed scenario rules
→ original scene recipes
→ independent React Native prototype
```

## Decision

Define a mechanics-to-scenario transformation policy for the Public Original Game Definition Layer.

Allowed reuse:

- abstract timing bands such as fast, medium, slow, or calibrated ranges
- abstract movement relationships such as committed jump, constant horizontal velocity, gravity-driven descent, or single active projectile constraint
- role-level entity categories such as player, patroller, airborne pressure, hazard, pickup, projectile, and goal
- trace-derived state and event vocabularies when they remain generic
- behavioral validation against abstract traces and scenario assertions

Required transformation:

- convert source-derived measurements into broad tuning ranges before scene design
- substitute all source roles with original scenario roles
- author new scene layouts rather than copying source coordinates or topology
- change encounter order, spacing, staging, and resolution patterns
- use original naming, theme, and product framing
- add divergence notes to every scene recipe that explain how the recipe avoids source structure

Forbidden transformation:

- copying exact level layouts, scene order, platform topology, or spawn positions
- reproducing source enemy catalogs, names, stage names, weapons, or identity
- describing source sprites, silhouettes, palettes, animation frames, or visual framing
- using screenshots, video, crops, frames, save states, or original sprites as public references
- validating by pixel or screenshot comparison
- treating behavioral similarity as a mandate for clone-specific implementation

Validation for this layer must check both:

- **mechanics conformance**: the new prototype still follows selected abstract mechanics and trace vocabulary
- **originality divergence**: scenes, names, theme, and encounter recipes remain newly authored and do not encode source-specific expressive structure

## Consequences

**Positive**

- The project can reuse learned mechanical feel without copying expressive scenario design.
- Future scene recipes have a concrete rule: mechanics may inform constraints, but layouts and encounters must be re-authored.
- Validation expands beyond trace matching to include clean-room scenario safety.

**Negative**

- Originality divergence cannot be fully automated; human review remains required for final judgment.
- Scene recipe authors must document divergence, adding planning overhead.
- Some abstract measurements may need to be generalized into ranges before they are safe for product use.

## Alternatives Considered

**Use exact calibrated mechanics directly in scenes.** Rejected because exact values can be useful for physics tuning, but exact scenario structure must not be copied.

**Rely only on ADR-007 asset originality rules.** Rejected because visual originality does not prevent encounter or level-structure cloning.

**Avoid behavioral validation to reduce similarity risk.** Rejected because the project goal is still to study feel; the safe path is abstract validation plus divergence checks, not abandoning validation.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- [ADR-007](./ADR-007-asset-recipe-originality-contract.md)
- [ADR-008](./ADR-008-behavioral-validation-no-pixel-comparison.md)
- [ADR-010](./ADR-010-public-original-game-definition-layer.md)
- [Original Game Definition Plan](../plans/original_game_definition_plan.md)
- [Behavioral Validation](../obsidian/Behavioral%20Validation.md)

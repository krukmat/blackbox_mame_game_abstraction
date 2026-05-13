# React Native Implementation Plan

The React Native prototype is intentionally a later-phase consumer of public abstractions.

- Input: mechanics specs, entity archetypes, asset recipes, and validation cases.
- Rendering: new art only, generated from independent recipes.
- Game loop: match abstract timings, collisions, state transitions, and scoring behavior.
- Validation: compare behavior against redacted golden-master cases rather than original pixels.
- Baseline scaffold: deterministic fixed-step loop, virtual controls, placeholder geometry, debug overlay, and future React Native Skia adapter points.

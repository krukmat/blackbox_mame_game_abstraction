# ADR-010 Public Original Game Definition Layer

tags: #adr #architecture #game-design #t12

Decision: add a public original game-definition layer after T10/T11 and before production-like React Native work.

## Summary

T10/T11 prove that abstract mechanics can cross the clean-room boundary and drive a prototype. They do not define what original game is being made.

ADR-010 introduces the layer that defines gameplay pillars, product direction, encounter grammar, scene recipes, progression, and theme translation rules while consuming only public artifacts.

## Key Rule

The layer may consume public mechanics, traces, entity archetypes, asset recipes, and validation reports. It must not consume or reference ROMs, screenshots, videos, audio, save states, frames, crops, original sprites, exact source levels, source names, or source visual identity.

## Related

- [[Public Original Game Definition Layer]]
- [[ADR-011 Mechanics-to-Scenario Transformation and Originality Validation]]
- [[React Native Prototype]]
- Full ADR: `docs/adr/ADR-010-public-original-game-definition-layer.md`

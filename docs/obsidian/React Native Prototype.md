# React Native Prototype

tags: #rn #typescript #game-engine

`apps/rn-prototype/src/`

## Purpose

An independent TypeScript game engine that consumes the **public abstract specs** produced by the Python harness. It must never depend on ROMs, MAME, or private evidence paths. Its visual output uses new original assets, not the source game's art.

## Architecture

```
src/
  engine/
    GameLoop.ts        tick() → EntityState (deterministic, fixed-step)
    TimeStep.ts        fixed dt seconds per tick
    PhysicsSystem.ts   step(entity, input, dt) → EntityState
    CollisionSystem.ts AABB collision checks
    EventBus.ts        event emission (player_jump, hit, score, ...)
    SceneManager.ts    scene lifecycle
  entities/
    Entity.ts          EntityState dataclass
    Player.ts          player-specific update logic
    Enemy.ts           enemy-specific update logic
  input/
    InputState.ts      { left, right, jump, fire } booleans
    VirtualControls.ts touch/keyboard adapter
  rendering/
    SkiaAdapter.ts     adapter point for React Native Skia (placeholder)
  specs/               (public spec consumers — loaded from specs/)
```

## Key Design Decisions

**Deterministic fixed-step loop**: `GameLoop.tick(player, input)` always produces the same output for the same `(EntityState, InputState)` pair. No wall-clock time dependency inside the tick.

**No MAME dependency**: the RN prototype is fully testable without MAME, ROMs, or any Python tooling.

**Spec-driven**: entity archetypes, physics constants, and collision regions come from JSON/YAML specs in `specs/`, not from hardcoded values.

**New assets only**: rendering uses new original art generated from [[Asset Factory]] recipes. The Skia adapter is a placeholder for real rendering integration.

## Validation

The game loop emits trace entries that can be compared against observed MAME traces using [[Behavioral Validation]].

## Current State

Scaffold is implemented. Key gaps:
- Skia rendering is not connected.
- Physics constants are placeholder values.
- Enemy AI is a stub.
- No real asset loading (geometry placeholders only).

## Related

- [[Asset Factory]]
- [[Behavioral Validation]]
- [[ADR-008 Behavioral Validation No Pixels]]
- `apps/rn-prototype/`
- `docs/tasks/implemented_phases/05_react_native_prototype_phase6.md`
- `docs/react_native_implementation_plan.md`

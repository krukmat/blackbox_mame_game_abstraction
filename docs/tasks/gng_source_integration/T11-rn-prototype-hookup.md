# T11 — RN Prototype Hookup

## Status

🔄 In Progress (T11.1 ✅ Done — T11.2 🔄 In Progress)

## Objective

Connect the RN prototype engine to real public abstract artifacts so it drives behavior from calibrated mechanics data instead of hardcoded sample values. This is the boundary proof: public artifact → TypeScript engine → deterministic playable behavior.

## Why This Task Is Complex

The RN prototype currently has a working physics+collision scaffold with hardcoded fake values:

- `PhysicsSystem`: `gravity: 9.8, moveSpeed: 3, jumpVelocity: 6` — arbitrary
- `loadSpecs.ts`: imports `mechanics.generated.sample.json` and `entities.generated.sample.json` — fake stubs
- `SceneManager.createPlayableScene()`: hardcoded entity positions — not from trace
- No YAML parser present in the TypeScript environment
- `gng_abstract_mechanics.yaml` has multiple fields marked `calibration: pending` — these cannot be wired until T11.3 measures them from trace data
- `gng_trace.json` is too large (47MB+) to load wholesale in any runtime

This is not a simple "swap the import." It requires:
1. A YAML loader in TypeScript
2. A Python-side episode extractor that converts the large trace into small consumable segments
3. Physics calibration measured from trace events (jump arc, movement speed)
4. Wiring calibrated values into the engine
5. Clean-room verification that no private paths enter RN

## Scope

Five sequential subtasks, each with explicit dependencies:

- **T11.1** — Abstract Mechanics Loader (TypeScript YAML)
- **T11.2** — Trace Episode Extractor (Python + public artifact)
- **T11.3** — Physics Calibration from Trace
- **T11.4** — Episode-Driven Scene in RN Prototype
- **T11.5** — Clean-Room Verification

## Out of Scope

- Full mobile/React Native app (screen, touch input, platform build)
- Signal Garden game design (T12)
- Rendering beyond existing placeholder geometry
- Networking, persistence, monetization

## Dependencies

- T10.4 complete (fresh, quality-gated `gng_trace.json` required for T11.2 and T11.3)

## Blocks

- T12.0 (first T12 task requires T11 to demonstrate clean-room proof)

## Effort (aggregate)

`L` — five sequential subtasks, new external dependency (YAML parser), a Python extraction pipeline, calibration measurement, and clean-room gate

## Reasoning Grade

`High` — episode schema is new design territory; calibration requires measuring from noisy trace data; clean-room boundary must be maintained across both Python and TypeScript layers

## Recommended Model

`Sonnet`

---

## T11.1 — Abstract Mechanics Loader (TypeScript YAML)

### Status
✅ Done

### Purpose
Add a YAML parser to the RN prototype and load `gng_abstract_mechanics.yaml` into typed TypeScript. Wire `TimeStep` with the real calibrated `ms_per_frame` value instead of the hardcoded 16 ms stub.

### Scope
- Add `js-yaml` (or equivalent) to `apps/rn-prototype/package.json`
- Create `src/specs/mechanicsLoader.ts`:
  - reads `gng_abstract_mechanics.yaml` relative to the project root
  - returns a typed `AbstractMechanics` interface matching the YAML schema
  - exposes `timing.ms_per_frame` (calibrated: 16.768 ms)
- Update `TimeStep` to accept `ms_per_frame` from loader instead of hardcoded default
- TDD: `mechanicsLoader` loads real file, `timing.ms_per_frame` matches YAML value, `TimeStep` uses loaded value
- Existing 3 tests must still pass

### Out of Scope
- Calibrating velocity values (T11.3)
- Episode loading (T11.2)

### Dependencies
- T10.4 (gng_abstract_mechanics.yaml is already calibrated for timing; velocity fields still pending)

### Effort
`S`

### Reasoning Grade
`Low`

### Recommended Model
`Haiku`

### Acceptance Criteria
- `js-yaml` (or equivalent) present in `package.json`
- `mechanicsLoader.ts` loads `gng_abstract_mechanics.yaml` without error
- `timing.ms_per_frame` value from loader matches the YAML field (16.768)
- `TimeStep` accepts a configurable `fixedDeltaMs` sourced from loader
- All existing tests pass plus new loader tests

---

## T11.2 — Trace Episode Extractor

### Status
🔲 Planned

### Purpose
Define an "episode" format and implement a Python extractor that converts `gng_trace.json` into a small, self-contained `specs/episodes/gng_episodes.json` that the RN prototype can load without ingesting a 47MB file.

An episode is a compact, sequential record of frames capturing one meaningful gameplay scenario: player moves, jumps, fires, encounters an enemy, and resolves the encounter.

### Scope
- Design the episode schema:
  ```
  episode:
    id: string
    frame_start: int
    frame_end: int
    frames: list of:
      frame: int
      player: { x, y, velocity_x, velocity_y, state, events }
      enemies: list of { entity_id, x, y, state, events }
      projectiles: list of { entity_id, x, y, state }
  ```
- Implement `apps/mame-harness/episode_extractor.py`:
  - reads `specs/traces/gng_trace.json`
  - groups consecutive player-present frames into episodes
  - an episode starts when player spawns and ends after a configurable window (e.g., 120 frames)
  - extracts minimum 3 episodes with at least one jump event each
  - outputs `specs/episodes/gng_episodes.json`
- Verify output passes `ensure_no_private_paths`
- TDD: extractor produces valid episodes, episodes contain player data, output passes guardrails
- New public artifact path `specs/episodes/` must be allowed under ADR-003

### Out of Scope
- Loading episodes in RN (T11.4)
- Physics calibration (T11.3)
- Modifying trace schema

### Dependencies
- T10.4 (quality-gated trace with ≥ 20 jump events required)
- T11.1 (episode schema design informs what the loader in T11.4 needs)

### Effort
`M`

### Reasoning Grade
`High` — episode boundary logic must handle detection gaps, wrap-around, and sparse player data; new public artifact type may need ADR annotation

### Recommended Model
`Sonnet`

### Acceptance Criteria
- `episode_extractor.py` runs without error on the T10.4 trace
- Output contains ≥ 3 episodes, each with ≥ 1 jump event
- Episodes contain only normalized coordinates (0.0–1.0 range), no pixel addresses
- `ensure_no_private_paths` passes on `gng_episodes.json`
- `specs/episodes/gng_episodes.json` is ≤ 500 KB
- All Python tests pass

---

## T11.3 — Physics Calibration from Trace

### Status
🔲 Planned

### Purpose
Measure the actual GNG physics constants from player trace events and calibrate the `PhysicsSystem` in the RN prototype. Remove all `calibration: pending` markers from `gng_abstract_mechanics.yaml` for locomotion, jump arc, and projectile fields.

### Scope
- Implement `apps/mame-harness/physics_calibrator.py`:
  - Reads player trace entries
  - Measures `velocity_x` from consecutive moving frames (normalized → abstract units)
  - Measures jump arc: frames from `jump_start` → `jump_peak` → `land`, derives `jumpVelocity` and `gravity`
  - Reports measured constants with standard deviation and sample count
  - Output: `specs/calibration/gng_physics_calibration.yaml`
- Update `gng_abstract_mechanics.yaml`:
  - Replace `calibration: pending` with measured values for: `locomotion.velocity_x`, `jump_arc.velocity_y`, `jump_arc.gravity_units_per_frame`, `projectile.velocity_x`
  - Set `calibration_status: calibrated` for all affected fields
- Update `PhysicsSystem` default config in RN prototype with calibrated values
- TDD: calibrator returns non-zero values for all required fields, values within plausible GNG range, mechanics YAML updated values pass schema

### Out of Scope
- Enemy or projectile mass calibration
- Collision size calibration

### Dependencies
- T10.4 (trace must have ≥ 20 jump events and ≥ 30 fire events)
- T11.1 (TypeScript types for mechanics must exist before updating PhysicsSystem)

### Effort
`M`

### Reasoning Grade
`High` — trace velocity values are noisy ratios; jump arc requires frame-accurate peak detection across sparse player data; measured values must be physically plausible

### Recommended Model
`Sonnet`

### Acceptance Criteria
- `physics_calibrator.py` produces `specs/calibration/gng_physics_calibration.yaml`
- Calibration file documents measured values with sample count ≥ 10 for each constant
- `gng_abstract_mechanics.yaml` has no remaining `calibration: pending` fields for locomotion, jump, and projectile
- `PhysicsSystem` default config matches calibrated values
- All Python and TypeScript tests pass

---

## T11.4 — Episode-Driven Scene in RN Prototype

### Status
🔲 Planned

### Purpose
Load a real episode from `gng_episodes.json` into the RN engine and build a playable scene from it. Replace `SceneManager.createPlayableScene()` hardcoded layout with `createEpisodeScene(episode)` driven by episode entity data.

### Scope
- Add `src/specs/episodeLoader.ts`:
  - reads `gng_episodes.json`
  - returns typed episode array
  - validates episode has required player and frame data
- Extend `SceneManager`:
  - `createEpisodeScene(episode: Episode): SceneState` — builds scene from episode entity types and initial positions
  - entities derive `kind`, initial `position`, and `velocity` from episode frame 0
- Update `GameLoop.tick()` to advance through episode frames when in episode-playback mode
- PhysicsSystem uses calibrated values from T11.3
- TDD:
  - `episodeLoader` loads real file without error
  - `createEpisodeScene` produces correct entity kinds from episode data
  - episode playback advances frame counter
  - all existing tests pass

### Out of Scope
- Visual rendering to screen
- Mobile touch input
- Saving episode state

### Dependencies
- T11.2 (gng_episodes.json must exist)
- T11.3 (PhysicsSystem must use calibrated values)

### Effort
`M`

### Reasoning Grade
`Medium`

### Recommended Model
`Sonnet`

### Acceptance Criteria
- `episodeLoader.ts` loads `gng_episodes.json` without error
- `createEpisodeScene` builds a scene with entity kinds matching the episode data
- `GameLoop` can advance through episode frames deterministically
- All existing tests pass plus new episode tests
- No hardcoded positions or velocities remain in `createPlayableScene` or `createEpisodeScene`

---

## T11.5 — Clean-Room Verification

### Status
🔲 Planned

### Purpose
Verify that the RN prototype, after T11.1–T11.4 changes, does not import private evidence, ROM paths, or frame-derived data. Confirm the clean-room boundary holds across both the Python extraction layer and the TypeScript engine.

### Scope
- Audit all `import` and `require` paths in `apps/rn-prototype/src/` — none may reference `evidence/private/`, `plans/`, or any path outside `specs/` or `packages/schemas/`
- Audit `gng_episodes.json` and `gng_physics_calibration.yaml` for private path references
- Add TypeScript test asserting the episode and mechanics loaders import only from allowed public paths
- Add Python test asserting `episode_extractor.py` and `physics_calibrator.py` output files pass `ensure_no_private_paths`
- Verify `package.json` has no dependencies on native MAME or ROM tooling

### Out of Scope
- Auditing T12 artifacts (not yet created)

### Dependencies
- T11.1–T11.4 complete

### Effort
`S`

### Reasoning Grade
`Low`

### Recommended Model
`Haiku`

### Acceptance Criteria
- No RN source file imports from outside `specs/` or `packages/schemas/`
- `gng_episodes.json` passes `ensure_no_private_paths`
- `gng_physics_calibration.yaml` passes `ensure_no_private_paths`
- All Python and TypeScript tests pass

---

## Subtask Summary

| Subtask | Title | Effort | Reasoning | Model |
|---------|-------|--------|-----------|-------|
| T11.1 | Abstract Mechanics Loader (TypeScript YAML) | `S` | `Low` | Haiku |
| T11.2 | Trace Episode Extractor | `M` | `High` | Sonnet |
| T11.3 | Physics Calibration from Trace | `M` | `High` | Sonnet |
| T11.4 | Episode-Driven Scene in RN Prototype | `M` | `Medium` | Sonnet |
| T11.5 | Clean-Room Verification | `S` | `Low` | Haiku |

## Reference Documents

- [This Task File](./T11-rn-prototype-hookup.md)
- [T10.4-public-artifact-generation.md](T10.4-public-artifact-generation.md)
- [T10.6-opencv-vision-backend.md](T10.6-opencv-vision-backend.md)
- [gng_source_integration_plan.md](../../plans/gng_source_integration_plan.md)
- [original_game_definition_plan.md](../../plans/original_game_definition_plan.md)
- [ADR-001](../../adr/ADR-001-clean-room-layered-architecture.md)
- [ADR-003](../../adr/ADR-003-public-output-blocklist.md)
- [ADR-006](../../adr/ADR-006-vision-layer-numeric-only-output.md)
- [ADR-008](../../adr/ADR-008-behavioral-validation-no-pixel-comparison.md)
- [ADR-010](../../adr/ADR-010-public-original-game-definition-layer.md)
- [docs/obsidian/React Native Prototype.md](../../obsidian/React%20Native%20Prototype.md)
- [docs/obsidian/Vision Layer.md](../../obsidian/Vision%20Layer.md)
- [README.md](../../../README.md)
- [CLAUDE.md](../../../CLAUDE.md)
- [AGENTS.md](../../../AGENTS.md)

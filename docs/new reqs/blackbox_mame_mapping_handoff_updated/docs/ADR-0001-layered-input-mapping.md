---
title: ADR-0001 - Layered Input Mapping and Bootstrap Simplification
status: proposed
date: 2026-05-16
tags:
  - adr
  - blackbox-mame
  - clean-room
  - input-mapping
  - mame
  - sdl
  - retroarch
  - codex-ready
  - claude-code-ready
related:
  - README.md
  - AGENTS.md
  - CLAUDE.md
  - apps/mame-harness/input_planner.py
  - apps/mame-harness/source_profiles.py
  - apps/mame-harness/preflight.py
  - apps/mame-harness/mame_runner.py
  - scripts/launch_manual_capture.sh
  - scripts/launch_manual_capture_autoboot.sh
  - scripts/mame_autoboot.lua
  - packages/schemas
  - packages/validation
  - packages/vision
---

# ADR-0001 - Layered Input Mapping and Bootstrap Simplification

## Status

Proposed.

## Context

The repository concept is understandable and valuable: use MAME as a private black-box observation boundary, capture behavioral evidence, redact private or sensitive artifacts, extract public behavioral abstractions, and feed an independent implementation without copying ROMs, screenshots, audio, sprites, local paths, or expressive game content.

The main friction is not the high-level concept. The main friction is the first mapping phase.

At the moment, the bootstrap path effectively expects the contributor to understand too many things too early:

- MAME execution details.
- Local MAME, ROM and ffmpeg paths.
- Game-specific driver knowledge, currently strongly biased toward `gngb`.
- YAML input plans.
- Frame timing and boot timing.
- The difference between physical device input, canonical controller input and semantic game action.
- Which commands are production-ready and which are still placeholders.

The current flow jumps too quickly from low-level observation to semantic game actions such as `insert_coin`, `press_start`, `jump`, `fire`, `move_left` and `move_right`. This makes the first phase fragile because it asks the user to author a game-specific action plan before the system has normalized the physical input layer.

Comparable open-source ecosystems solve adjacent parts of this problem through layered abstractions:

- SDL GameController mappings normalize physical controllers into canonical button names.
- RetroArch separates physical controller detection/autoconfiguration from the virtual `RetroPad` abstraction and later core/game remaps.
- AntiMicroX demonstrates the value of a guided mapping UX and reusable input profiles.
- stable-retro demonstrates the value of explicit action spaces, although its target is reinforcement learning rather than clean-room game abstraction.

The repository should adopt the same architectural lesson: separate physical device mapping from canonical controller mapping from game-specific semantic actions.

## Decision

Introduce a three-layer input mapping model before the existing `input_plan -> per-frame JSON -> Lua -> MAME` pipeline.

The new mapping model will be:

```text
physical device profile
        ↓
canonical controller profile
        ↓
game action profile
        ↓
compiled input plan
        ↓
existing frame-level JSON / Lua / MAME execution
```

### Layer 1 - Device Profile

Represents the detected or manually configured physical controller/keyboard.

Purpose:

- Capture device identity.
- Store raw physical input identifiers.
- Normalize raw input names to canonical control names.
- Allow import from SDL GameControllerDB or RetroArch autoconfig where possible.

Example location:

```text
profiles/devices/<device_id>.yaml
```

Example shape:

```yaml
schema_version: 1
profile_type: device_profile
id: keyboard_default
source: manual
device:
  kind: keyboard
  name: Default Keyboard
  guid: null
raw_to_canonical:
  ArrowLeft: dpad_left
  ArrowRight: dpad_right
  ArrowUp: dpad_up
  ArrowDown: dpad_down
  KeyZ: south
  KeyX: east
  Enter: start
  ShiftRight: select
metadata:
  created_by: bootstrap
  clean_room_safe: true
```

### Layer 2 - Canonical Controller Profile

Represents the stable internal controller vocabulary used by the repository.

Purpose:

- Avoid coupling game logic to physical hardware.
- Keep a reusable vocabulary across games.
- Provide a deterministic target for importers and tests.

Initial canonical controls:

```text
dpad_left
dpad_right
dpad_up
dpad_down
south
east
west
north
start
select
l1
r1
pause
noop
```

The canonical vocabulary should be intentionally small at first. It can be expanded only when a real game/profile requires it.

Example location:

```text
profiles/controllers/arcade_2button.yaml
```

Example shape:

```yaml
schema_version: 1
profile_type: controller_profile
id: arcade_2button
canonical_controls:
  - dpad_left
  - dpad_right
  - dpad_up
  - dpad_down
  - south
  - east
  - start
  - select
constraints:
  required:
    - dpad_left
    - dpad_right
    - south
    - east
    - start
  optional:
    - dpad_up
    - dpad_down
    - select
metadata:
  clean_room_safe: true
```

### Layer 3 - Game Action Profile

Maps canonical controller controls to semantic game actions for a specific source profile / driver.

Purpose:

- Keep game semantics separate from hardware.
- Allow different games to reuse the same controller profile.
- Compile semantic action plans only after the physical and canonical layers are stable.

Example location:

```text
profiles/games/gngb/default_actions.yaml
```

Example shape:

```yaml
schema_version: 1
profile_type: game_action_profile
id: gngb_default_actions
source_profile: gng
driver: gngb
canonical_to_action:
  dpad_left: move_left
  dpad_right: move_right
  dpad_up: move_up
  dpad_down: move_down
  south: jump
  east: fire
  start: press_start
  select: insert_coin
allowed_actions:
  - noop
  - insert_coin
  - press_start
  - move_left
  - move_right
  - move_up
  - move_down
  - jump
  - fire
metadata:
  clean_room_safe: true
```

### Compiled Input Plan

The existing `input_planner.py` and Lua/MAME integration should remain the execution boundary. The new profiles should compile into the existing input plan format first, rather than forcing a broad rewrite.

This means the first implementation phase should add a compatibility compiler, not replace the working MAME harness.

Example command target:

```bash
python -m apps.mame_harness.cli map compile \
  --device profiles/devices/keyboard_default.yaml \
  --controller profiles/controllers/arcade_2button.yaml \
  --game profiles/games/gngb/default_actions.yaml \
  --sequence plans/sequences/gng_smoke_sequence.yaml \
  --out plans/generated/gng_smoke_compiled.yaml
```

## Consequences

### Positive consequences

- The first mapping phase becomes guided and deterministic.
- Contributors no longer need to understand game semantics before mapping physical input.
- Hardware mapping becomes reusable across games.
- The current MAME harness can remain mostly intact.
- SDL and RetroArch mappings can be imported later without redesigning the core model.
- Testability improves because each layer can be validated independently.
- Clean-room guardrails remain compatible with the architecture because public profiles contain only abstract mappings, not expressive game assets.

### Negative consequences

- More files and concepts are introduced.
- Profile schema design must be kept small to avoid overengineering.
- Importers from SDL/RetroArch can introduce edge cases.
- A wizard can become complex if implemented before the data model is stable.

### Neutral consequences

- The current `gngb` bias remains acceptable in the short term, provided the architecture no longer hardcodes that assumption into the mapping model.
- Existing plans can remain as fixtures while the new layer is introduced.

## Decision Drivers

- Reduce first-phase mapping friction.
- Preserve the clean-room boundary.
- Avoid rewriting the working MAME harness.
- Make mapping deterministic and testable.
- Separate mechanical input discovery from semantic game abstraction.
- Make future multi-game support realistic.
- Enable later import from SDL GameControllerDB and RetroArch autoconfig.

## Alternatives Considered

### Alternative A - Keep YAML semantic plans only

Continue using hand-authored YAML plans with actions such as `jump`, `fire`, `insert_coin` and `press_start`.

Rejected because it keeps the current first-phase friction and forces contributors to understand semantic actions and frame timing before they have a working device/controller setup.

### Alternative B - Build a full GUI first

Build a visual mapping tool similar to AntiMicroX before refactoring the input model.

Rejected for now because a GUI would hide, not solve, the missing domain model. A CLI/TUI wizard can come after the profile schema is stable.

### Alternative C - Replace MAME harness with RetroArch/libretro

Use RetroArch/libretro as the execution layer to inherit its input abstraction.

Rejected for now because the current repo is already built around MAME, MAME drivers and Lua/autoboot execution. RetroArch is useful as a pattern and possible future adapter, not as an immediate replacement.

### Alternative D - Use stable-retro style action spaces directly

Model games as Gymnasium-like environments from the start.

Rejected for now because the project goal is clean-room behavioral abstraction and independent reimplementation support, not reinforcement learning. The action-space idea is useful, but the full RL stack is unnecessary.

## Scope

### In scope

- Add profile schemas for `device_profile`, `controller_profile` and `game_action_profile`.
- Add sample profiles for keyboard and `gngb`.
- Add validation for profile files.
- Add compiler from layered profiles to the current input plan format.
- Add tests for schema validation and compilation.
- Add docs explaining the new mapping model.
- Add a first CLI command group such as `map validate` and `map compile`.

### Out of scope for this ADR

- Full GUI.
- Full TUI wizard.
- Automatic screen/state segmentation.
- Automatic semantic inference of game actions.
- Full boot calibration.
- Full SDL/RetroArch importers.
- Replacing MAME with another backend.
- Any use of ROMs, screenshots, audio, sprites or expressive game assets in public artifacts.

## Implementation Plan

### Phase 1 - Foundation

Goal: introduce the layered model without changing the MAME execution path.

Tasks:

1. Create directories:

```text
profiles/devices/
profiles/controllers/
profiles/games/gngb/
plans/sequences/
plans/generated/
```

2. Add JSON Schemas:

```text
packages/schemas/device_profile.schema.json
packages/schemas/controller_profile.schema.json
packages/schemas/game_action_profile.schema.json
packages/schemas/input_sequence.schema.json
```

3. Add sample YAML profiles:

```text
profiles/devices/keyboard_default.yaml
profiles/controllers/arcade_2button.yaml
profiles/games/gngb/default_actions.yaml
plans/sequences/gng_smoke_sequence.yaml
```

4. Add profile loading and validation module:

```text
apps/mame-harness/mapping_profiles.py
```

5. Add compiler module:

```text
apps/mame-harness/mapping_compiler.py
```

6. Add CLI subcommands:

```bash
blackbox map validate --profile <path>
blackbox map compile --device <path> --controller <path> --game <path> --sequence <path> --out <path>
```

7. Add tests:

```text
apps/mame-harness/tests/test_mapping_profiles.py
apps/mame-harness/tests/test_mapping_compiler.py
apps/mame-harness/tests/test_mapping_cli.py
```

### Phase 2 - Bootstrap and Portability

Goal: remove local-machine assumptions and make the first run portable.

Tasks:

1. Add environment config file support:

```text
.env.example
blackbox.local.example.yaml
```

2. Replace hardcoded paths in scripts with config/env variables.
3. Add `doctor` command or extend existing `preflight`.
4. Ensure public metadata redacts local paths.
5. Add docs:

```text
docs/bootstrap.md
docs/mapping.md
```

### Phase 3 - Importers

Goal: reduce manual mapping using known controller databases.

Tasks:

1. Add SDL mapping parser:

```text
apps/mame-harness/sdl_mapping_importer.py
```

2. Add RetroArch autoconfig parser:

```text
apps/mame-harness/retroarch_mapping_importer.py
```

3. Add CLI commands:

```bash
blackbox map import-sdl --mapping-line <line> --out <path>
blackbox map import-retroarch --config <path> --out <path>
```

4. Add round-trip tests.

### Phase 4 - Mapping Wizard

Goal: provide guided first-use mapping.

Tasks:

1. Add a CLI wizard:

```bash
blackbox map init
```

2. Wizard should:

- Ask for device type: keyboard, controller, arcade stick.
- Offer a preset when available.
- Ask the user to bind required controls.
- Validate duplicate bindings.
- Save a `device_profile` and optionally a `game_action_profile`.
- Never store screenshots, ROM paths or private evidence in public profiles.

### Phase 5 - Boot Calibration

Goal: reduce fragile hand-authored frame timings.

Tasks:

1. Add a `calibrate-boot` command.
2. Store calibration metadata under a clean-room-safe public profile.
3. Keep raw video/screenshots private.
4. Output only abstract timing/state metadata.

## Acceptance Criteria

The implementation is acceptable when:

- Existing tests continue to pass.
- Existing MAME harness behavior is not broken.
- A keyboard profile can compile a smoke input sequence into the current YAML input plan format.
- Generated public profiles do not contain absolute paths, ROM paths, screenshots, audio, sprite dumps or private evidence paths.
- Invalid profile files fail with actionable validation messages.
- Duplicate or missing required controls are detected.
- The README or docs explain the difference between device, controller and game action profiles.
- The new flow supports `gngb` without hardcoding the architecture to `gngb`.

## Risks

| Risk | Mitigation |
|---|---|
| Overengineering the profile model | Keep schemas minimal and implement only keyboard + arcade 2-button + gngb first. |
| Breaking existing input plans | Compile to existing format and keep old tests/fixtures. |
| Leaking private machine paths | Reuse existing guardrails and add profile-specific tests. |
| Importer complexity | Defer SDL/RetroArch importers until the internal profile model is stable. |
| Wizard complexity | Implement `map validate` and `map compile` before `map init`. |

## Recommended First Pull Request

Title:

```text
Introduce layered input mapping profiles and compiler
```

Scope:

- Add schemas.
- Add sample profiles.
- Add mapping profile loader.
- Add mapping compiler to existing input plan format.
- Add CLI `map validate` and `map compile`.
- Add tests.
- Add documentation page `docs/mapping.md`.

Do not include SDL importer, RetroArch importer, GUI/TUI wizard or boot calibration in the first PR.

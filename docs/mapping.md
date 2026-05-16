# Layered Input Mapping

The first mapping phase now has an explicit public compatibility layer before the existing deterministic MAME execution path.

## Why This Exists

The old bootstrap path forced contributors to jump too quickly from physical keys or buttons to game-semantic actions like `jump`, `fire`, `insert_coin`, and `press_start`.

The layered model separates four concerns:

- physical device mapping: raw keyboard or controller inputs
- canonical controller mapping: the repo's reusable internal control vocabulary
- semantic game action mapping: game-specific actions such as `move_right` or `jump`
- compiled input plan: the existing YAML plan consumed by `input_planner.py`

## Model

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

The important boundary is unchanged:

```text
layered public profiles
  -> generated public input plan YAML
  -> apps/mame-harness/input_planner.py
  -> private per-frame JSON
  -> scripts/mame_autoboot.lua
  -> MAME
```

This first implementation does not rewrite the runner, Lua injection, or MAME execution path.

## Files

- `profiles/devices/` — physical keyboard or controller bindings to canonical controls
- `profiles/controllers/` — canonical controller vocabulary and required controls
- `profiles/games/<driver>/` — canonical controls mapped to semantic game actions
- `plans/sequences/` — canonical control sequences
- `plans/generated/` — compiled public input plans compatible with `input_planner.py`

## GNG Runtime Path

For GNG, the canonical layered path is now:

```text
profiles/games/gngb/default_actions.yaml
  -> plans/sequences/gng_boot_only.yaml or plans/sequences/gng_gameplay.yaml
  -> plans/generated/gng_boot_only.yaml or plans/generated/gng_gameplay.yaml
  -> input_planner.py
  -> private JSON
  -> scripts/mame_autoboot.lua
  -> MAME
```

Use these terms consistently:

- `plans/sequences/...` = editable layered source of truth
- `plans/generated/...` = runtime-facing public plans

The older authored semantic plans under `plans/gng_boot_only.yaml` and `plans/gng_gameplay.yaml` remain historical reference artifacts only. They are no longer the canonical operational path.

Future boot calibration work remains bounded by ADR-018:

- a public `profiles/games/gngb/boot_calibration.yaml` may become the timing source
- that calibration artifact would regenerate or replace the fixed-wait boot portions of the sequence/generation flow
- it must not introduce a second GNG-specific runtime model outside the same generated-plan boundary

## Clean-Room Boundary

These files are public clean-room artifacts. They may contain abstract mappings only.

They must not contain:

- ROMs or ROM paths
- screenshots, video, audio, sprites, frame dumps, or crop paths
- absolute local machine paths
- `evidence/private/` paths
- `private://` evidence handles

The compiler and loader reuse the existing guardrail conventions:

- unsafe public output paths are rejected
- payload strings are scanned for private markers and absolute paths
- missing mappings fail explicitly instead of silently degrading to `noop`

## Quickstart

Repo-local command form:

```bash
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map init \
  --out profiles/devices/my_controller.yaml

apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map import-sdl \
  --db path/to/gamecontrollerdb.txt \
  --name "8BitDo Pro 2" \
  --out profiles/devices/8bitdo_pro_2.yaml

apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map import-retroarch \
  --config path/to/controller.cfg \
  --out profiles/devices/imported_retroarch_controller.yaml

apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map validate \
  --profile profiles/devices/keyboard_default.yaml

apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map compile \
  --device profiles/devices/keyboard_default.yaml \
  --controller profiles/controllers/arcade_2button.yaml \
  --game profiles/games/gngb/default_actions.yaml \
  --sequence plans/sequences/gng_smoke_sequence.yaml \
  --out plans/generated/gng_smoke_compiled.yaml
```

Equivalent shorthand if your environment exposes the CLI as `blackbox`:

```bash
blackbox map validate --profile profiles/devices/keyboard_default.yaml

blackbox map compile \
  --device profiles/devices/keyboard_default.yaml \
  --controller profiles/controllers/arcade_2button.yaml \
  --game profiles/games/gngb/default_actions.yaml \
  --sequence plans/sequences/gng_smoke_sequence.yaml \
  --out plans/generated/gng_smoke_compiled.yaml
```

The compiled file is still just the existing input-plan shape:

```yaml
plan_name: gng_smoke_sequence
game_id: gngb
steps:
  - action: insert_coin
    frames: 4
  - action: press_start
    frames: 4
```

## Wizard

`map init` is a prompt-based wizard that creates a public `device_profile` without hand-authoring YAML.

The first version:

- asks for device type, profile id, device name, optional guid, and output path
- offers `keyboard_default` as an optional device-binding preset
- uses `arcade_2button` as the controller-shape preset
- enforces required controls
- allows optional controls to be skipped
- rejects duplicate raw bindings during input

After writing the YAML, it prints the next `map validate` command and a compile example command.

## SDL Import

`map import-sdl` imports one SDL GameControllerDB entry into the existing `device_profile` layer.

Supported SDL controls map onto the current canonical vocabulary only:

- `dpup`, `dpdown`, `dpleft`, `dpright`
- `a`, `b`, `x`, `y`
- `back`, `start`
- `leftshoulder`, `rightshoulder`
- `guide`

Unsupported SDL controls are ignored with explicit warnings in the CLI result. Duplicate SDL fields, duplicate canonical mappings, and duplicate raw physical bindings fail explicitly.

## RetroArch Import

`map import-retroarch` imports one RetroArch autoconfig `.cfg` file into the existing `device_profile` layer.

Supported RetroArch fields map onto the current canonical vocabulary only:

- `input_up_btn`, `input_up_axis`
- `input_down_btn`, `input_down_axis`
- `input_left_btn`, `input_left_axis`
- `input_right_btn`, `input_right_axis`
- `input_a_btn`, `input_b_btn`, `input_x_btn`, `input_y_btn`
- `input_select_btn`, `input_start_btn`
- `input_l_btn`, `input_r_btn`

The importer uses a fixed RetroPad-style face-button convention:

- `input_b_btn` -> `south`
- `input_a_btn` -> `east`

Unsupported RetroArch fields are ignored with explicit warnings in the CLI result. Duplicate canonical mappings and duplicate raw physical bindings fail explicitly.

## Portable Bootstrap

MAP-07 adds a portable local bootstrap layer around the mapping workflow without changing the execution boundary.

Use:

```bash
cp .env.example .env
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py doctor
```

The doctor command checks:

- configured MAME binary and version
- ffmpeg availability
- source-profile and driver alignment
- ROM-path preflight for the selected source profile
- writable private evidence root under `evidence/private`
- repo-relative public trace output safety

Bootstrap details live in [`docs/bootstrap.md`](bootstrap.md).

## First-PR Limits

- `map validate` validates one public mapping artifact at a time.
- `map compile` compiles only through the current `input_planner.py` contract.
- Missing controller bindings or game-action mappings fail explicitly.
- `pause` exists in `input_planner.VALID_ACTIONS`, but it is not treated as part of the safe first-PR execution surface because the current Lua injector does not map it.

## Deferred Work

Not part of the first implementation:

- boot calibration
- runner or Lua rewrites

## First-PR Review Notes

Review against the Phase 1 prompt found one schema/model inconsistency and one contributor-UX risk:

- `input_sequence` examples in the handoff use `sequence_type`, while the initial schema required `profile_type` only
- the handoff examples assume a `blackbox` executable, while the repo currently exposes the CLI through `apps/mame-harness/cli.py`

Both are resolved in the current branch:

- `packages/schemas/input_sequence.schema.json` now accepts either `profile_type` or `sequence_type`
- this document shows the repo-local command form first and keeps `blackbox` only as shorthand

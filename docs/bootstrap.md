# Bootstrap Setup

Use this when setting up the repo on a new machine. Keep all local machine details in ignored config files or environment variables.

## What Stays Local

- MAME binary location
- ffmpeg binary location
- private ROM directory
- private evidence root under `evidence/private`

Do not commit those values into tracked docs or source files.

## 1. Create The Harness Environment

```bash
python3.11 -m venv apps/mame-harness/.venv
source apps/mame-harness/.venv/bin/activate
pip install -e '.[dev]'
```

## 2. Add Local Bootstrap Config

Option A: shell-friendly config for scripts and `doctor`

```bash
cp .env.example .env
```

Fill in at least:

- `BLACKBOX_SOURCE_PROFILE`
- `BLACKBOX_MAME_DRIVER`
- `BLACKBOX_MAME_BINARY`
- `BLACKBOX_FFMPEG_BINARY`
- `BLACKBOX_ROM_PATH`

Option B: YAML config for `doctor`

```bash
cp blackbox.local.example.yaml blackbox.local.yaml
```

Environment variables override YAML when both are present.

## 3. Verify The Machine

```bash
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py doctor
```

The doctor command checks:

- configured MAME binary presence and version
- ffmpeg availability
- source-profile and driver alignment
- ROM path preflight for the selected source profile
- writable private evidence root under `evidence/private`
- repo-relative public trace output path safety

Its output is path-safe: it reports statuses and issue codes without printing local machine paths.

## 4. Mapping Workflow

```bash
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map validate \
  --profile profiles/devices/keyboard_default.yaml

apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map compile \
  --device profiles/devices/keyboard_default.yaml \
  --controller profiles/controllers/arcade_2button.yaml \
  --game profiles/games/gngb/default_actions.yaml \
  --sequence plans/sequences/gng_smoke_sequence.yaml \
  --out plans/generated/gng_smoke_compiled.yaml
```

This still compiles into the existing execution boundary:

```text
layered profiles
  -> generated YAML
  -> input_planner.py
  -> private JSON
  -> scripts/mame_autoboot.lua
  -> MAME
```

## 5. Manual Capture Helpers

After `doctor` passes:

```bash
./scripts/launch_manual_capture_autoboot.sh manual_01
./scripts/extract_frames.sh manual_01
```

Those scripts read `.env` automatically. They no longer assume a machine-specific MAME binary or ROM path, but they still enforce that evidence stays under `evidence/private`.

For GNG, the runtime-facing defaults now point at generated plans:

- `BLACKBOX_BOOT_PLAN=plans/generated/gng_boot_only.yaml`
- `BLACKBOX_TRACE_INPUT_PLAN=plans/generated/gng_gameplay.yaml`

The editable layered source of truth remains:

- `plans/sequences/gng_boot_only.yaml`
- `plans/sequences/gng_gameplay.yaml`

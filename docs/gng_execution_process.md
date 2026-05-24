# GNG Execution Process

This document is the operational reference for running the GNG observation flow after layered mapping adoption.

Use it when you need to:

- verify a local machine is ready
- run a manual GNG capture
- run an automated GNG capture path
- recompile GNG runtime plans after editing layered inputs

## Canonical Runtime Model

For GNG, the canonical execution path is:

```text
profiles/games/gngb/default_actions.yaml
  -> plans/sequences/gng_boot_only.yaml or plans/sequences/gng_gameplay.yaml
  -> plans/generated/gng_boot_only.yaml or plans/generated/gng_gameplay.yaml
  -> input_planner.py
  -> private per-frame JSON
  -> scripts/mame_autoboot.lua
  -> MAME
```

Operational rule:

- edit behavior in `plans/sequences/...`
- execute `plans/generated/...`

The older authored semantic plans under `plans/gng_boot_only.yaml` and `plans/gng_gameplay.yaml` remain migration references only. They are not the canonical runtime path.

## Required Local Inputs

You need:

- `apps/mame-harness/.venv/`
- a working MAME binary
- a working `ffmpeg` binary
- a private ROM directory containing `gng.zip`
- local config in `.env` or `blackbox.local.yaml`

The active GNG source-profile contract remains:

- source profile: `gng`
- MAME driver: `gngb`

## Default Runtime Artifacts

The runtime-facing defaults are:

- boot plan: `plans/generated/gng_boot_only.yaml`
- gameplay plan: `plans/generated/gng_gameplay.yaml`
- trace output: `specs/traces/gng_trace.json`

The editable layered sources are:

- `plans/sequences/gng_boot_only.yaml`
- `plans/sequences/gng_gameplay.yaml`

## 1. Machine Verification

Create local config if needed:

```bash
cp .env.example .env
```

Fill in at least:

- `BLACKBOX_MAME_BINARY`
- `BLACKBOX_FFMPEG_BINARY`
- `BLACKBOX_ROM_PATH`

Then run:

```bash
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py doctor
```

This verifies:

- MAME binary presence and version
- ffmpeg presence
- source-profile and driver alignment
- ROM-path preflight
- writable private evidence root
- public trace-output path safety

Do not skip this step on a new machine.

## 2. Recommended Manual Capture

This is the standard GNG execution flow for interactive observation.

Launch MAME with automated boot:

```bash
./scripts/launch_manual_capture_autoboot.sh manual_01
```

What it does:

1. Loads `plans/generated/gng_boot_only.yaml`
2. Exports a private per-frame JSON plan for Lua
3. Launches MAME with `scripts/mame_autoboot.lua`
4. Injects coin and start automatically
5. Hands control to the user once Arthur is controllable
6. Records `capture.avi` under `evidence/private/run_manual_01/`

After you close MAME, extract frames and regenerate the public trace:

```bash
./scripts/extract_frames.sh manual_01
```

That step:

1. Extracts PNG frames privately under `evidence/private/.../frames/extracted_png/`
2. Regenerates `specs/traces/gng_trace.json`
3. Prints trace-entry and state/event counts

## 3. Fully Manual Capture

Use this only if you do not want autoboot injection.

```bash
./scripts/launch_manual_capture.sh manual_01
./scripts/extract_frames.sh manual_01
```

In this mode, the user performs coin and start manually inside MAME.

## 4. Automated CLI Run

Use this when you want the harness run path directly rather than the shell helper scripts.

```bash
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py run \
  --rom gng \
  --source-profile gng \
  --rom-path /private/path/to/roms \
  --input-plan plans/generated/gng_gameplay.yaml \
  --frames-to-run 300
```

Use `--dry-run` first if you only want to validate command construction:

```bash
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py run \
  --rom gng \
  --source-profile gng \
  --input-plan plans/generated/gng_gameplay.yaml \
  --frames-to-run 300 \
  --dry-run
```

## 5. Recompile After Editing Layered Inputs

If you change `profiles/games/gngb/default_actions.yaml` or either GNG sequence file, recompile before executing.

Boot plan:

```bash
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map compile \
  --device profiles/devices/keyboard_default.yaml \
  --controller profiles/controllers/arcade_2button.yaml \
  --game profiles/games/gngb/default_actions.yaml \
  --sequence plans/sequences/gng_boot_only.yaml \
  --out plans/generated/gng_boot_only.yaml
```

Gameplay plan:

```bash
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map compile \
  --device profiles/devices/keyboard_default.yaml \
  --controller profiles/controllers/arcade_2button.yaml \
  --game profiles/games/gngb/default_actions.yaml \
  --sequence plans/sequences/gng_gameplay.yaml \
  --out plans/generated/gng_gameplay.yaml
```

Optional validation before compile:

```bash
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map validate \
  --profile plans/sequences/gng_boot_only.yaml

apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map validate \
  --profile plans/sequences/gng_gameplay.yaml
```

## 6. Guardrails And Boundaries

Public runtime artifacts may include:

- generated YAML input plans
- public traces under `specs/`
- abstract mechanics and validation outputs

Public runtime artifacts must not include:

- ROM paths
- screenshots
- videos
- frame paths
- crop paths
- private evidence paths

Private evidence stays under:

```text
evidence/private/
```

## 7. Current Boot-Timing Source

Today, boot timing still comes from fixed waits carried through the layered GNG sequence/generation path.

Current source:

- `plans/sequences/gng_boot_only.yaml`
- `plans/generated/gng_boot_only.yaml`

Future direction:

- `profiles/games/gngb/boot_calibration.yaml`

When ADR-018 is implemented in production, that calibration artifact should replace or regenerate the boot-specific timing without changing the runtime boundary.

## 8. Decision Rules

Use these rules consistently:

- want to run GNG now: use `plans/generated/...`
- want to change GNG behavior: edit `plans/sequences/...`, then recompile
- want to inspect private evidence: use `evidence/private/...` locally only
- want to change boot timing long-term: route that work through ADR-018 boot calibration, not ad hoc edits across scripts and docs

## 9. Reference Commands

Bootstrap:

```bash
cp .env.example .env
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py doctor
```

Recommended manual capture:

```bash
./scripts/launch_manual_capture_autoboot.sh manual_01
./scripts/extract_frames.sh manual_01
```

Automated run:

```bash
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py run \
  --rom gng \
  --source-profile gng \
  --rom-path /private/path/to/roms \
  --input-plan plans/generated/gng_gameplay.yaml \
  --frames-to-run 300
```

Recompile:

```bash
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py map compile \
  --device profiles/devices/keyboard_default.yaml \
  --controller profiles/controllers/arcade_2button.yaml \
  --game profiles/games/gngb/default_actions.yaml \
  --sequence plans/sequences/gng_gameplay.yaml \
  --out plans/generated/gng_gameplay.yaml
```

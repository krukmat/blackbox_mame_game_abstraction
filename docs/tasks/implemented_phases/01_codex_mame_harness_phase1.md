# Prompt — Codex MAME Harness Phase 1

Implement Phase 1 of the `blackbox_mame_game_abstraction` framework: MAME Harness.

## Context

The repo already contains the scaffold. We need a working Python CLI that can run MAME in a controlled way, using dry-run mode for tests and real mode when the user provides a MAME binary and game shortname.

## Scope

### 1. Implement `MameRunner`

It must accept:

```text
mame_binary
game_shortname
working_dir
rom_path
cfg_dir
nvram_dir
input_dir
state_dir
snapshot_dir
```

It must build deterministic command lines and support:

```text
record input file
playback input file
load save state slot/name
aviwrite output
mngwrite output
seconds_to_run or frames_to_run when available
autoboot_script for Lua
```

Expose `dry_run=True` to return command without executing.

### 2. Implement `CaptureManager`

Responsibilities:

```text
create evidence/private/run_<id> directory
create frames, video, logs, metadata subfolders
write run metadata JSON
refuse to write outside evidence/private unless explicitly configured for derived non-visual metadata
```

### 3. Implement `InputPlanner`

Responsibilities:

```text
load plans/basic_controls.yaml
validate button names
expand action sequences into frame-level input metadata
do not inject inputs into MAME yet; only record the intended plan
```

### 4. Implement `StateManager`

Responsibilities:

```text
reference named save states
support loading state identifiers
store state registry metadata, not save-state binary files in git
```

### 5. Implement Lua script template

Create:

```text
scripts/mame_autoboot.lua
```

Initial version:

```text
logs frame count
logs basic lifecycle events
does not read emulator memory in Phase 1
```

### 6. Tests

Add tests for:

```text
command construction
evidence path isolation
metadata creation
input plan parsing
Lua script path wiring
```

## Constraints

- No copyrighted game content.
- No ROM files.
- No committed videos or screenshots.
- No sprite extraction output.
- Keep everything clean-room and behavior-observation oriented.

## After implementation

- Run tests.
- Update README with exact local commands.

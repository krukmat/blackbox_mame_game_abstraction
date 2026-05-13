# MAME Runner

tags: #mame #runner #architecture

`apps/mame-harness/mame_runner.py`

## Responsibility

Build deterministic MAME command lines and execute them (or simulate execution in dry-run mode). Always return a structured result — never raise for operational outcomes.

## Key Types

### `MameRunRequest`
All run parameters. Notable fields:
- `game_shortname`: the MAME driver/game name (e.g., `"gngb"`)
- `source_profile`: optional `SourceProfile` — if set, enables preflight
- `dry_run`: if True, build command but don't execute
- Paths for `state_dir`, `snapshot_dir`, `aviwrite_path`, `record_input_file` are enforced as private-only via `ensure_private_evidence_path`

### `MameRunResult`
```python
status: str   # "dry_run" | "preflight_failure" | "execution_failure" | "success"
command: list[str]
preflight: PreflightResult | None
execution: MameExecution | None
```
See [[ADR-004 MAME Runner Structured Results]].

### `MameExecution`
Raw subprocess output: `returncode`, `stdout`, `stderr`.
⚠️ stdout/stderr may contain local machine paths — must be redacted before writing to public metadata.

## Flow

```
build_mame_command(request)
  → [optional] run_preflight(profile, mame_binary, rom_path)
      → if not ok: return MameRunResult(status="preflight_failure")
  → if dry_run: return MameRunResult(status="dry_run")
  → subprocess.run(command)
      → if returncode != 0: return MameRunResult(status="execution_failure")
      → else: return MameRunResult(status="success")
```

## Private Path Enforcement in Command Building

`build_mame_command` calls `_append_path_arg` with `enforce_private=True` for write destinations:
- `-state_directory` → must be under `evidence/private/`
- `-snapshot_directory` → must be under `evidence/private/`
- `-record` → must be under `evidence/private/`
- `-aviwrite` → must be under `evidence/private/`
- `-mngwrite` → must be under `evidence/private/`

ROM path and input directory are **not** enforced as private (they are read-only inputs, not write destinations).

## Related

- [[Source Profile]]
- [[Preflight]]
- [[ADR-004 MAME Runner Structured Results]]
- `apps/mame-harness/mame_runner.py`

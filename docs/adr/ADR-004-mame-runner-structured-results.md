# ADR-004 — MAME Runner Structured Result Objects

## Status
Accepted

## Date
2026-05-13

## Context

The original MAME runner design raised exceptions for all failure modes (binary missing, preflight failure, subprocess error). This made it difficult to:

- Distinguish between a dry-run success, a preflight failure, and a subprocess execution failure in downstream CLI code.
- Write unit tests that exercise each outcome without mocking `subprocess`.
- Produce structured public metadata that accurately records what happened during a run attempt.

Exception-driven flow also conflates "expected operational outcomes" (e.g., MAME not installed — a known precondition failure) with "unexpected errors" (e.g., bug in command construction).

## Decision

Replace exception-driven normal flow with typed structured result objects:

```python
@dataclass(slots=True)
class MameRunResult:
    status: str          # "dry_run" | "preflight_failure" | "execution_failure" | "success"
    command: list[str]
    preflight: PreflightResult | None = None
    execution: MameExecution | None = None
```

`run_mame` always returns a `MameRunResult`. It never raises for operational outcomes. The caller (`cli.py::handle_run`) reads `result.status` and maps it to a human-readable note via a plain dict lookup.

`PreflightResult` follows the same pattern — it is always returned, never raised:

```python
@dataclass(frozen=True, slots=True)
class PreflightResult:
    ok: bool
    profile_id: str
    mame_binary: str
    driver: str
    issues: tuple[PreflightIssue, ...]
    detected_version: int | None = None
    rom_zip_path: Path | None = None
```

Preflight is optional: if no `source_profile` is set on the request, preflight is skipped and `MameRunResult.preflight` is `None`.

## Consequences

**Positive**
- The CLI can produce complete public metadata for every run outcome, including failures, without try/except wrapping.
- Tests can exercise preflight_failure and execution_failure paths by controlling the request object, not by mocking subprocess at a low level.
- The `status` field maps cleanly to the `RunState.phase` state machine in `state_manager.py`.

**Negative**
- `status` is a plain `str` rather than an `Enum`, which means typos are not caught at definition time. A future refactor could introduce `RunStatus = Literal["dry_run", "preflight_failure", "execution_failure", "success"]`.
- `MameExecution.stdout` and `MameExecution.stderr` are captured verbatim from subprocess output. They may contain local machine paths that need redaction before being written to public metadata. The current `handle_run` writes them directly into the metadata dict. This is a known gap tracked in T05.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- `apps/mame-harness/mame_runner.py`
- `apps/mame-harness/preflight.py`
- `apps/mame-harness/cli.py` — `handle_run`
- `docs/tasks/gng_source_integration/T04-mame-runner-hardening.md`

# ADR-004 — MAME Runner Structured Result Objects

tags: #adr #runner

Status: **Accepted** | Date: 2026-05-13

> See the full ADR at `docs/adr/ADR-004-mame-runner-structured-results.md`

## Summary

`run_mame` always returns `MameRunResult(status, command, preflight, execution)`. Never raises for operational outcomes. Status values: `"dry_run"`, `"preflight_failure"`, `"execution_failure"`, `"success"`.

## Why Not Exceptions?

Exception-driven flow conflates expected operational outcomes (MAME not installed, wrong ROM path) with unexpected bugs. Structured results allow the CLI to produce complete public metadata for every outcome, including failures.

## Known Gap

`status` is a plain `str`, not an `Enum`. Typos are not caught at definition time.

`MameExecution.stdout`/`stderr` may contain local machine paths that need redaction before writing to public metadata. Currently written verbatim — tracked as an open gap.

## Related

- [[MAME Runner]]
- [[Source Profile]]
- [[Preflight]]

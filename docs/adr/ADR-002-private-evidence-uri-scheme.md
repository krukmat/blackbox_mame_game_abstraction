# ADR-002 — `private://` URI Scheme for Evidence References

## Status
Accepted

## Date
2026-05-13

## Context

Public metadata artifacts (e.g., `specs/run_metadata.json`) need to reference the private evidence session that produced them — for traceability and debugging purposes — without exposing the actual local filesystem path.

A run produces a session under `evidence/private/run_<id>/`. If the public metadata writes that absolute path, it would:

1. Leak a local machine path into a tracked artifact.
2. Violate the clean-room output rule (`BLOCKED_PUBLIC_PATH_MARKERS` includes `evidence/private/`).
3. Make the artifact machine-specific and non-reproducible.

An alternative would be to omit the reference entirely, but then there is no way to correlate a public spec artifact with the private evidence that produced it during a debugging or audit session.

## Decision

Introduce an opaque URI scheme `private://<run_id>` to reference evidence sessions in public metadata.

Rules:
- Command arguments that point into `evidence/private/run_<id>/` are rewritten to `private://<run_id>/<relative_suffix>`.
- The `private_evidence_ref` field in run metadata uses `private://<run_id>` as its value.
- The `guardrails.ensure_no_private_paths` check does **not** block `private://` URIs — they are the intended safe form.
- Any code that needs to resolve a `private://` URI to a real path must do so explicitly and only inside trusted local tooling, never in a public writer.

Implementation: `cli.py::_redact_command_paths` and the `private_evidence_ref` field in `handle_run`.

## Consequences

**Positive**
- Public metadata is traceable: a developer holding the `run_id` can find the private evidence locally.
- The `private://` prefix is visually distinct and grep-detectable — easy to audit.
- Passes the `ensure_no_private_paths` check because the blocked markers (`evidence/private/`, `/frames/`, `/crops/`) do not appear in the URI form.

**Negative**
- `private://` is not a real URI scheme — tooling that treats it as a URL will fail. This is intentional (it must not resolve externally) but can surprise developers.
- The current redaction logic in `_redact_command_paths` only rewrites paths that contain `evidence/private/`. An absolute path constructed differently (e.g., a symlink or `~`-prefixed path) would not be caught. A more robust approach would normalize all paths against the repo root before checking.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- [ADR-003](./ADR-003-public-output-blocklist.md)
- `apps/mame-harness/cli.py` — `_redact_command_paths`, `handle_run`
- `apps/mame-harness/guardrails.py` — `BLOCKED_PUBLIC_PATH_MARKERS`, `ensure_no_private_paths`
- `docs/tasks/gng_source_integration/T05.1-redaction-boundary-audit.md`

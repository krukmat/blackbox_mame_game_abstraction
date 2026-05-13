# ADR-002 — `private://` URI Scheme for Evidence References

tags: #adr #redaction

Status: **Accepted** | Date: 2026-05-13

> See the full ADR at `docs/adr/ADR-002-private-evidence-uri-scheme.md`

## Summary

Public metadata needs to reference evidence sessions for traceability. The solution is an opaque `private://<run_id>` URI that encodes the reference without exposing the local filesystem path.

## Key Rule

`_redact_command_paths` in `cli.py` rewrites any command argument containing `evidence/private/run_<id>/` to `private://<run_id>/<relative_suffix>`.

The `private_evidence_ref` field in run metadata is always `private://<run_id>`.

## Why Not Omit the Reference Entirely?

Without a reference, a public spec artifact cannot be correlated with the private evidence that produced it during debugging or audit. The `private://` scheme preserves traceability without exposure.

## Known Gap

The redaction only catches paths containing the literal string `evidence/private/`. Absolute paths resolved differently (symlinks, `~` expansion) are not caught.

## Related

- [[Private vs Public Boundary]]
- [[Guardrails]]
- [[ADR-001 Clean-Room Layered Architecture]]
- [[ADR-003 Public Output Blocklist]]

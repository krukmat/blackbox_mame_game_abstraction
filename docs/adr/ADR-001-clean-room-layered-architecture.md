# ADR-001 — Clean-Room Layered Architecture

## Status
Accepted

## Date
2026-05-13

## Context

The project goal is to study game behavior through MAME observation and produce an independent React Native game. This requires handling two fundamentally different kinds of data:

- **Private evidence**: raw frames, video, MAME logs, save states — material that may contain copyrighted expressive content and must never become a tracked or public artifact.
- **Public outputs**: abstract mechanics specifications, entity archetypes, asset recipes, behavioral validation reports — material that must be shareable, trackable, and legally safe.

Early drafts attempted to keep this separation informal (documented conventions only), but that approach would allow developer error to leak private paths or frame references into public specs without any enforcement at the code level.

The system also needs to be used by agents and contributors who may not fully understand the legal boundary. Enforcement must be structural, not advisory.

## Decision

Organize the codebase into four explicit layers, each with a strict trust boundary:

```
apps/mame-harness          CLI, runner, capture session, input planning, public metadata writer
packages/vision            Private-only frame manifest and motion analysis — numeric output only
packages/asset-factory     Abstract recipe generation from redacted entity candidates
packages/validation        Behavioral diff and validation report generation
apps/rn-prototype          TypeScript gameplay implementation — consumes public specs only
```

The boundary between private and public is enforced programmatically:

- `guardrails.py` defines `ensure_private_evidence_path`, `ensure_public_output_path`, and `ensure_no_private_paths`.
- All file writes on the public side must pass through `write_public_metadata` or an equivalent guardrail-aware writer.
- The vision layer (`packages/vision`) loads frames but never emits paths — it emits numeric motion summaries only.
- The `evidence/private/` tree is gitignored at the repo level.

## Consequences

**Positive**
- Any attempt to write a private path into a public spec raises a `ValueError` at write time, not at review time.
- The React Native prototype can be developed and tested without MAME, ROMs, or any private evidence on the machine.
- Contributors can work on public-facing packages without ever needing access to real captured evidence.

**Negative**
- The `sys.path` manipulation in `behavioral_validation.py` and `asset_recipe_generator.py` (inserting `packages/` subdirectories at runtime) is a workaround for the flat package layout. A proper namespace package or `pyproject.toml` workspace would be cleaner but would require Python packaging decisions that are deferred to a later phase.
- The vision layer is currently a stub. The numeric output contract exists but the real CV inference is not implemented.

## Alternatives Considered

**Single flat package**: simpler imports, but no structural enforcement of the evidence boundary. Rejected because the legal separation must be machine-verifiable, not advisory.

**Per-layer virtual environments**: maximally isolated but operationally impractical for a single developer workflow. Deferred.

## Related

- [docs/architecture.md](../architecture.md)
- [docs/legal_guardrails.md](../legal_guardrails.md)
- [ADR-002](./ADR-002-private-evidence-uri-scheme.md)
- [ADR-003](./ADR-003-public-output-blocklist.md)

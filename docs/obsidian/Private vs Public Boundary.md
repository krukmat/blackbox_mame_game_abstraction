# Private vs Public Boundary

tags: #architecture #guardrails #legal

The most fundamental architectural invariant in this project.

## What is Private

Everything under `evidence/private/run_<id>/`:

| Subdirectory | Contents | Format |
|---|---|---|
| `frames/` | Captured game frames | PGM (ASCII greyscale) |
| `video/` | AVI capture from MAME | AVI |
| `logs/` | Input recording files | MAME input format |
| `metadata/` | Private run metadata | JSON |
| `states/` | MAME save states | `.state` |

**All of this is gitignored and must never appear in tracked artifacts.**

## What is Public

Everything under `specs/`:

| File | Contents |
|---|---|
| `specs/run_metadata.json` | Redacted run metadata (no machine paths) |
| `specs/entities/*.json` | Numeric entity candidates (no image refs) |
| `specs/assets/*.yaml` | Abstract asset recipes |
| `specs/validation/*.yaml` | Golden master behavioral cases |
| `specs/validation/reports/*.json` | Behavioral validation results |

## How the Boundary is Enforced

Three mechanisms, each catching different attack surfaces. See [[Guardrails]].

1. **gitignore**: `evidence/private/` is gitignored → can't commit raw captures.
2. **Write-time guardrails**: `ensure_public_output_path` blocks writing blocked extensions or directories.
3. **Payload inspection**: `ensure_no_private_paths` scans string values in dicts/lists for path markers.

## The Reference Model

Private evidence is referenced in public metadata via `private://<run_id>` URIs.

See [[ADR-002 Private URI Scheme]].

## Related

- [[Guardrails]]
- [[ADR-001 Clean-Room Layered Architecture]]
- [[ADR-002 Private URI Scheme]]
- [[ADR-003 Public Output Blocklist]]
- `apps/mame-harness/guardrails.py`

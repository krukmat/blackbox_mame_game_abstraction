# ADR-001 — Clean-Room Layered Architecture

tags: #adr #architecture

Status: **Accepted** | Date: 2026-05-13

> See the full ADR at `docs/adr/ADR-001-clean-room-layered-architecture.md`

## Summary

The project is divided into four explicit layers. The key boundary is between `evidence/private/` (private) and everything else (public). This boundary is enforced programmatically via `guardrails.py`, not just by convention.

## Layers

| Layer | Location | Trust |
|-------|----------|-------|
| CLI + runner + capture | `apps/mame-harness/` | Bridges private and public |
| Vision (private-only) | `packages/vision/` | Reads private, emits numeric |
| Asset + validation | `packages/asset-factory/`, `packages/validation/` | Public only |
| RN prototype | `apps/rn-prototype/` | Public only, no MAME dependency |

## Why This Matters

Without structural enforcement, developer error can leak frame paths or private paths into public specs. The guardrail functions raise `ValueError` at write time, making leakage a test failure rather than a code review finding.

## Related

- [[Private vs Public Boundary]]
- [[Guardrails]]
- [[ADR-002 Private URI Scheme]]
- [[ADR-003 Public Output Blocklist]]

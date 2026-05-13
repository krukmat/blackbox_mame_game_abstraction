# ADR-006 — Vision Layer Emits Numeric Output Only

tags: #adr #vision #private

Status: **Accepted** | Date: 2026-05-13

> See the full ADR at `docs/adr/ADR-006-vision-layer-numeric-only-output.md`

## Summary

The vision layer is the only layer that reads private frame files. It validates every frame path with `ensure_private_evidence_path` on load. No frame path ever appears in a return value, log message, or serialized artifact.

## The Invariant

> Reads private paths → emits numeric summaries only.

Entity candidate records contain floats, ints, and abstract string labels. No paths.

## Current State

The vision pipeline is a **placeholder**. Entity candidates are synthetic — real pixel analysis is deferred. The architecture and output contracts are correct.

## Related

- [[Vision Layer]]
- [[Private vs Public Boundary]]
- [[ADR-001 Clean-Room Layered Architecture]]

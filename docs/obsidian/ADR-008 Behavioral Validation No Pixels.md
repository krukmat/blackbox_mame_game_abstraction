# ADR-008 — Behavioral Validation Without Pixel Comparison

tags: #adr #validation #testing

Status: **Accepted** | Date: 2026-05-13

> See the full ADR at `docs/adr/ADR-008-behavioral-validation-no-pixel-comparison.md`

## Summary

Validation compares abstract behavioral traces (`frame, entity_id, x, y, state, events, score_delta`) instead of screenshots. This is required because original screenshots are copyrighted and the RN prototype uses different art anyway.

## What is Validated

- Position within `movement_tolerance` (default 1.0)
- State (exact string match)
- Events (exact list match)
- Score delta (exact int match)

## What is Not Validated (intentionally)

- Visual appearance
- Frame images
- Pixel values
- Asset similarity to source game

## Related

- [[Behavioral Validation]]
- [[React Native Prototype]]
- [[Legal Guardrails]]

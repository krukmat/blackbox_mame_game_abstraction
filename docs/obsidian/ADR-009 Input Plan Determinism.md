# ADR-009 — Input Plan Determinism and YAML Definition

tags: #adr #input #determinism

Status: **Accepted** | Date: 2026-05-13

> See the full ADR at `docs/adr/ADR-009-input-plan-determinism.md`

## Summary

Input plans are YAML files with a fixed action vocabulary and frame counts. They are version-controlled, validated at load time, and expanded deterministically to per-frame action sequences. Same plan → same frame sequence every time.

## Why Determinism Matters

MAME observation runs must be reproducible. If the same input is applied to the same ROM at the same starting state, the output must be identical. Non-reproducible observation would make it impossible to correlate runs or build a stable abstract mechanics spec.

## Related

- [[MAME Runner]]
- [[Input Plan]]
- [[ADR-005 Source Profile Pattern]]

# ADR-026 — Internal-State Observation Boundary

tags: #adr #clean-room #decision-gate #mame #lua

**Status**: Accepted (T20.0, 2026-06-07) — constrained contract; clause 4 binding (memory ≠ published truth) | **Date**: 2026-06-07

## Problem

The mapping pipeline reconstructs all quantitative gameplay facts (positions, velocities,
identity) from rendered pixels, which forced per-entity CV signatures ([[ADR-012 Entity Signature-Based Player Identification]], [[ADR-021 Enemy Tracking Continuity]]), scroll-reset hacks ([[ADR-022 Scroll-Aware Vision Pipeline]]), and per-constant human pickers ([[ADR-019 Human-Validated Calibration Candidates]]). MAME's Lua bridge could instead read exact entity state from RAM using community cheat-DB addresses — but [[ADR-022 Scroll-Aware Vision Pipeline]] already rejected Lua introspection informally ("observational, not introspective"). This ADR formalizes that boundary as a deliberate decision.

## The two arguments

**For**: published output is unchanged (numbers only, [[ADR-006 Vision Layer Numeric Output]]); RAM values are facts, not expressive content; addresses are community facts, not ROM derivations; removes the dominant manual-labor/error source and scales across games ([[ADR-005 Source Profile Pattern]]).

**Against**: breaks the observational identity (ADR-022); widens the access footprint; makes provenance discipline load-bearing; the benefit may be obtainable via Levels 0–2 (input truth + designed experiments + modern vision) without crossing the line.

## Decision (contract if Accepted)

1. Addresses only from cited community cheat DBs, in a private/uncommitted config; no ROM disassembly.
2. Raw addresses/values are private (`evidence/private/`), never in public output or stdout.
3. Public output stays numbers-only; guardrails extended to reject addresses/raw values.
4. Memory is a measurement/verification source, **not** the published sole truth — public values stay explainable as observable behavior.
5. Graceful absence: no config → observational fallback, no loss of correctness.

If Rejected: T20.5/T20.6 dropped; modern vision ([[ADR-022 Scroll-Aware Vision Pipeline]] successors) becomes the primary positional source; ADR-022's rejection stands as formal policy.

## Recommendation

Accept under the constrained contract, scoped as a measurement/verification **accelerator and cross-check** (closing the [[ADR-019 Human-Validated Calibration Candidates]] `t_peak` failure mode), not as the published source of truth. Reject is defensible if posture purity is prioritized over automation. **Advisory only — the approver records the final decision.**

## Related

- [[ADR-001 Clean-Room Layered Architecture]]
- [[ADR-003 Public Output Blocklist]]
- [[ADR-006 Vision Layer Numeric Output]]
- [[ADR-019 Human-Validated Calibration Candidates]]
- [[ADR-022 Scroll-Aware Vision Pipeline]]
- Full ADR: `docs/adr/ADR-026-internal-state-observation-boundary.md`
- Plan: `docs/plans/automated_mapping_pipeline_plan.md`
- Task: `docs/tasks/automated_mapping_pipeline/T20.0-internal-state-observation-decision.md`

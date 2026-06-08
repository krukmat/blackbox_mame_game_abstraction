# ADR-023 — Ground-Truth Input Timeline

tags: #adr #input #clean-room #lua

**Status**: Accepted (T20.1, 2026-06-07) | **Date**: 2026-06-07

## Problem

Input-driven events (`movement_*`, `jump_start`, `fire`) *are* the player inputs the harness already injects via the MAME Lua bridge ([[ADR-009 Input Plan Determinism]]), yet they were re-derived from noisy computer vision in `trace_extractor._infer_events` — a contributing cause of the calibration inconsistencies that the [[ADR-019 Human-Validated Calibration Candidates]] picker workflow compensates for. Manual captures discarded input truth entirely.

## Decision

The Lua bridge records the **effective per-frame input state** (injected plan OR human keyboard) to a private `evidence/private/run_<id>/logs/input_timeline.json`, and this is the authoritative source for input-driven events. CV inference is demoted to a fallback.

- MAME 0.287 has no `ioport_field:read()`; the state is read from `ioport_port:read()` after applying the plan, normalized via `(value ~ defvalue) & mask`.
- Fixed `BUTTON_ORDER` → deterministic serialized array (a scripted timeline matches the plan exactly — HP-1).
- Private artifact; only frame indices + abstract button labels cross internally; the Lua prints a count, never the path ([[ADR-003 Public Output Blocklist]], [[ADR-006 Vision Layer Numeric Output]]).

## Output Contract

`[{ "frame": N, "buttons": ["right","button2"] }, ...]` — schema `packages/schemas/input_timeline.schema.json`.

## Related

- [[ADR-009 Input Plan Determinism]]
- [[ADR-003 Public Output Blocklist]]
- [[ADR-006 Vision Layer Numeric Output]]
- [[ADR-019 Human-Validated Calibration Candidates]]
- [[ADR-026 Internal-State Observation Boundary]]
- [[Input Plan]]
- Full ADR: `docs/adr/ADR-023-ground-truth-input-timeline.md`
- Implementation: `scripts/mame_autoboot.lua`, `apps/mame-harness/input_timeline.py`

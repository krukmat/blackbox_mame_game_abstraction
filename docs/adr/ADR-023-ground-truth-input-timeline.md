# ADR-023 — Ground-Truth Input Timeline

## Status

Accepted (T20.1, 2026-06-07)

## Date

2026-06-07

## Context

Player-driven events in the public trace — `movement_start/stop`, `jump_start`, `fire` —
are exactly the player inputs. The harness already *generates* and *injects* those inputs
deterministically through the MAME Lua bridge (`scripts/mame_autoboot.lua`, ADR-009).

Despite that, the event layer historically inferred these events from computer vision:
`trace_extractor._infer_events` derived `jump_start` from velocity-threshold transitions on
pixel-bbox centroids. This is noisy and was a contributing cause of the calibration
inconsistencies that the ADR-019 human-picker workflow was built to compensate for. For
manual captures (operator plays), the injected plan is not even available, so events were
inferred entirely from noisy vision.

Reading inputs back is not introspective in the ADR-022 sense: inputs are what a player
performs, fully observable. Capturing them does not cross the clean-room boundary — only
numbers/strings (frame index + abstract button labels) are recorded, and the artifact is
private.

## Decision

The MAME Lua bridge records the **effective per-frame input state** — injected plan OR human
keyboard — to a private artifact `evidence/private/run_<id>/logs/input_timeline.json`. This
timeline is the **authoritative source** for input-driven events. CV-based event inference is
demoted to a fallback used only when no timeline is present.

**Capture mechanism.** MAME 0.287 has no `ioport_field:read()`. The effective state is read
from `ioport_port:read()` after the plan is applied (so the read picks up both the
`field:set_value` override and any natural keyboard input for that frame), normalized across
active-low/active-high wiring via `(port_value ~ field.defvalue) & field.mask`. Buttons are
emitted in a fixed `BUTTON_ORDER` so the serialized array is deterministic.

**Artifact shape** (`packages/schemas/input_timeline.schema.json`):

```json
[ { "frame": 1500, "buttons": ["right", "button2"] }, { "frame": 1501, "buttons": [] } ]
```

**Clean-room contract.**
- The artifact is private (under `evidence/private/`, gitignored). It carries only frame
  indices and abstract button labels — no paths, no pixels, no copyright names.
- The Lua never prints the private timeline path to stdout; only a count
  (`blackbox_harness:input_timeline:written:<N>`), per ADR-003/ADR-006.
- The path is provided via `BLACKBOX_INPUT_TIMELINE_PATH`, or derived from the input-plan
  path when absent (graceful fallback).

## Consequences

**Positive**
- Input-driven events become ground truth for both scripted and manual captures, removing
  the dominant source of event noise and a major reason for per-constant human pickers.
- Deterministic: a scripted run's timeline matches the injected plan exactly
  (`input_timeline.timeline_matches_plan`), which is the HP-1 check for T20.1.
- Downstream (T20.2) can switch event derivation to the timeline behind a stable contract.

**Negative**
- Adds a per-frame port read and an in-memory timeline flushed on machine stop (negligible).
- The MAME-produced equality (real capture timeline == plan) is an operator integration
  check; it cannot run in CI without a ROM.
- The capture relies on the frame-notifier firing after natural input is polled; if a MAME
  version changes that ordering, the manual-capture read point must be revisited.

## Alternatives Considered

1. **Keep CV event inference.** Rejected as the default — it is the documented source of
   event noise. Retained only as a fallback when no timeline exists.
2. **Parse MAME `.inp` recordings.** `-record`/`-playback` capture inputs, but `.inp` is a
   version-sensitive binary format; reading the live port state in Lua is simpler and yields
   the same ground truth directly in the abstract button vocabulary.
3. **Read RAM input state.** Out of scope here and governed by ADR-026; unnecessary because
   inputs are observable without introspection.

## Related

- [ADR-009](./ADR-009-input-plan-determinism.md) — deterministic input plans this builds on
- [ADR-003](./ADR-003-public-output-blocklist.md) / [ADR-006](./ADR-006-vision-layer-numeric-only-output.md) — numeric/no-path output contract
- [ADR-019](./ADR-019-human-validated-calibration-candidates.md) — manual workflow this reduces
- [ADR-026](./ADR-026-internal-state-observation-boundary.md) — sibling input-source decision
- `scripts/mame_autoboot.lua` — capture implementation (T20.1)
- `apps/mame-harness/input_timeline.py`, `packages/schemas/input_timeline.schema.json`
- `docs/plans/automated_mapping_pipeline_plan.md`, `docs/tasks/automated_mapping_pipeline/T20.1-input-state-logger.md`

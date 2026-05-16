# ADR-018 — Boot Calibration Emits Abstract Timing Markers Only

## Status
Accepted

## Date
2026-05-16

## Context

The current boot workflow for GNG depends on fixed frame counts embedded directly in public input plans such as `plans/gng_boot_only.yaml` and `plans/gng_gameplay.yaml`. Those values are duplicated into scripts and documentation and are difficult to recalibrate safely.

The repository needs a calibration workflow that can reduce this fragility, but it must not:

- publish screenshots, frames, crops, or video-derived artifacts
- introduce pixel comparison as a validation or calibration method
- replace the current deterministic execution boundary
- turn boot calibration into a game-specific runtime rewrite

Any follow-up implementation also creates a new reusable pattern: a private observation step that emits a new public timing artifact. That boundary must be defined before implementation starts.

## Decision

Introduce boot calibration as a two-surface contract:

```text
private calibration session
  -> private evidence and private observation logs
  -> public boot calibration artifact
  -> generated public input plan YAML
  -> existing input_planner / Lua / MAME path
```

### Public Artifact

The public artifact is a clean-room-safe timing profile, not a media artifact and not an executable trace dump.

Recommended location:

```text
profiles/games/<driver>/boot_calibration.yaml
```

Recommended contents:

- profile type and profile id
- source profile and driver
- calibration method
- semantic boot phase markers
- frame counts or bounded frame windows
- optional durations derived from frame counts
- recommended deterministic plan steps
- status / human review field
- optional `private://<run_id>` provenance reference

The artifact may contain abstract timing/state metadata only.

### Forbidden Public Data

The artifact must not contain:

- screenshots
- videos
- frame paths
- crop paths
- OCR output from screen text
- per-frame image hashes
- raw visual feature vectors
- pixel comparison reports
- public payload strings that expose `evidence/private/`, `/frames/`, or `/crops/`

### Calibration Method Policy

The first implementation must use a hybrid manual-confirmation workflow. It may inspect private evidence locally, but the public output remains abstract.

Private-only automation such as controllability probes may be added later if they:

- remain private
- emit only abstract timing markers publicly
- do not use pixel comparison
- preserve the same public artifact contract

### Runtime Compatibility Rule

Boot calibration must not replace the current execution boundary.

The executable runtime remains:

```text
public input plan YAML
  -> input_planner.load_input_plan()
  -> private per-frame JSON
  -> scripts/mame_autoboot.lua
  -> MAME
```

Calibration changes how boot timing is derived, not how MAME is driven.

## Consequences

**Positive**

- Boot timing becomes a first-class public contract instead of duplicated comments and frame counts.
- Future recalibration can happen without exposing visual evidence.
- Existing determinism rules remain intact because the executable artifact is still a normal input plan.
- The artifact is reusable across games as a pattern without hardcoding visual heuristics into public plans.

**Negative**

- A new public artifact type requires schema, validation, and writer coverage.
- The first implementation still depends on operator confirmation rather than full automation.
- Future private automation must be careful not to expand into screen-classification scope without a separate decision.

## Alternatives Considered

**Keep hand-authored fixed waits only**

Rejected because the timing remains duplicated and recalibration stays ad hoc.

**Full automatic prompt detection**

Rejected for the first implementation because it would require broader private visual heuristics and would increase the risk of drifting into public visual diagnostics.

**Public per-frame boot trace**

Rejected because it creates a new public leakage surface and is unnecessary for the executable contract.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- [ADR-002](./ADR-002-private-evidence-uri-scheme.md)
- [ADR-003](./ADR-003-public-output-blocklist.md)
- [ADR-008](./ADR-008-behavioral-validation-no-pixel-comparison.md)
- [ADR-009](./ADR-009-input-plan-determinism.md)
- [ADR-014](./ADR-014-layered-input-mapping.md)
- [docs/boot_calibration_spike.md](../boot_calibration_spike.md)
- [docs/plans/layered_input_mapping_plan.md](../plans/layered_input_mapping_plan.md)
- `apps/mame-harness/cli.py`
- `apps/mame-harness/guardrails.py`
- `apps/mame-harness/input_planner.py`

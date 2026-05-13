# ADR-008 — Behavioral Validation Without Pixel Comparison

## Status
Accepted

## Date
2026-05-13

## Context

The React Native prototype needs to be validated against the observed game behavior. The natural approach in game testing is to compare screenshots pixel-by-pixel against a golden master. However:

1. Screenshots of the original game are copyrighted expressive content and cannot be committed or used as test fixtures in this project.
2. The RN prototype uses entirely new original assets — its visual output is intentionally different from the source game.
3. Pixel comparison would couple the test to the rendering implementation (font rendering, antialiasing, resolution) rather than to the gameplay semantics.

The goal of validation is to answer: **does the prototype behave the same way, not look the same way?**

## Decision

Use abstract behavioral traces for validation instead of screenshots.

A **trace** is a sequence of `TraceEntry` records, one per frame per entity:

```python
@dataclass(slots=True)
class TraceEntry:
    frame: int
    entity_id: str
    entity_type: str
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    state: str            # e.g., "grounded", "jumping", "dead"
    events: list[str]     # e.g., ["spawn", "hit", "score"]
    score_delta: int
```

`BehavioralDiff.compare` aligns observed and simulated traces by `(frame, entity_id)` and checks:
- position within a `movement_tolerance` (default: 1.0 unit)
- state match (exact string)
- event sequence match (exact list)
- score delta match (exact int)

The result is a `BehavioralDiffResult` with a `confidence` float (fraction of non-mismatched keys) and a list of human-readable mismatch descriptions.

Validation reports are written as both JSON (machine-readable) and Markdown (human-readable) to `specs/validation/reports/`.

Both output paths go through `ensure_public_output_path` and `ensure_no_private_paths` before write.

## Consequences

**Positive**
- Golden master cases (`specs/validation/golden_master_cases.yaml`) contain only abstract numeric and state data — safe to commit.
- The same validation framework works for MAME-derived traces and TypeScript simulation traces with no pixel or image dependency.
- Adding a new test case is as simple as adding a YAML entry — no screenshot tooling needed.

**Negative**
- The `movement_tolerance` default (1.0 unit) is a placeholder. The appropriate tolerance depends on the game's coordinate system scale, which is not yet determined from real captured evidence.
- State and event matching is exact string comparison. Small naming differences between the MAME observation layer and the RN simulation layer (e.g., `"jumping"` vs `"jump"`) will produce false mismatches. A canonical state vocabulary needs to be defined.
- The current `BehavioralDiff` does not support tolerance on events or score, only on position. Timing drift in event sequences (same event, one frame off) would count as a mismatch.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- `packages/validation/behavioral_diff.py`
- `apps/mame-harness/behavioral_validation.py`
- `specs/validation/golden_master_cases.yaml`
- `docs/tasks/implemented_phases/06_golden_master_validation_phase7.md`

# ADR-021 — Enemy Tracking Continuity via Generalized EntityTracker

tags: #adr #vision #entity-tracking #enemy

**Status**: Proposed (T10.8) | **Date**: 2026-05-24

## Problem

After [[ADR-012 Entity Signature-Based Player Identification]] gave the player cross-frame identity, non-player entities still got frame-indexed IDs (`enemy_a_{frame}_{region_index}`). A zombi visible for 30 consecutive frames produced 30 distinct `entity_id` values and 30 redundant `spawn` events. Tracked as a [[ADR-013 OpenCV Vision Backend]] Known Gap.

Without enemy continuity:
- [[React Native Prototype]] episode extraction cannot expose per-enemy motion arcs.
- [[Public Original Game Definition Layer]] encounter grammar (T12) cannot derive archetypes from a noise-flooded trace.
- [[Behavioral Validation]] cannot align observed vs simulated enemy behavior.

## Decision

Generalize `ArthurTracker` into a reusable `EntityTracker` keyed by `EntitySignature`. A single tracker, multiple per-type signatures, persistent IDs.

```python
@dataclass(slots=True)
class EntitySignature:
    entity_type: str                   # "enemy_a", "enemy_b", "player", ...
    height_min_px: int
    height_max_px: int
    center_y_min_px: int
    center_y_max_px: int
    aspect_ratio_min: float
    aspect_ratio_max: float
    max_frame_jump_px: float
    gap_tolerance_frames: int = 0

class EntityTracker:
    def __init__(self, signatures: list[EntitySignature]) -> None: ...
    def step(self, regions, frame) -> StepResult: ...  # tracked, spawned, died
```

**`ArthurTracker` becomes a backward-compatible wrapper** over a single-signature `EntityTracker`. All existing tests pass unchanged.

**Persistent ID scheme**: `{entity_type}_{spawn_frame}_{spawn_index}` — frame in the ID is the spawn frame, not the current frame. Stable across the entity's lifetime.

**Greedy nearest-neighbor matching** with per-type `max_frame_jump_px` ceiling. Greedy ordered by track `spawn_frame` ascending (oldest first). Hungarian assignment deferred.

**Per-type `gap_tolerance_frames`**: bridges short detection gaps. Track closes (`die` event emitted on last entry) when gap exceeded.

**Signature calibration via picker** ([[ADR-019 Human-Validated Calibration Candidates]]): `enemy_signature_picker.py` clusters candidate regions, operator validates against private PNGs, `enemy_signature_calibrator.py` writes `specs/calibration/gng_enemy_signatures.yaml`.

## Scope Boundary

**In scope (T10.8)**:
- Zombi (`enemy_a`) and crow (`enemy_b`) in stage 1 screen 1
- No camera scroll

**Deferred (T10.9)**:
- Red Arremer (devil)
- Stage 1 boss (cyclops)
- Requires resolving [[ADR-013 OpenCV Vision Backend]] MOG2 scroll-reset gap first

## Output Contract

All vision output remains numeric per [[ADR-006 Vision Layer Numeric Output]]. `EntitySignature` is numeric only. `TrackedEntity.entity_id` is a string with no copyright references. No path strings introduced.

## Known Limitations

- Greedy assignment can swap IDs when two same-type entities cross paths within `max_frame_jump_px`. Accepted for screen 1.
- MOG2 can absorb stationary enemies (zombi in grave). Mitigation: emergence motion breaks absorption.
- Boss tracking and stage 2+ scroll handling remain Known Gaps for follow-up work.

## Resolves

- [[ADR-013 OpenCV Vision Backend]] Known Gap: "Cross-frame enemy ID continuity is not implemented."

## Implemented In

- `packages/vision/entity_tracker.py` (T10.8.2 — new)
- `packages/vision/arthur_tracker.py` (T10.8.2 — refactored as wrapper)
- `packages/vision/trace_extractor.py` (T10.8.3 — integration)
- `apps/mame-harness/enemy_signature_picker.py` (T10.8.1 — new)
- `apps/mame-harness/enemy_signature_calibrator.py` (T10.8.1 — new)
- `specs/calibration/gng_enemy_signatures.yaml` (T10.8.1 — new)
- `packages/vision/tests/test_entity_tracker.py` (T10.8.2 — new)
- `packages/vision/tests/test_trace_extractor_enemies.py` (T10.8.3 — new)
- `packages/vision/tests/test_enemy_tracking_integration.py` (T10.8.4 — new)

## Related

- [[ADR-006 Vision Layer Numeric Output]]
- [[ADR-008 Behavioral Validation No Pixels]]
- [[ADR-012 Entity Signature-Based Player Identification]]
- [[ADR-013 OpenCV Vision Backend]]
- [[ADR-019 Human-Validated Calibration Candidates]]
- [[ADR-020 Projectile In-Flight Tracking]]
- [[Vision Layer]]
- Full ADR: `docs/adr/ADR-021-enemy-tracking-continuity.md`
- Plan: `docs/plans/T10.8-enemy-tracking-continuity.md`
- Task: `docs/tasks/gng_source_integration/T10.8-enemy-tracking-continuity.md`

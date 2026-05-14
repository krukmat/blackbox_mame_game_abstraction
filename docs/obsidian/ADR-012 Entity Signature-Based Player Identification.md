# ADR-012 — Entity Signature-Based Player Identification

tags: #adr #vision #entity-tracking #player

**Status**: Accepted | **Date**: 2026-05-14

## Problem

[[FrameDiffer]] produces one bounding box per frame — the union of all changed pixels. When multiple entities are on screen, this merges player, enemies, and projectiles into a single blob. [[TraceExtractor]] classifies that blob by area ratio, producing one wrong `TraceEntry` instead of separate correct entries per entity.

## Decision

Introduce `ArthurSignature` + `ArthurTracker` in `packages/vision/arthur_tracker.py`.

**ArthurSignature** is a configurable dataclass encoding the player character's geometric constraints:

```python
@dataclass(slots=True)
class ArthurSignature:
    height_min_px: int = 24      # standing + attack animations
    height_max_px: int = 36
    center_y_min_px: int = 155   # on-ground vertical band, 256×224 frame
    center_y_max_px: int = 195
```

**ArthurTracker** matches these constraints against the multi-region list produced by the updated [[FrameDiffer]] and returns the best candidate via nearest-neighbor from last-known position.

**FrameDiffer** is extended from single-bounding-box to **connected-component labeling** (4-connectivity flood fill, minimum 4 pixels per component).

**TraceExtractor** updated to emit one `TraceEntry` per entity per frame:
1. `ArthurTracker.find_arthur` → player region or `None`
2. Remaining regions → classified by area ratio (existing heuristic)
3. Player always gets `entity_id = "player"`

## Why Not a Generic `PlayerTracker`?

Only GNG exists as an observation target. Premature abstraction adds interface complexity without a second use case. When a second game requires its own signature, the refactor will be informed by real requirements.

## Output Contract

All output remains numeric-only per [[ADR-006 Vision Layer Numeric Output]]. `ArthurSignature` fields are ints. `ArthurTracker` returns `MotionBox` (all numeric) or `None`. No path references introduced.

## Known Limitations

- Signature calibrated for 256×224. A different native resolution requires new values.
- Crouch/death animations (height < 24 px) produce `None` — short gaps are bridged by `movement_tolerance` in [[ADR-008 Behavioral Validation No Pixels]].
- CC-labeling is O(pixels) per frame — acceptable offline, not real-time.

## Implemented In

- `packages/vision/arthur_tracker.py` (T10.5-B)
- `packages/vision/frame_differ.py` extended (T10.5-A)
- `packages/vision/trace_extractor.py` updated (T10.5-C)
- `packages/vision/tests/test_arthur_tracker.py` (T10.5-D)
- `packages/vision/tests/test_frame_differ_multi.py` (T10.5-D)

## Related

- [[ADR-006 Vision Layer Numeric Output]]
- [[ADR-008 Behavioral Validation No Pixels]]
- [[ADR-001 Clean-Room Layered Architecture]]
- [[Vision Layer]]
- Full ADR: `docs/adr/ADR-012-entity-signature-based-player-identification.md`
- Task: `docs/tasks/gng_source_integration/T10.5-arthur-tracker.md`

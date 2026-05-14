# ADR-012 — Entity Signature-Based Player Identification

## Status
Accepted

## Date
2026-05-14

## Context

The `FrameDiffer` layer produces a single bounding box per frame — the union of all changed pixels between consecutive frames. When multiple entities are on screen simultaneously (player character, enemies, projectiles), this bounding box merges all motion into a single region, making entity-level tracking impossible from a single aggregate blob.

`TraceExtractor.extract_trace` attempts to classify the aggregate region by area ratio (`_entity_type_from_box`) but has no way to produce separate `TraceEntry` records for different entities in the same frame. This means a frame where Arthur, an enemy, and a projectile are all moving produces exactly one entry — classified as whatever entity type the combined blob most resembles.

The first step toward multi-entity traces is identifying the player character reliably across frames. In Ghosts 'n Goblins (GNG), Arthur has a stable geometric signature when on the ground:

- Sprite height: 24–36 pixels (standing + attack animations)
- Vertical center position: y ∈ [155, 195] px in the 256×224 native frame
- The signature is narrow enough to reject most enemies and projectiles

A general solution (full multi-entity segmentation) requires per-game configuration and is deferred. The immediate need is a player-specific identifier that works for GNG and establishes a reusable pattern for future games.

## Decision

Introduce an `ArthurSignature` + `ArthurTracker` pair in `packages/vision/arthur_tracker.py`.

**ArthurSignature** is a dataclass that encodes the geometric constraints for the player entity of a specific game:

```python
@dataclass(slots=True)
class ArthurSignature:
    height_min_px: int = 24
    height_max_px: int = 36
    center_y_min_px: int = 155
    center_y_max_px: int = 195
```

Default values are calibrated from GNG's 256×224 native resolution. A future game would instantiate a different `ArthurSignature` (or a renamed equivalent) with its own values.

**ArthurTracker** consumes a list of `MotionBox` regions from a single frame and returns the one region that satisfies the signature, or `None` if none qualifies:

- `find_arthur(regions, sig) -> MotionBox | None`: filters by height and center_y; returns the best candidate by nearest-neighbor distance from the previous player position when multiple candidates qualify.
- `track_sequence(diffs, sig) -> list[MotionBox | None]`: applies `find_arthur` across a full diff sequence, carrying position state for nearest-neighbor disambiguation.

**FrameDiffer** is extended to produce multiple regions per frame using connected-component labeling over changed pixels, replacing the single global bounding box. `FrameDiffStat.changed_regions` is already typed as `list[MotionBox]`, so the contract is unchanged — only the cardinality increases.

**TraceExtractor** is updated in eight sequential steps (T10.5-C.1–C.4.c.2.b):
1. **C.1 — Player isolation**: call `ArthurTracker.find_arthur`; emit player `TraceEntry` with `entity_id = "player"` when a match is found; emit nothing for the player when `find_arthur` returns `None`.
2. **C.2 — Remaining regions**: classify each non-player region with `_entity_type_from_box`; emit one `TraceEntry` per region.
3. **C.3 — Per-entity prev_state**: replace the shared reverse-scan prev_state lookup with `prev_state_by_entity: dict[str, str]` and `prev_region_by_entity: dict[str, MotionBox]`, keyed by `entity_id`, so state never bleeds between player and enemies.
4. **C.4.a — Presence bookkeeping foundation**: replace `prev_seen: dict[str, int]` (keyed by `entity_type`) with `prev_seen_by_id: dict[str, int]` (keyed by `entity_id`).
5. **C.4.b — Spawn emission**: player gets one `spawn` on first appearance; enemies get `spawn` per ephemeral ID.
6. **C.4.c.1 — Disappearance detection**: compute which `entity_id` values are absent from the next frame.
7. **C.4.c.2.a — Last-entry resolution**: resolve the last real emitted entry for each disappearing `entity_id`.
8. **C.4.c.2.b — Die annotation**: append `die` to each resolved disappearing entity entry, without duplication.

All output remains numeric-only per ADR-006. No path references are introduced.

## Consequences

**Positive**
- Player character is reliably identified across frames, decoupled from the area-ratio heuristic that conflated player with enemies.
- Multiple entities in the same frame produce separate `TraceEntry` records — the trace is richer and more structurally accurate for behavioral validation (ADR-008).
- `ArthurSignature` is a configuration object, not hardcoded logic. Adding a second game requires instantiating new signature values, not branching the tracker code (resolves ADR-005 Known Gap pattern for the vision layer).
- Nearest-neighbor position tracking handles ambiguous frames (two regions both in the signature range) without arbitrary tie-breaking.

**Negative**
- The signature is calibrated for GNG at 256×224. A game at a different native resolution requires recalibration — the numeric px values are not resolution-independent ratios.
- Connected-component labeling over full-frame pixel diffs is O(pixels) per frame. For 256×224 frames at ~60 fps, this is approximately 3.4M pixel comparisons per second — acceptable for offline analysis but not real-time.
- The signature does not cover Arthur's crouch or death animations. Frames where Arthur is crouching (height < 24 px) or dying will return `None` from `find_arthur`, resulting in a gap in the player trace. This is acceptable — the behavioral validator uses `movement_tolerance` to bridge short gaps.
- The class is named `ArthurTracker` because this version is GNG-specific. Future games will need equivalent tracker classes with their own signatures. A generic `PlayerTracker(signature)` abstraction is deferred until a second game requires it — per the project's anti-premature-abstraction rule.

## Alternatives Considered

**1. ML-based entity segmentation**
Would generalize across games without per-game configuration. Rejected because it requires training data (private frames), introduces a model dependency, and is out of scope for the current clean-room observation phase.

**2. Color/palette-based segmentation**
GNG frames are grayscale PGM. Color segmentation is not available at this pipeline stage.

**3. Pure area-ratio classification (current approach)**
Kept as the fallback for non-player entities. Not sufficient alone because a combined player+enemy blob is classified as whichever entity type the merged area most resembles — producing a single wrong entry instead of two correct ones.

**4. Template matching**
Would require storing a reference frame crop of Arthur — private visual content that cannot be committed. Rejected on clean-room grounds.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- [ADR-006](./ADR-006-vision-layer-numeric-only-output.md)
- [ADR-008](./ADR-008-behavioral-validation-no-pixel-comparison.md)
- `packages/vision/frame_differ.py`
- `packages/vision/trace_extractor.py`
- `packages/vision/arthur_tracker.py` (introduced by T10.5)
- `docs/tasks/gng_source_integration/T10.5-arthur-tracker.md`

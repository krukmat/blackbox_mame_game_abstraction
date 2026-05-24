# ADR-021 — Enemy Tracking Continuity via Generalized EntityTracker

## Status

Proposed (T10.8)

## Date

2026-05-24

## Context

After ADR-012 introduced `ArthurSignature` + `ArthurTracker` for cross-frame player identity, the rest of the vision pipeline still treated non-player entities as ephemeral per-frame detections. `trace_extractor._entity_id_from_type` produces IDs of the form `{entity_type}_{frame}_{region_index}`, embedding the frame number into the identifier so that a single enemy detected over ten consecutive frames generates ten distinct `entity_id` values and ten redundant `spawn` events.

This was documented in ADR-013 as a Known Gap: "Cross-frame enemy ID continuity is not implemented — enemies remain ephemeral per-frame entities." The gap blocks:

- T11.2 episode extraction — episodes cannot expose meaningful per-enemy behavior because every frame creates new IDs.
- T12.3 encounter grammar — archetypes cannot be derived from a trace without per-enemy motion lifecycle.
- Behavioral validation (ADR-008) — trace comparison requires stable IDs to align observed vs simulated entity behaviors.

A second consideration: ADR-012 chose the name `ArthurTracker` deliberately to avoid premature generalization until a second use case existed. T10.8 is that second use case. Multiple enemy types of varying geometry and motion patterns appear concurrently in stage 1 screen 1, and a single tracker class with per-type signatures is the natural shape — generalizing now follows the existing project rule rather than adding a parallel hierarchy of `ZombiTracker`, `CrowTracker`, etc.

A third consideration: T10.7.E (projectile in-flight tracking) introduced cross-frame continuity for a single projectile type using a picker-based calibration workflow (ADR-019). That work is structurally identical to enemy tracking — both need persistent IDs, per-type signatures, and gap tolerance. Generalizing now lets T10.7.E and T10.8 share infrastructure rather than ship two parallel tracker implementations.

## Decision

Introduce a generalized `EntityTracker` in `packages/vision/entity_tracker.py` that supports multiple concurrent tracks across multiple signature types.

**EntitySignature** is the base configuration object:

```python
@dataclass(slots=True)
class EntitySignature:
    entity_type: str                   # canonical type label (T09.2 enum)
    height_min_px: int
    height_max_px: int
    center_y_min_px: int
    center_y_max_px: int
    aspect_ratio_min: float
    aspect_ratio_max: float
    max_frame_jump_px: float           # per-type velocity ceiling
    gap_tolerance_frames: int = 0      # per-type gap tolerance
```

`ArthurSignature` becomes an `EntitySignature` instance with the existing GNG-calibrated values; the dataclass identity is preserved as a named alias for readability and backward compatibility with existing tests.

**EntityTracker** consumes a list of `MotionBox` regions per frame and returns a list of `TrackedEntity` records — each with a stable `entity_id`, the matched `MotionBox`, and the `signature.entity_type`:

```python
class EntityTracker:
    def __init__(self, signatures: list[EntitySignature]) -> None: ...
    def step(self, regions: list[MotionBox], frame: int) -> StepResult: ...

@dataclass(slots=True)
class StepResult:
    tracked: list[TrackedEntity]
    spawned: list[TrackedEntity]       # subset of tracked: first frame for this id
    died: list[DiedEntity]              # tracks that closed this frame (gap exceeded)
```

Matching algorithm (greedy global, ordered by signature priority):

1. For each active track, predict next position = `last_position` (zero-order prediction; first-order velocity prediction is deferred until validation requires it).
2. For each region, compute the set of compatible signatures (height/center_y/aspect_ratio bounds satisfied).
3. Greedy assignment: iterate active tracks sorted by `spawn_frame` (oldest first), assign the closest compatible unassigned region within `max_frame_jump_px`.
4. Remaining unassigned regions become new tracks. Allocate `entity_id = f"{signature.entity_type}_{frame}_{spawn_index}"` where `spawn_index` disambiguates simultaneous spawns of the same type.
5. Active tracks with no assignment increment `missing_frames`. When `missing_frames > signature.gap_tolerance_frames`, the track closes (emit `die` on the entity's last-seen entry — done by the trace extractor, not the tracker itself).

**ArthurTracker** remains as a backward-compatible API:

```python
class ArthurTracker:
    def __init__(self) -> None:
        self._tracker = EntityTracker([ArthurSignature()])

    def find_arthur(self, regions, sig, prev_center=None) -> MotionBox | None: ...
    def track_sequence(self, diffs, sig) -> list[MotionBox | None]: ...
```

Internally it delegates to `EntityTracker` but exposes the existing single-entity contract. All existing tests pass unchanged.

**trace_extractor.extract_trace** is updated:

- Instantiate `EntityTracker` once, configured with the player signature and the enemy signatures loaded from `specs/calibration/gng_enemy_signatures.yaml`.
- Replace the manual player + remaining-region scan with `tracker.step(regions, frame)`.
- Per-entity `entity_id` comes from `TrackedEntity.entity_id` directly; the `{entity_type}_{frame}_{region_index}` scheme is removed.
- `spawn` events are emitted for entities in `StepResult.spawned`.
- `die` events are emitted retroactively on the last entry of entities in `StepResult.died`.

**Enemy signature calibration** follows the ADR-019 picker pattern:

- `apps/mame-harness/enemy_signature_picker.py` clusters candidate motion regions and presents frame ranges to the operator for accept/reject.
- `apps/mame-harness/enemy_signature_calibrator.py` consumes accepted clusters and produces `specs/calibration/gng_enemy_signatures.yaml`.

All vision-layer output remains numeric only per ADR-006. No path references are introduced.

## Consequences

**Positive**

- Cross-frame enemy continuity is structurally enforced. The same physical enemy keeps the same `entity_id` across all frames in which it is detected.
- `ArthurTracker` and enemy tracking share infrastructure — one matching algorithm, one bug surface, one set of regression tests.
- T11.2 episode extraction can build encounter timelines with per-enemy motion arcs.
- T12.3 encounter grammar can be calibrated from real per-enemy velocity and lifecycle data.
- Adding a new game requires a new set of `EntitySignature` instances, not a new tracker class. ADR-012's deferred generic abstraction is now justified by two concrete use cases.

**Negative**

- Greedy nearest-neighbor assignment can produce ID swaps when two same-type enemies cross paths within `max_frame_jump_px` of each other. This is an accepted limitation for screen 1, where path crossings are rare. Hungarian assignment is deferred.
- Stationary enemies waiting in a spawn point may be absorbed into the MOG2 background model. ADR-013 already documents this; T10.8 does not resolve it. Mitigation: enemies that matter (about to emerge or already moving) introduce motion that breaks static absorption.
- The refactor touches one of the most-tested files in the vision layer (`arthur_tracker.py`). Regression risk is non-trivial; mitigated by the wrapper pattern preserving the public API exactly.
- Stage 2+ camera scroll remains a Known Gap (ADR-013) and is out of T10.8 scope. The tracker will produce degraded output on scrolling stages, just as it does today.
- Boss tracking (Red Arremer, cyclops) is deferred to T10.9. The infrastructure is ready, but signature calibration for bosses requires either pre-scroll appearances or resolving the scroll gap.

## Alternatives Considered

**1. Per-type tracker classes (`ZombiTracker`, `CrowTracker`)**

Would mirror ADR-012's deferred-generalization rule literally. Rejected because the matching algorithm is identical across types — branching into N classes duplicates the same nearest-neighbor logic N times and complicates testing. ADR-012 explicitly anticipated this generalization when a second use case appeared.

**2. Hungarian assignment instead of greedy**

Would optimally resolve cross-path ambiguity. Rejected for the initial implementation because (a) screen 1 has few cross-path scenarios, (b) the `O(n³)` complexity is not justified at the current scale (≤ 6 simultaneous entities), and (c) greedy with `max_frame_jump_px` gives correct results in the cases validated so far. Deferred to a follow-up if validation gates fail.

**3. Tracker per ROI (left/right halves of the screen)**

Rejected because GNG enemies traverse the full width of the screen as part of normal play. Spatial partitioning would introduce hand-off complexity worse than the problem it solves.

**4. ML-based multi-object tracking (e.g., SORT, DeepSORT)**

Out of clean-room scope. Requires training data (private frames) and introduces a model dependency. The current geometric+velocity approach is sufficient for the documented use cases.

**5. Defer enemy continuity entirely; encode lifecycle in T11.2 episode extractor**

Rejected because it pushes the same problem one layer down without solving it. The episode extractor would need to re-implement the matching to recover lifecycle from a flattened per-frame trace — duplicating work and breaking ADR-008's "trace is the canonical artifact" principle.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- [ADR-006](./ADR-006-vision-layer-numeric-only-output.md)
- [ADR-008](./ADR-008-behavioral-validation-no-pixel-comparison.md)
- [ADR-012](./ADR-012-entity-signature-based-player-identification.md)
- [ADR-013](./ADR-013-opencv-vision-backend.md)
- [ADR-019](./ADR-019-human-validated-calibration-candidates.md)
- [ADR-020](./ADR-020-projectile-in-flight-tracking.md)
- `packages/vision/entity_tracker.py` (introduced by T10.8)
- `packages/vision/arthur_tracker.py` (refactored by T10.8)
- `packages/vision/trace_extractor.py` (refactored by T10.8)
- `specs/calibration/gng_enemy_signatures.yaml` (introduced by T10.8)
- `docs/plans/T10.8-enemy-tracking-continuity.md`
- `docs/tasks/gng_source_integration/T10.8-enemy-tracking-continuity.md`

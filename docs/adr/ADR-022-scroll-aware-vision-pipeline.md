# ADR-022 — Scroll-Aware Vision Pipeline

## Status

Proposed (T10.9)

## Date

2026-05-24

## Context

ADR-013 introduced MOG2 background subtraction as the dominant motion-detection mechanism in the vision pipeline. MOG2 assumes a static camera: each pixel's history is modelled as a mixture of Gaussians fit to that specific pixel position over time. When the camera scrolls horizontally (as it does in every stage 2+ section of GNG and in the approach to the stage-1 boss), every background pixel changes its content simultaneously. MOG2 reports the entire frame as foreground until its history window flushes — typically 100+ frames at default settings — which masks every real entity motion during and immediately after the scroll.

`gng_vision_config.py` already has `reset_on_scroll: bool = True` declared, but no code reads it. The reset path was deliberately deferred when MOG2 was introduced; ADR-013 tracked it as a Known Gap.

The deferral was acceptable while all observation runs stayed in stage 1 screen 1 (no scroll). T10.9 changes that: reaching the stage-1 boss requires scrolling past several screens of the cemetery, and the boss encounter itself happens in a post-scroll camera position. Without scroll handling the boss is effectively invisible to the vision layer.

A second consideration: any future work on stage 2+ (volcano, jail, etc.) inherits the same blocker. Resolving it inside T10.9 unblocks a much larger surface than just the cyclops.

## Decision

Introduce a `ScrollDetector` in `packages/vision/scroll_detector.py` that detects horizontal camera scrolls between consecutive frames and emits `ScrollEvent` records. The vision pipeline consumes these events to reset the MOG2 background model at scroll end and re-warm the model over a configurable warmup window.

```python
@dataclass(slots=True)
class ScrollEvent:
    frame_start: int            # first frame where shift > threshold
    frame_end: int              # first frame where shift falls back below threshold for >= debounce frames
    total_shift_px: int         # accumulated horizontal shift across the event
    direction: str              # "left" | "right"

class ScrollDetector:
    def __init__(
        self,
        shift_threshold_px: int = 2,
        max_shift_px: int = 16,
        scroll_streak_frames: int = 3,
        post_scroll_debounce_frames: int = 3,
    ) -> None: ...

    def step(
        self,
        prev_frame: np.ndarray,
        curr_frame: np.ndarray,
        player_mask: np.ndarray | None = None,
        frame_index: int = 0,
    ) -> ScrollEvent | None: ...
```

**Detection algorithm**:

1. For each consecutive frame pair, compute the integer horizontal pixel-shift `dx ∈ [-max_shift_px, +max_shift_px]` that maximizes cross-correlation between the previous frame and the current frame shifted by `dx`.
2. Optionally exclude a `player_mask` region (`ArthurTracker.find_arthur` bounding box dilated by 4 px) so Arthur's large moving sprite does not dominate correlation.
3. When `|dx| >= shift_threshold_px` for `scroll_streak_frames` consecutive frames, declare scroll-start. Continue accumulating `total_shift_px`.
4. When `|dx| < shift_threshold_px` for `post_scroll_debounce_frames` consecutive frames, close the event and emit `ScrollEvent`.

**Pipeline integration**:

The vision pipeline (`vision_pipeline.extract_run_trace` or equivalent) runs the scroll detector alongside the frame differ. When a `ScrollEvent` closes:

1. The MOG2 background subtractor is rebuilt from scratch.
2. For the next `mog2_warmup_frames` frames, non-player entity output from `EntityTracker` is suppressed — the warmup region produces unreliable foreground masks.
3. `ArthurTracker` continues to operate because its signature is geometry-based, not background-subtraction-based.
4. After warmup, normal pipeline behavior resumes.

The suppression window is recorded in the trace as a structural gap (no `TraceEntry` records for non-player entities in that frame range). Consumers must treat the gap as "unknown", not "no entities present".

All output remains numeric per ADR-006. `ScrollEvent` carries no path references; the warmup gap is implicit in the trace by absence of entries, not by an explicit suppression flag (which would expand the public schema).

## Consequences

**Positive**

- The MOG2 model stays valid throughout multi-screen runs. Stage 1 boss frames produce coherent detections.
- Future stage-2+ work inherits a working scroll-aware pipeline without further refactor.
- Player tracking is unaffected — `ArthurTracker` is signature-based and survives MOG2 reset.
- The detector is a single new module with a narrow, testable surface.

**Negative**

- `mog2_warmup_frames` frames after each scroll have no enemy detections. This is a structural gap, not a bug — consumers must handle it explicitly.
- Pixel-shift correlation adds per-frame cost (O(2 · max_shift_px · pixels) per pair). At `max_shift_px=16` and 256×224 frames this is ~1.8M comparisons per frame — acceptable offline, not real-time.
- The detector assumes pure horizontal scroll. Vertical scroll (not present in GNG) would require extending the search to 2 DOF. Deferred.
- Player masking before correlation requires `ArthurTracker` to run first each frame. The pipeline order becomes: ArthurTracker → ScrollDetector → MOG2 → EntityTracker. This ordering must be enforced.

## Alternatives Considered

**1. Optical flow (Farneback dense flow)**

Would generalize to any motion, including parallax and vertical scroll. Rejected because (a) GNG scrolls only horizontally on stage 1, (b) Farneback is an order of magnitude slower than constrained correlation, (c) it adds an OpenCV-only dependency that constrains future vision-backend swaps (ADR-013 explicitly leaves the backend replaceable).

**2. ROM-state scroll address inspection (via MAME Lua)**

Would read the scroll register directly from the running emulator. Rejected on clean-room grounds — the project policy is observational, not introspective. Reading internal state bypasses the abstraction layer that the whole framework is designed to maintain.

**3. Reset MOG2 every N frames as a coarse fallback**

Would avoid the scroll detector entirely. Rejected because non-scroll frames are well-served by the existing MOG2 history, and periodic resets would re-introduce warmup windows in stage-1-screen-1 runs that currently work fine.

**4. Defer scroll handling until T12 stage-2+ work**

Rejected because the stage-1 boss falls inside T10.9's scope, and the boss encounter is post-scroll. Deferring would leave T10.9 incomplete or force a partial-stage-1 acceptance.

## Related

- [ADR-006](./ADR-006-vision-layer-numeric-only-output.md)
- [ADR-012](./ADR-012-entity-signature-based-player-identification.md)
- [ADR-013](./ADR-013-opencv-vision-backend.md)
- [ADR-021](./ADR-021-enemy-tracking-continuity.md)
- `packages/vision/scroll_detector.py` (introduced by T10.9)
- `packages/vision/frame_differ.py` (modified by T10.9 — MOG2 reset hook)
- `packages/vision/gng_vision_config.py` (modified by T10.9 — `reset_on_scroll` wired)
- `docs/plans/T10.9-boss-and-devil-tracking.md`
- `docs/tasks/gng_source_integration/T10.9-boss-and-devil-tracking.md`

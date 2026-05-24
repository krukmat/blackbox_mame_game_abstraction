# ADR-022 — Scroll-Aware Vision Pipeline

tags: #adr #vision #mog2 #scroll

**Status**: Proposed (T10.9) | **Date**: 2026-05-24

## Problem

[[ADR-013 OpenCV Vision Backend]] adopted MOG2 background subtraction assuming a static camera. When GNG scrolls horizontally — every stage 2+ section and the approach to the stage-1 boss — every background pixel changes content simultaneously and MOG2 reports the entire frame as foreground until its history flushes (100+ frames). This was tracked as a Known Gap and was acceptable while observation stayed in stage 1 screen 1.

[[T10.9 — Boss and Devil Tracking]] reaches the stage-1 boss, which exists only post-scroll. The gap becomes blocking.

## Decision

Introduce `ScrollDetector` in `packages/vision/scroll_detector.py` to detect horizontal camera scrolls between consecutive frames. The vision pipeline resets the MOG2 background model at scroll end and re-warms over the configured `mog2_warmup_frames` window.

```python
@dataclass(slots=True)
class ScrollEvent:
    frame_start: int
    frame_end: int
    total_shift_px: int
    direction: str            # "left" | "right"

class ScrollDetector:
    def step(prev_frame, curr_frame, player_mask=None, frame_index=0) -> ScrollEvent | None: ...
```

**Algorithm**: integer pixel-shift cross-correlation in `[-max_shift_px, +max_shift_px]`, with optional player-mask exclusion to prevent Arthur's large moving sprite from dominating correlation. Debounce via `scroll_streak_frames` (start) and `post_scroll_debounce_frames` (end).

**Pipeline order invariant**: `ArthurTracker → ScrollDetector → MOG2 → EntityTracker`. Player tracking continues during MOG2 warmup because [[ADR-012 Entity Signature-Based Player Identification]] is signature-based, not background-based. Non-player [[EntityTracker]] output is suppressed during warmup — the trace contains a structural gap, not noise.

**Reset at scroll-end, not scroll-start**: mid-scroll frames are unusable regardless of MOG2 state. Resetting at scroll-end captures the new static background cleanly.

## Output Contract

All numeric per [[ADR-006 Vision Layer Numeric Output]]. `ScrollEvent` carries no path references. Warmup gap is implicit in the trace by absence of entries — no new public schema field needed.

## Known Limitations

- Vertical scroll not supported (not present in GNG).
- Pixel-shift correlation is O(2 · max_shift_px · pixels) — bounded but non-trivial.
- Warmup window blinds non-player detection for `mog2_warmup_frames` post-reset. Consumers must treat the gap as "unknown".

## Resolves

- [[ADR-013 OpenCV Vision Backend]] Known Gap: "MOG2 background model must be reset when the camera scrolls."

## Alternatives Rejected

- **Farneback dense optical flow**: order of magnitude slower; over-engineered for 1-DOF problem; backend-locked.
- **ROM-state scroll address inspection via MAME Lua**: violates clean-room observational policy.
- **Periodic blind reset**: re-introduces warmup windows in static-camera runs that currently work fine.

## Implemented In

- `packages/vision/scroll_detector.py` (T10.9.1 — new)
- `packages/vision/frame_differ.py` (T10.9.1 — MOG2 reset hook)
- `packages/vision/gng_vision_config.py` (T10.9.1 — `reset_on_scroll` wired)
- `packages/vision/trace_extractor.py` (T10.9.1 — warmup-suppression consumer)
- `packages/vision/tests/test_scroll_detector.py`
- `packages/vision/tests/test_pipeline_scroll_integration.py`

## Related

- [[ADR-006 Vision Layer Numeric Output]]
- [[ADR-012 Entity Signature-Based Player Identification]]
- [[ADR-013 OpenCV Vision Backend]]
- [[ADR-021 Enemy Tracking Continuity]]
- [[Vision Layer]]
- Full ADR: `docs/adr/ADR-022-scroll-aware-vision-pipeline.md`
- Plan: `docs/plans/T10.9-boss-and-devil-tracking.md`
- Task: `docs/tasks/gng_source_integration/T10.9-boss-and-devil-tracking.md`

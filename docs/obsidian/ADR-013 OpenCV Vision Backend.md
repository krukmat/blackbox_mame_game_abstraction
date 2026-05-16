# ADR-013 — OpenCV Vision Backend

tags: #adr #vision #opencv

Source: `docs/adr/ADR-013-opencv-vision-backend.md`
Task: `docs/tasks/gng_source_integration/T10.6-opencv-vision-backend.md`

## Decision

Replace the pure-Python consecutive-frame diff in [[Vision Layer]] with OpenCV as a replaceable backend, using MOG2 background subtraction, HUD ROI masking, and player gap tolerance to fix three structural problems in the current trace quality.

## Why

Three measurable failures in the T10.5 trace drove this decision:

| Problem | Metric | Fix |
|---------|--------|-----|
| Arthur standing still → no diff signal | 76% miss rate (769/3162 frames) | MOG2 background subtraction |
| GNG HUD pixels → hazard noise | 144k spurious hazard entries | ROI mask: bottom 20px excluded |
| Quiet-frame gaps → spawn/die cascade | 111 player spawns instead of 1 | Gap tolerance (3 frames) |

## Key Design Choices

**Adapter pattern** — `FrameDifferBackend` Protocol with two implementations:
- `PurePythonBackend` — current flood fill, used in all unit tests (no OpenCV needed in test environment)
- `OpenCVBackend` — cv2.connectedComponentsWithStats + MOG2, used in production runs

**GNGVisionConfig** — game-specific config dataclass:
- `hud_y_top: int = 204` — rows ≥ 204 are masked (bottom 20px of 256×224 frame)
- `mog2_history: int = 300` — MOG2 background model window
- `mog2_warmup_frames: int = 50` — first 50 frames use consecutive diff fallback
- `player_gap_tolerance: int = 3` — player absent ≤ 3 frames → suppress die

**ADR-006 contract maintained** — OpenCV reads private frames in memory, emits only numeric bounding boxes. No private paths in output.

## Known Gaps

- MOG2 must be reset on camera scroll (stage 2+). Stage 1 only for now.
- Cross-frame enemy identity continuity not implemented — enemies remain ephemeral per-frame IDs.

## Subtask Order

```
T10.6-A (adapter + install)
  → T10.6-B (HUD mask)
    → T10.6-C (cv2 contours)
      → T10.6-D (MOG2)
        → T10.6-E (gap tolerance)
          → T10.6-F (trace regeneration)
```

## Quality Targets (T10.6-F)

| Metric | Before | Target |
|--------|--------|--------|
| Player detection rate | ~24% | >60% |
| Player spawn count | 111 | 1 |
| Hazard entries | 144k | <5k |

## Related

- [[ADR-006 Vision Layer Numeric Output]] — numeric output contract maintained
- [[ADR-012 Entity Signature-Based Player Identification]] — ArthurTracker unchanged
- [[ADR-001 Clean-Room Layered Architecture]] — OpenCV stays inside the private vision layer
- `packages/vision/frame_differ.py`
- `packages/vision/gng_vision_config.py` (new)
- `packages/vision/trace_extractor.py`

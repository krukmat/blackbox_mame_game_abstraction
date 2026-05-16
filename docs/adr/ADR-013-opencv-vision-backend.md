# ADR-013 — OpenCV as Replaceable Vision Backend with Background Subtraction

## Status
Accepted

## Date
2026-05-14

## Context

The current `FrameDiffer` implementation uses consecutive-frame pixel diff in pure Python. This approach has three structural limitations that produce low-quality traces:

### Problem 1 — Stationary-entity blindness (76% player miss rate)

Consecutive-frame diff only detects pixels that *changed* between frame N-1 and frame N. When Arthur stands still, crouches mid-animation, or pauses between actions, his pixels are identical in both frames — producing zero diff signal. In manual_02 (3162 total frames), 1592 frames had empty diffs. The result is that Arthur is detected in only ~24% of frames, and gaps in detection trigger false spawn/die cascades (111 spawns instead of 1).

### Problem 2 — HUD noise (144k hazard entries)

GNG's HUD (score digits, lives indicator, timer) occupies the bottom ~20 rows of the 256×224 frame (y ≈ 204–223 px). Score digits change every frame the score increments; the timer decrements every second. These produce diff blobs in every active frame that pass the `hazard` classifier (`_entity_type_from_box` ratio < `_RATIO_PROJECTILE`). The result is 144k spurious hazard entries — 87% of all trace entries — that carry no behavioral information.

### Problem 3 — Python flood fill performance

The current `_connected_regions` implementation uses a Python set-based BFS flood fill: O(changed_pixels) with per-pixel set operations. For a 256×224 frame this is approximately 57k pixel comparisons per frame, which is acceptable but 10–50× slower than equivalent C++ operations. At scale (6000+ frames per run) this compounds.

### Why OpenCV now

ADR-012 introduced per-entity detection (ArthurTracker) which makes trace quality directly observable. The current trace quality is insufficient for T10.4 artifact validation and T11 RN prototype consumption. OpenCV resolves all three structural problems within the existing numeric-output constraint (ADR-006):

- `cv2.createBackgroundSubtractorMOG2()` builds a statistical background model over the frame sequence, detecting foreground pixels even when entities are stationary.
- ROI masking via numpy array slicing excludes the HUD region before any diff computation — no path strings, no image writes.
- `cv2.connectedComponentsWithStats()` replaces the Python flood fill with a C++ implementation that returns bounding boxes directly.

OpenCV reads private frames in memory and emits only numeric contour data (bounding boxes, centroids, areas). The ADR-006 contract — vision layer emits numeric output only — is fully maintained.

## Decision

### 1. Adapter pattern: `FrameDifferBackend` protocol

Extract the current diff logic behind a `FrameDifferBackend` protocol in `packages/vision/frame_differ.py`. Two concrete implementations:

- **`PurePythonBackend`** — current flood fill code, unchanged. Used in all unit tests (works with synthetic pixel lists, no OpenCV dependency).
- **`OpenCVBackend`** — new implementation backed by `cv2`. Used in production runs via `vision_pipeline.py`.

`FrameDiffer` accepts a backend at construction time; the default for real runs is `OpenCVBackend`. Tests continue to pass `PurePythonBackend` explicitly, so OpenCV is not a test dependency.

```python
class FrameDifferBackend(Protocol):
    def find_regions(
        self,
        prev_pixels: list[list[int]],
        curr_pixels: list[list[int]],
        frame_width: int,
        frame_height: int,
    ) -> tuple[float, list[MotionBox]]:
        ...
```

### 2. HUD exclusion via `GNGVisionConfig`

Introduce `GNGVisionConfig` (dataclass, `packages/vision/gng_vision_config.py`):

```python
@dataclass(slots=True)
class GNGVisionConfig:
    hud_y_top: int = 204      # rows >= hud_y_top are masked (bottom 20px of 224px frame)
    min_contour_area: int = 4  # pixels — same as current MIN_COMPONENT_PIXELS
```

Before diff computation, the OpenCVBackend zeros out the mask in `[hud_y_top:, :]`. The PurePythonBackend ignores the config (existing tests pass unmodified). Vision pipeline passes `GNGVisionConfig()` when running against GNG evidence.

### 3. `OpenCVBackend` contour extraction

Replaces the Python BFS flood fill:

```
1. Build diff mask: np.abs(prev - curr) > threshold  (threshold=10, grayscale)
2. Apply HUD mask: mask[hud_y_top:, :] = 0
3. cv2.connectedComponentsWithStats on mask → labels, stats, centroids
4. Filter by area >= min_contour_area
5. Produce MotionBox per component (x, y, width, height, center_x, center_y from stats)
```

Output type is `list[MotionBox]` — identical to current. The `FrameDiffStat` contract does not change. All downstream consumers (`ArthurTracker`, `TraceExtractor`) are unaffected.

### 4. Background subtraction (MOG2) for stationary entity detection

The `OpenCVBackend` builds a `cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=16, detectShadows=False)` model over the full frame sequence before producing per-frame diffs. The foreground mask from MOG2 replaces the consecutive-diff mask for frames after the model warm-up period (first 50 frames).

This detects entities that are stationary for multiple frames — the primary cause of the 76% player miss rate.

Known limitations:
- MOG2 requires reset when the camera scrolls (stage 2+). Stage 1 (manual_01, manual_02) is mostly static. A `reset_on_scroll: bool = True` flag is added to `GNGVisionConfig` but not implemented until T12.
- The warm-up period (first ~50 frames) falls inside the boot sequence (frames 0–1504 in manual runs), so no gameplay frames are lost.

### 5. Player gap tolerance in `TraceExtractor`

Independent of OpenCV but enabled by the improved detection: introduce `player_gap_tolerance: int = 3` in `extract_trace`. If the player is absent for ≤ 3 consecutive frames, suppress the `die` event and hold the last known position. This breaks the spawn/die cascade caused by quiet-frame gaps.

The gap tolerance is a `GNGVisionConfig` field (not hardcoded in `TraceExtractor`) so it remains game-configurable.

## Consequences

**Positive**
- Player detection rate is expected to increase from ~24% to >60% with MOG2 background subtraction.
- HUD noise (144k hazard entries) is eliminated entirely by the ROI mask.
- Player spawn count drops from 111 to 1 once gap tolerance bridges quiet-frame gaps.
- The adapter pattern ensures existing unit tests require zero changes — `PurePythonBackend` is the test default.
- `cv2.connectedComponentsWithStats` is 10–50× faster than the Python flood fill for large frames.
- `GNGVisionConfig` makes all numeric thresholds explicit and game-configurable.

**Negative**
- `opencv-python-headless` adds ~50 MB to the venv (pre-compiled binary wheel, no display dependency).
- MOG2 must be reset on camera scroll. Stage 2+ runs will require a scroll-detection gate before the model is trusted. This is documented as a Known Gap.
- The warm-up period produces coarser foreground masks for the first 50 frames (pure diff fallback). This is acceptable because manual_01/02 boot sequences have no gameplay in the first 1500 frames.
- `GNGVisionConfig` introduces a new game-specific config object. Adding a second game requires instantiating a different config — the same pattern as `ArthurSignature` (ADR-012).

## Known Gaps

- **MOG2 + camera scroll**: Background model becomes invalid when GNG scrolls horizontally (stage 2+). A scroll-detection gate is required before the model can be trusted. Not implemented in T10.6; tracked here.
- **Threshold `10` in diff mask**: The grayscale diff threshold (>10 counts as changed) is calibrated for GNG PGM frames. A game with more visual noise may need a higher threshold. Tracked in `GNGVisionConfig` as `diff_threshold: int = 10`.

## Alternatives Considered

**1. Sliding window diff (frame N vs frame N-K)**
Compare against frame K steps back instead of immediately preceding frame. Simpler than MOG2 and requires no warm-up. Rejected because it still misses entities stationary for more than K frames, requires K to be tuned per game, and adds O(K) memory for frame buffering with no better correctness guarantee than MOG2.

**2. Reference frame subtraction (diff against first frame)**
Diff every frame against a fixed "clean background" frame captured before any entity appears. More deterministic than MOG2. Rejected because GNG's opening screen contains sprites (title screen, player lives display) that differ from the in-game background — there is no guaranteed clean background frame without manual annotation.

**3. Full ML segmentation (YOLO, SAM)**
Would generalize across games. Rejected: requires training data (private frames), heavy model dependency, and is architecturally out of scope for the observation phase.

**4. Keep pure Python, fix gap tolerance only**
Would fix the spawn/die cascade but not the 76% miss rate or the HUD noise. Rejected as insufficient for T10.4 acceptance criteria.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- [ADR-006](./ADR-006-vision-layer-numeric-only-output.md)
- [ADR-008](./ADR-008-behavioral-validation-no-pixel-comparison.md)
- [ADR-012](./ADR-012-entity-signature-based-player-identification.md)
- `packages/vision/frame_differ.py`
- `packages/vision/gng_vision_config.py` (introduced by T10.6-A)
- `packages/vision/arthur_tracker.py`
- `packages/vision/trace_extractor.py`
- `docs/tasks/gng_source_integration/T10.6-opencv-vision-backend.md`

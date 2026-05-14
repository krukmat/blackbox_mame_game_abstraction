# Vision Layer

tags: #vision #evidence #private #numeric #entity-tracking

`packages/vision/` — the only layer that reads private frame files.

## Modules

### `frame_manifest.py`
- `FrameManifest.from_run(run_id, frames_dir, ms_per_frame)`: loads `.pgm` or `.png` files from a private evidence directory. Every path is validated with `ensure_private_evidence_path` before creating a `FrameRecord`.
- `FrameRecord` stores `private_path` internally. **This path is never serialized or included in any public output.**
- Timestamps are calibrated: `ms_per_frame` defaults to `GNG_MS_PER_FRAME` (16.768 ms, ~59.6374 fps) from `fps_calibration.py`.

### `frame_differ.py`
- `FrameDiffer.diff_manifest(manifest)`: computes per-frame motion between consecutive frames.
- `_diff_pair` returns a `FrameDiffStat` with `changed_regions: list[MotionBox]`.
- **T10.5-A extends this** from a single global bounding box to **N connected-component regions** (4-connectivity flood fill, minimum 4 px per component). Each independent motion blob becomes its own `MotionBox`.
- Output is numeric only — no image reference (ADR-006).

### `arthur_tracker.py` *(introduced in T10.5-B)*
- `ArthurSignature`: configurable geometric constraints for the player entity.
  - Default (GNG 256×224): `height ∈ [24, 36] px`, `center_y ∈ [155, 195] px`.
- `ArthurTracker.find_arthur(regions, sig, prev_center)`: returns the `MotionBox` that best matches the signature, or `None`.
  - Nearest-neighbor disambiguation when multiple candidates qualify.
- `ArthurTracker.track_sequence(diffs, sig)`: applies `find_arthur` across a full diff sequence.
- See [[ADR-012 Entity Signature-Based Player Identification]].

### `trace_extractor.py`
- `extract_trace(diff_stats, input_plan, frame_width, frame_height)`: assembles `TraceEntry` records.
- **T10.5-C updates this in four sequential steps:**
  - **C.1**: Wire `ArthurTracker.find_arthur` → emit player `TraceEntry` (`entity_id = "player"`) when found; skip player entry when `None`.
  - **C.2**: Classify remaining regions with `_entity_type_from_box`; emit one `TraceEntry` per region.
  - **C.3**: Replace shared prev_state reverse-scan with `prev_state_by_entity: dict[str, str]` and `prev_region_by_entity: dict[str, MotionBox]` — state never bleeds between player and enemies.
  - **C.4**: Replace `prev_seen: dict[str, int]` with `prev_seen_by_id: dict[str, int]`; player gets one `spawn`; enemies get `spawn` per ephemeral ID; `die` annotated on last seen entry.
- Rules 1–6 from T10.2.2.1 apply per entity, not per frame.
- State/event strings: canonical T09.2 vocabulary only.

### `entity_candidate_builder.py`
- `EntityCandidateBuilder.build_from_manifest(manifest)`: uses motion data to produce entity candidate records.
- Output fields are all numeric or abstract string labels:
  - `bbox_stats`: mean_width, mean_height, mean_x, mean_y (floats)
  - `motion_stats`: mean_motion, max_motion, active_frames (numeric)
  - `animation_estimate`: frame_count (int)
  - `interaction_hints`: list of abstract role strings (e.g., `"moving_actor"`)

### `hud_probe.py`
- Stub for HUD region detection (score display, lives counter). Not yet implemented.

## Frame Format

Frames are read as PGM P2 (ASCII greyscale) or PNG. The pipeline detects format from extension. MAME outputs AVI video; frames are extracted via ffmpeg before analysis.

Only P2 (ASCII) PGM is supported for `.pgm` files. P5 (binary PGM) is not supported (Known Gap, ADR-006).

## Timing Calibration

GNG native FPS: **59.6374 fps** (measured from three capture runs via ffprobe). `ms_per_frame = 16.768`. Source: `apps/mame-harness/fps_calibration.py`. Calibrated in T10.3.

## Invariant

> The vision layer reads private paths but never writes them. All output is numeric or abstract strings. Any function that takes a `private_path` must not forward that path to a return value, a log message destined for public output, or a serialized artifact.

## Related

- [[Private vs Public Boundary]]
- [[Asset Factory]]
- [[ADR-006 Vision Layer Numeric Output]]
- [[ADR-012 Entity Signature-Based Player Identification]]
- `packages/vision/`
- `docs/tasks/gng_source_integration/T10.5-arthur-tracker.md`

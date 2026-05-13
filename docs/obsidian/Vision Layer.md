# Vision Layer

tags: #vision #evidence #private #numeric

`packages/vision/` — the only layer that reads private frame files.

## Modules

### `frame_manifest.py`
- `FrameManifest.from_run(run_id, frames_dir)`: loads `.pgm` files from a private evidence directory. Every path is validated with `ensure_private_evidence_path` before creating a `FrameRecord`.
- `FrameRecord` stores `private_path` internally. **This path is never serialized or included in any public output.**
- Timestamps are synthetic (16ms per frame = 60fps approximation).

### `frame_differ.py`
- `FrameDiffer.diff(a, b)`: computes a motion mask between two consecutive frames. Returns a 2D list of delta values (0 = no change).
- Output is numeric only — no image reference.

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

Frames are read as PGM P2 (ASCII greyscale). This is a plain-text format readable without binary decoding. MAME can output MNG or PNG snapshots — conversion to PGM for local analysis is a planned step.

Only P2 (ASCII) PGM is supported. P5 (binary PGM) would require a different reader.

## Current State

The vision pipeline is a **placeholder**. The entity candidates it produces are synthetic (derived from frame count and a fixed motion pattern), not from real pixel analysis. The architecture and output contracts are correct; the CV implementation is deferred.

## Invariant

> The vision layer reads private paths but never writes them. All output is numeric or abstract strings. Any function that takes a `private_path` must not forward that path to a return value, a log message destined for public output, or a serialized artifact.

## Related

- [[Private vs Public Boundary]]
- [[Asset Factory]]
- [[ADR-006 Vision Layer Numeric Output]]
- `packages/vision/`
- `docs/tasks/implemented_phases/03_vision_layer_phase3.md`

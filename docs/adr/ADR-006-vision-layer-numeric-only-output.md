# ADR-006 — Vision Layer Emits Numeric Output Only

## Status
Accepted

## Date
2026-05-13

## Context

Frame analysis (motion detection, entity candidate extraction) requires reading private frame files. Those files are PGM images stored under `evidence/private/run_<id>/frames/`. They must never be referenced in public outputs.

The vision layer needs to:
1. Load frames from the private evidence directory.
2. Compare consecutive frames to detect motion regions.
3. Produce entity candidate records that downstream public writers can safely use.

The challenge is that entity candidate records may naturally include bounding box coordinates derived from frame content. These are numeric and safe. But the path to the source frame is not — it must not appear in public metadata.

## Decision

The vision layer (`packages/vision`) enforces two rules:

**Rule 1 — Frame records hold private paths internally, never emit them.**

`FrameRecord` stores a `private_path: Path` field. `FrameManifest.from_run` validates every frame path with `ensure_private_evidence_path` before creating the record. The path is used only for local pixel reads (`load_frame_pixels`) and is never serialized or included in any public-facing output.

**Rule 2 — Entity candidate builder emits numeric summaries only.**

`EntityCandidateBuilder` (in `packages/vision/entity_candidate_builder.py`) produces records with:
- `bbox_stats` (mean_width, mean_height, mean_x, mean_y — all floats)
- `motion_stats` (mean_motion, max_motion, active_frames — all numeric)
- `animation_estimate` (frame_count — int)
- `interaction_hints` (list of strings — abstract role labels, no path references)

No frame path, crop path, or image reference appears in an entity candidate record.

**PGM format choice**: the vision layer reads `.pgm` (portable greymap) files. PGM is a blocked public suffix (`.png`, `.jpg` are blocked; `.pgm` is currently not but the frame directory itself is blocked from public writes). PGM was chosen because MAME can write MNG/PNG snapshots, and the harness converts or reads them locally without exporting. At this stage frames are not actually captured in a real run — the vision pipeline is a placeholder that generates synthetic entity candidates.

## Consequences

**Positive**
- The public entity candidate JSON can be audited for path leakage by `ensure_no_private_paths` before write, and it always passes because numeric fields are never strings with path content.
- Tests for the vision layer can use synthetic PGM test fixtures without requiring a real MAME run.

**Negative**
- The vision pipeline is currently a stub. Real frame analysis (actual differencing, bounding box extraction) is not implemented. The entity candidates produced are synthetic placeholders derived from frame count and a fixed motion pattern. This is tracked as a future phase.
- Reading PGM files as text (the current `_read_pgm` implementation) is simple but brittle for binary PGM variants (P5 binary format). Only P2 (ASCII) PGM is supported. MAME snapshot output format compatibility needs verification.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- [ADR-003](./ADR-003-public-output-blocklist.md)
- `packages/vision/frame_manifest.py`
- `packages/vision/frame_differ.py`
- `packages/vision/entity_candidate_builder.py`
- `docs/tasks/implemented_phases/03_vision_layer_phase3.md`

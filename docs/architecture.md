# Architecture

The implementation is divided into four clean-room layers:

- `apps/mame-harness`: CLI, deterministic MAME command building, private capture session setup, input-plan expansion, and public metadata writing.
- `packages/vision`: private-only frame manifest loading and frame differencing that emit numeric motion summaries only.
- `packages/asset-factory` and `packages/validation`: public-output layers for abstract asset recipes and behavioral validation reports.
- `apps/rn-prototype`: a deterministic TypeScript gameplay core that consumes abstract specs rather than expressive source assets.

The key boundary is between `evidence/private/` and everything else:

- Private side: frames, video, logs, save-state directories, and any local-only evidence references.
- Public side: run metadata, entity candidates, asset recipes, validation cases, validation reports, and React Native-side gameplay specs.

No file writer on the public side is allowed to emit frame paths, crop paths, image paths, or blocked capture extensions.

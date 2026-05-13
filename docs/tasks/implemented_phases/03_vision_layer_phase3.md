# Prompt — Vision Layer Phase 3

Implement Phase 3: Vision Layer placeholders and first working frame analysis.

## Goal

Analyze locally captured frames and produce redacted entity candidate metadata.

Do not export sprite crops.  
Do not save original visual content outside `evidence/private`.

## Scope

### 1. `FrameManifest`

Implement a frame manifest loader that:

```text
loads a directory of frames from evidence/private/<run_id>/frames
creates an internal manifest with frame index, private path, dimensions, timestamp/frame number
never exposes private paths in public derived specs
```

### 2. `FrameDiffer`

Implement frame differencing that:

```text
compares consecutive frames
generates motion masks internally
outputs only redacted statistics:
  - changed_pixel_ratio
  - bounding boxes of changed regions
  - approximate center points
  - frame ranges
```

### 3. `EntityCandidateBuilder`

Implement entity candidate generation that:

```text
clusters moving bounding boxes across frames
creates entity_candidate.json with:
  - candidate id
  - bbox stats
  - motion stats
  - observed frame ranges
  - no image crop paths
  - no original pixel data
```

### 4. `HUDProbe` placeholder

Define an interface for detecting:

```text
score changes
lives changes
timer changes
```

No OCR dependency yet.

### 5. Tests

Add tests verifying:

```text
no output contains private frame paths
no image files are written to datasets/derived
entity candidates contain only numeric/statistical metadata
```

## Constraints

- Use OpenCV only if already configured; otherwise create an adapter interface and pure-Python placeholder.
- Do not add heavy ML models.
- Do not save visual crops.

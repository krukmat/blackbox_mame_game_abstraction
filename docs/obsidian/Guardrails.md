# Guardrails

tags: #guardrails #architecture #enforcement

`apps/mame-harness/guardrails.py` — the enforcement layer for the [[Private vs Public Boundary]].

## Functions

### `ensure_private_evidence_path(path)`
Validates that a path is under `evidence/private/`. Raises `ValueError` otherwise.
Used by: `CaptureSession`, `FrameManifest.from_run`, `build_mame_command` (for private write args).

### `ensure_public_output_path(path)`
Checks two things:
- Path suffix is not in `BLOCKED_PUBLIC_SUFFIXES` (images, video, audio, ROM, save states)
- No path component is in `BLOCKED_PUBLIC_DIRECTORY_NAMES` (`frames`, `video`, `crops`, etc.)
- Path does not start with `evidence/`

Used by: `write_public_metadata`, `write_asset_recipes`, `write_validation_reports`.

### `ensure_no_private_paths(payload)`
Recursively walks dict/list/str payloads. Raises `ValueError` if any string contains a path marker from `BLOCKED_PUBLIC_PATH_MARKERS` (`evidence/private/`, `/frames/`, `/crops/`).

Used by: every public metadata writer before serializing.

### `ensure_private_or_allowed_metadata_path(path, allow_public_metadata)`
Tries private first, falls back to public if `allow_public_metadata=True`. Used for the `public_metadata_dir` field in `CaptureSession`.

## Constants

```python
PRIVATE_EVIDENCE_ROOT = Path("evidence/private")

BLOCKED_PUBLIC_SUFFIXES = {
    ".zip", ".7z", ".rom", ".bin",
    ".png", ".jpg", ".jpeg", ".bmp", ".gif",
    ".mp4", ".avi", ".mov", ".mkv",
    ".wav", ".flac",
    ".state", ".sta", ".sav", ".chd",
}

BLOCKED_PUBLIC_PATH_MARKERS = (
    "evidence/private/",
    "/frames/",
    "/crops/",
)

BLOCKED_PUBLIC_DIRECTORY_NAMES = {
    "frames", "video", "videos", "crops", "screenshots", "states"
}
```

## Known Gaps

- The redaction in `cli.py::_redact_command_paths` only catches paths containing `evidence/private/` as a substring. Absolute paths constructed differently (symlinks, `~` expansion) would bypass it.
- `BLOCKED_PUBLIC_SUFFIXES` is a static set — new evidence types (e.g., `.webp`) need manual additions.
- `ensure_no_private_paths` normalizes backslashes but doesn't handle URL-encoded paths or `..` traversal.

## Related

- [[Private vs Public Boundary]]
- [[ADR-003 Public Output Blocklist]]
- [[ADR-002 Private URI Scheme]]

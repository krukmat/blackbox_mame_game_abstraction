# ADR-003 — Public Output Extension and Directory Blocklist

## Status
Accepted

## Date
2026-05-13

## Context

The clean-room rule forbids any public output from containing or referencing copyrighted expressive content: sprites, audio, video, screenshots, save states, ROMs. In practice, this means public file writers must not be able to produce files with those extensions or write into directories associated with visual/audio capture.

There are two surfaces to protect:

1. **File paths being written**: a public writer must not create `.png`, `.avi`, `.sav`, etc. files under tracked locations.
2. **Payload content**: a public metadata writer must not embed string values that contain paths to private frames, crops, or evidence directories.

Without machine enforcement, a developer under time pressure could inadvertently add an image comparison step or log a frame path into a public JSON file.

## Decision

Define two complementary blocklists in `guardrails.py`:

### Extension blocklist (`BLOCKED_PUBLIC_SUFFIXES`)
```python
{".zip", ".7z", ".rom", ".bin",
 ".png", ".jpg", ".jpeg", ".bmp", ".gif",
 ".mp4", ".avi", ".mov", ".mkv",
 ".wav", ".flac",
 ".state", ".sta", ".sav", ".chd"}
```
`ensure_public_output_path` raises `ValueError` if the output path has any of these suffixes.

### Directory blocklist (`BLOCKED_PUBLIC_DIRECTORY_NAMES`)
```python
{"frames", "video", "videos", "crops", "screenshots", "states"}
```
`ensure_public_output_path` raises `ValueError` if any component of the output path is one of these names.

### Path marker blocklist (`BLOCKED_PUBLIC_PATH_MARKERS`)
```python
("evidence/private/", "/frames/", "/crops/")
```
`ensure_no_private_paths` recursively walks any dict/list/str payload and raises `ValueError` if any string value contains one of these markers.

All three checks are required because they protect different attack surfaces:
- Extension check: prevents writing binary evidence files into tracked directories.
- Directory check: prevents writing any file (even a `.json`) into a `frames/` or `video/` subdirectory.
- Marker check: prevents embedding private paths as string values inside otherwise-safe JSON/YAML outputs.

## Consequences

**Positive**
- The three-layer approach catches the most common accidental leakage patterns without requiring policy knowledge from callers.
- Tests can verify the boundary by attempting blocked writes and asserting the `ValueError`.

**Negative**
- The blocklist is static. A new evidence type (e.g., `.webp` frames, `.ogg` audio) would not be caught without a manual update to `BLOCKED_PUBLIC_SUFFIXES`.
- The `ensure_public_output_path` check on directory names is broad: a legitimate spec file placed inside a directory named `states/` (e.g., `specs/states/game_states.json`) would be blocked even if it contains no visual evidence. Callers must avoid those directory names for public outputs.
- The path marker check uses string matching, not path normalization. A Windows-style backslash path would bypass it. `ensure_no_private_paths` normalizes backslashes before checking, but cross-platform edge cases remain.

## Alternatives Considered

**Allowlist approach**: only permit known safe extensions (`.json`, `.yaml`, `.md`, `.ts`). More restrictive and future-proof. Rejected because it would break legitimate internal tooling without a migration path.

**No enforcement, rely on gitignore**: the `evidence/private/` gitignore prevents committing raw captures, but does not prevent a public writer from embedding a frame path as a string in a tracked JSON file. Insufficient.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- [ADR-002](./ADR-002-private-evidence-uri-scheme.md)
- `apps/mame-harness/guardrails.py`
- `apps/mame-harness/metadata_writer.py`
- `docs/tasks/gng_source_integration/T05.2.1-sensitive-surface-inventory-consolidation.md`

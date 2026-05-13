# Legal Guardrails

tags: #legal #clean-room #compliance

## What is Forbidden

These are hard prohibitions with no exceptions:

- Committing ROMs to git (any format: `.zip`, `.rom`, `.bin`, `.chd`)
- Committing screenshots, videos, or audio of the original game (`.png`, `.jpg`, `.mp4`, `.avi`, `.wav`, etc.)
- Committing emulator save states (`.state`, `.sta`, `.sav`)
- Extracting, exporting, recoloring, or transforming original sprites
- Using original sprite crops as input to image generation tools
- Pixel-perfect comparison against original game screenshots
- Publishing frame paths, crop paths, or local evidence paths in public specs

## What is Allowed

- Observing game behavior locally through MAME (run-time only, not committed)
- Storing private evidence locally under `evidence/private/` (gitignored)
- Extracting **numeric** behavioral metadata (positions, timings, motion values) from private frames
- Describing abstract mechanics (locomotion, jump arc, gravity, state transitions)
- Generating asset recipes for **new original art** — with anti-similarity rules
- Implementing a new game in React Native using **new original assets**
- Validating behavior via abstract behavioral traces (no pixels)

## The Clean-Room Sequence

```
Observable behavior
  → abstract spec (numbers, state names, timings)
  → new asset recipe (with prohibited similarity rules)
  → new original asset (human-reviewed, similarity-checked)
  → new theme
  → independent implementation
```

NOT:

```
Original sprite → modified sprite → reused asset
```

## Code Enforcement

See [[Guardrails]] for the code implementation.

Key enforcement points:
- `evidence/private/` is in `.gitignore`
- `ensure_public_output_path` blocks writing image/video/ROM extensions to tracked locations
- `ensure_no_private_paths` blocks embedding path markers in public metadata strings
- Asset recipes require `human_review_required: true` and five prohibited similarity rules
- `build_mame_command` enforces private paths for all write destinations

## Related

- [[Guardrails]]
- [[Private vs Public Boundary]]
- [[Asset Factory]]
- [[ADR-003 Public Output Blocklist]]
- [[ADR-007 Asset Recipe Originality Contract]]
- `docs/legal_guardrails.md`
- `CLAUDE.md` — Critical Guardrails section

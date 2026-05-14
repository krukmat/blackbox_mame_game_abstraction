# T08 - Initial Private GNG Capture

## Status

🔄 In Progress

## Subtask Status

| Subtask | Title | Status |
|---------|-------|--------|
| T08.1 | Dry-run Verification | ✅ Done — 2026-05-13 |
| T08.2.1 | Pre-capture Environment Gate | ✅ Done — 2026-05-13 |
| T08.2.2 | Single 300-frame MAME Execution | ✅ Done — 2026-05-13 |
| T08.2.3 | Private Evidence Directory Layout Audit | ✅ Done — 2026-05-13 |
| T08.2.4 | Public Metadata Clean-room Audit | ✅ Done — 2026-05-13 |
| T08.2.5 | Capture Pipeline Fixes (aviwrite path + Lua API) | ✅ Done — 2026-05-13 |

## Subtask Files

- [T08.1-dry-run-verification.md](T08.1-dry-run-verification.md)
- [T08.2.1-pre-capture-environment-gate.md](T08.2.1-pre-capture-environment-gate.md)
- [T08.2.2-single-300-frame-mame-execution.md](T08.2.2-single-300-frame-mame-execution.md)
- [T08.2.3-private-evidence-directory-layout-audit.md](T08.2.3-private-evidence-directory-layout-audit.md)
- [T08.2.4-public-metadata-clean-room-audit.md](T08.2.4-public-metadata-clean-room-audit.md)

## Purpose

Run the first real local `gng` observation through the hardened harness and record private evidence only.

## Reference Reasoning

`High`

Reasoning basis:

- this is the first task that exercises the entire chain against real local tooling and source material
- it requires operational judgment around private evidence handling and reproducibility
- it can expose mismatches between design assumptions and the real MAME/ROM environment

## Scope

- execute one local capture using the profile-backed CLI path
- verify the capture directory layout under `evidence/private`
- verify the public metadata output remains clean
- record the exact command path used for repeatability

## Out of Scope

- publishing screenshots or videos
- sharing ROM-derived artifacts
- long capture campaigns

## Inputs

- working CLI integration from `T07`
- local MAME install
- local `gng.zip`

## Deliverables

- one successful private capture run
- one validated public metadata file for that run
- a short operator note describing how to reproduce the capture

## Dependencies

- `T07`

## Blocks

- `T09`

## Acceptance Criteria

- the capture completes successfully against the local MAME installation
- the run writes private evidence under `evidence/private/<run>`
- the public output contains only allowed redacted references

## Implementation Notes

- this task is intentionally a local-development milestone, not a CI artifact milestone

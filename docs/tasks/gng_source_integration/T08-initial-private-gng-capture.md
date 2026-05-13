# T08 - Initial Private GNG Capture

## Status

Planned

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

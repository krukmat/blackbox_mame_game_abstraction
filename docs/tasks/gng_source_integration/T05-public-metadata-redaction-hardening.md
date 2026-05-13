# T05 - Public Metadata Redaction Hardening

## Status

Planned

## Purpose

Ensure no public output leaks local machine paths, ROM locations, or private evidence internals beyond sanctioned opaque handles.

## Reference Reasoning

`High`

Reasoning basis:

- this task protects a clean-room and legal boundary rather than a purely technical contract
- the work must reason about all public output surfaces, not only the obvious `evidence/private` paths
- a false negative here directly undermines the repo's output rule

## Scope

- harden command redaction logic
- sanitize `rom_path` and any absolute local paths
- verify no public metadata includes frame paths, crop paths, or local workspace paths
- extend tests for leakage scenarios

## Out of Scope

- semantic content review of inferred mechanics
- generalized data classification framework

## Inputs

- runner output contract from `T04`
- current metadata writer and guardrails

## Deliverables

- updated redaction logic
- expanded path leakage tests
- documented public metadata contract

## Dependencies

- `T04`

## Blocks

- `T06`

## Acceptance Criteria

- public outputs never contain absolute local paths
- public outputs never contain direct ROM paths
- public outputs never contain frame or crop paths
- tests cover both `evidence/private` paths and unrelated absolute local paths

## Implementation Notes

- treat leakage prevention as a hard contract, not best-effort formatting

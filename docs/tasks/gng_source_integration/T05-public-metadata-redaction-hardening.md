# T05 - Public Metadata Redaction Hardening

## Status

Completed — 2026-05-13

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
- documented `T05` policy artifacts and subtask breakdown

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

## Execution Breakdown

`T05` is executed through the following subtasks:

1. `T05.1 - Redaction Boundary Audit` ✓
2. `T05.2 - Unified Redaction Policy` ✓
3. `T05.3 - Redaction Implementation` ✓
4. `T05.4 - Leakage Regression Tests` ✓
5. `T05.5 - Public Metadata Contract Documentation` ✓

Current `T05.2` artifacts:

- `T05.2.1 - Sensitive Surface Inventory Consolidation`
- `T05.2.2 - Allowed Public Forms`
- `T05.2.3 - Blocked Public Forms`
- `T05.2.4 - Redaction Decision Table`
- `T05.2.5 - Boundary Consistency Review`

Reference task artifacts:

- `T05.1-redaction-boundary-audit.md`
- `T05.2-unified-redaction-policy-subtasks.md`
- `T05.2.1-sensitive-surface-inventory-consolidation.md`
- `T05.2.2-allowed-public-forms.md`
- `T05.2.3-blocked-public-forms.md`
- `T05.2.4-redaction-decision-table.md`
- `T05.2.5-boundary-consistency-review-subtasks.md`
- `T05.2.5-final-boundary-synthesis.md`
- `T05.3-redaction-implementation-subtasks.md`

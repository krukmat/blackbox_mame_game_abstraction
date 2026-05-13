# T06 - GNG Contract Test Coverage

## Status

Planned

## Purpose

Add the automated tests that lock the `gng` integration behavior in place before CLI integration and real capture work proceed.

## Reference Reasoning

`Medium`

Reasoning basis:

- the task must translate design intent into durable executable contracts
- it requires selecting the right boundaries to test without overcoupling tests to local machine state
- the work is test-design-heavy rather than algorithmically complex

## Scope

- source profile tests
- preflight validation tests
- runner contract tests
- public redaction tests
- CLI-facing tests where appropriate

## Out of Scope

- live MAME execution in automated tests
- end-to-end oracle trace validation

## Inputs

- implementation contracts from `T02` through `T05`

## Deliverables

- Python unit tests covering the `gng` integration contract

## Dependencies

- `T05`

## Blocks

- `T07`

## Acceptance Criteria

- tests prove the `gng` profile resolves to `gngb`
- tests prove missing MAME and missing ROM are reported cleanly
- tests prove public metadata does not leak local paths
- the full Python suite passes under Python 3.11

## Implementation Notes

- keep tests CI-safe and deterministic
- avoid hidden reliance on a local real MAME install

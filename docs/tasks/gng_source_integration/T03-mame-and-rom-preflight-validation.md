# T03 - MAME and ROM Preflight Validation

## Status

Planned

## Purpose

Validate local MAME and ROM prerequisites before any run is attempted.

## Reference Reasoning

`Medium`

Reasoning basis:

- the task must convert external environment uncertainty into a stable programmatic contract
- it requires balancing enough validation for safety without importing unnecessary complexity from the sibling project
- failure modes must be explicit because later tasks depend on deterministic preflight behavior

## Scope

- verify MAME binary presence
- verify MAME `-version` invocation succeeds
- verify version satisfies the repo minimum
- verify ROM path or ROM zip presence for the `gng` profile
- verify the `gng` profile resolves to the intended driver contract
- return structured validation errors

## Out of Scope

- full ROM content hashing and canonical manifest enforcement unless needed for driver safety
- visual probe flows
- Lua script orchestration

## Inputs

- `gng` source profile from `T02`
- current local MAME path
- current local `gng.zip` location

## Deliverables

- preflight validation module
- structured error format for preflight failures
- tests for success and failure cases

## Dependencies

- `T02`

## Blocks

- `T04`

## Acceptance Criteria

- the repo fails fast with a clear message when MAME is missing
- the repo fails fast with a clear message when the ROM input is missing
- the repo encodes the correct driver contract for `gng`
- preflight results can be consumed programmatically by the runner and CLI

## Implementation Notes

- mirror the discipline of the sibling `gng` repo without importing its full toolchain model

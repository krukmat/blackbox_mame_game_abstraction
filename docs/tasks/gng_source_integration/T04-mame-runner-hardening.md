# T04 - MAME Runner Hardening

## Status

Planned

## Purpose

Refactor the Python MAME runner so it produces stable structured results for dry runs, preflight failures, and execution failures.

## Reference Reasoning

`Medium`

Reasoning basis:

- the task changes a core execution contract used by CLI and metadata generation
- it requires interface design, not just local implementation
- regressions are likely if success, dry-run, and failure paths are not modeled carefully

## Scope

- integrate preflight validation into the run path
- replace exception-driven normal flow with structured result objects
- preserve dry-run command building
- keep private evidence path enforcement intact

## Out of Scope

- advanced manual visual mode
- replay scripting system
- importing the TypeScript oracle harness

## Inputs

- current `mame_runner.py`
- preflight contract from `T03`

## Deliverables

- hardened runner interface
- backward-compatible or intentionally migrated call sites
- tests for dry-run, preflight failure, execution failure, and success

## Dependencies

- `T03`

## Blocks

- `T05`

## Acceptance Criteria

- runner callers can distinguish dry-run, validation error, and execution error without parsing raw exceptions
- successful runs still expose the executed command and process outputs
- private evidence path rules remain enforced

## Implementation Notes

- keep the surface area small and typed
- prefer an explicit result model over loosely formatted dictionaries

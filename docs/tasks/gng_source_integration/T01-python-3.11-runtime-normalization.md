# T01 - Python 3.11 Runtime Normalization

## Status

Planned

## Purpose

Ensure all Python execution in this repository uses Python 3.11 as already declared in project metadata.

## Reference Reasoning

`Low`

Reasoning basis:

- the task is operationally simple and locally bounded
- the main requirement is consistency with already-declared project constraints
- ambiguity is low and the expected output is mostly mechanical

## Scope

- confirm local command paths for `python3.11`
- confirm test execution uses `python3.11 -m pytest`
- update repo documentation where the default command path is ambiguous
- verify the local test suite passes with Python 3.11

## Out of Scope

- CI pipeline design
- multi-version Python support
- environment managers such as `pyenv`, `tox`, or `nox`

## Inputs

- `pyproject.toml`
- root `README.md`
- current local shell environment

## Deliverables

- documented canonical Python test command
- any required README clarification
- local verification note that Python 3.11 passes the suite

## Dependencies

- none

## Blocks

- `T02`

## Acceptance Criteria

- the repo clearly states Python 3.11 as the execution baseline
- the documented test command uses Python 3.11 explicitly where needed
- the current Python test suite passes under Python 3.11

## Implementation Notes

- keep this task minimal
- do not broaden the task into environment tooling work

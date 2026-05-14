# T07 - CLI Source Profile Integration

## Status

✅ Done — 2026-05-13

## Files and Lines Affected

| File | Change |
|------|--------|
| `apps/mame-harness/cli.py:14` | Replaced `from source_profiles import GNG_SOURCE_PROFILE` with `get_source_profile` |
| `apps/mame-harness/cli.py:41` | Added `run_parser.add_argument("--source-profile", default=None)` |
| `apps/mame-harness/cli.py:103` | Replaced hardcoded if-branch with `get_source_profile(args.source_profile) if args.source_profile else None` |
| `apps/mame-harness/tests/test_cli.py` | Added `_make_run_args` fixture and 5 new T07.2 tests |
| `apps/mame-harness/README.md` | Added Quick start section with `--source-profile` examples |

## Purpose

Expose the `gng` profile through the repository CLI so local runs use a safe, reproducible path instead of ad hoc manual flags.

## Reference Reasoning

`Medium`

Reasoning basis:

- the task sits at the boundary between user input, profile resolution, and runner contracts
- it requires preserving existing CLI behavior while adding a safer execution path
- mistakes here can bypass profile rules or reintroduce unsafe manual configuration

## Scope

- add CLI support for selecting a source profile
- resolve profile-backed MAME arguments
- keep public run metadata redacted
- preserve generic dry-run support

## Out of Scope

- major CLI redesign
- broad multi-profile UX work beyond what is needed now

## Inputs

- profile and validation contracts from `T02` through `T06`

## Deliverables

- CLI option for source profile selection
- profile-backed run path for `gng`
- updated CLI tests and usage docs

## Dependencies

- `T06`

## Blocks

- `T08`

## Acceptance Criteria

- a user can trigger a `gng` run without manually passing the critical driver-specific details
- dry-run output reflects the selected profile
- real-run setup still honors private evidence isolation and public redaction

## Implementation Notes

- prefer extending the existing `run` command over inventing a parallel command unless the interface becomes materially clearer

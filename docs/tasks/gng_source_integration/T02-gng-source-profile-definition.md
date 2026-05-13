# T02 - GNG Source Profile Definition

## Status

Planned

## Purpose

Create the canonical local source profile for observing the `gng.zip` ROM set through MAME in this repo.

## Reference Reasoning

`Medium`

Reasoning basis:

- the task defines a new canonical contract that later tasks will rely on
- it requires selecting the correct factual source constraints from the sibling `gng` project
- the implementation is still bounded, but mistakes here propagate into validation and capture work

## Scope

- define a source profile format or config object for `gng`
- encode the correct MAME driver for the local set
- encode expected ROM path inputs and base capture parameters
- document the intended private-only usage of the profile

## Out of Scope

- multi-game profile registry design beyond what is needed for one clean implementation
- automatic ROM discovery across arbitrary folders
- deep ZIP manifest validation parity with the separate `gng` repo

## Inputs

- local findings from the sibling `gng` project
- current `apps/mame-harness` CLI and runner interfaces
- legal and output constraints from `AGENTS.md`

## Deliverables

- one canonical `gng` source profile definition
- documentation of the profile fields and expected behavior

## Dependencies

- `T01`

## Blocks

- `T03`

## Acceptance Criteria

- the profile explicitly encodes `gngb` as the driver for the local `gng.zip` set
- the profile is stored in a repo location suitable for code consumption and maintenance
- the profile makes no public promise of faithful game reproduction

## Implementation Notes

- reuse the `gng` project only for factual source constraints such as driver selection
- keep the profile abstract enough to fit this repo's clean-room workflow

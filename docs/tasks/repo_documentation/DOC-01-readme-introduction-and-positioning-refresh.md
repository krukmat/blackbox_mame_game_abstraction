# DOC-01 - README Introduction and Positioning Refresh

## Status

Ready

## Objective

Improve the opening of `README.md` so a first-time technical reader can understand the repository's contribution quickly, especially how it differs from adjacent emulator, tooling, and RL projects, without weakening the clean-room framing.

## Scope

- update the README introduction and nearby framing sections
- clarify what the project is, what problem it solves, and what public outputs it produces
- explain the clean-room boundary in plain language
- explain how the project differs from adjacent tools such as MAME, RetroArch, BizHawk, Gym-style environments, and controller-mapping tools
- add a concise note describing the layered input mapping direction at a high level
- preserve existing technical sections, diagrams, quick start, repository layout, and contribution guidance unless small reordering improves readability
- keep examples and wording clean-room safe

## Out Of Scope

- changing repository behavior, commands, or implementation
- changing project status claims beyond what is already verified in repository files
- removing guardrail warnings
- adding screenshots, ROM paths, frame paths, crop paths, or any expressive game artifacts
- rewriting the README into product marketing copy
- introducing new architectural decisions or changing ADR scope

## Dependencies

- none for execution readiness
- must read the listed ADRs and overview docs before editing because the task touches public project positioning and clean-room boundary language

## Reasoning Grade

High

## Effort Grade

Low

## Recommended Model

GPT-5.5

## Acceptance Criteria

- `README.md` is the only required edited file unless a tiny supporting link adjustment is clearly necessary
- the opening explains the repository within the first 60-90 seconds of reading
- the README clearly distinguishes the project from adjacent tools
- the README consistently uses clean-room-safe language and does not read like a game cloning pipeline
- no private paths, frame paths, crop paths, screenshots, ROM locations, or expressive assets are introduced
- existing diagrams remain valid Mermaid or are replaced with clearer valid Mermaid
- quick start, repository layout, and contribution-relevant technical sections remain present
- any layered input mapping note stays high-level and consistent with ADR-014

## Reference Documents

- [Current task prompt](../../new%20reqs/blackbox_mame_mapping_handoff_updated/prompts/13_adjust_project_readme_intro.md)
- [Execution order note](../../new%20reqs/blackbox_mame_mapping_handoff_updated/EXECUTION_ORDER.md)
- [README.md](../../../README.md)
- [AGENTS.md](../../../AGENTS.md)
- [CLAUDE.md](../../../CLAUDE.md)
- [Layered Input Mapping Plan](../../plans/layered_input_mapping_plan.md)
- [ADR-001](../../adr/ADR-001-clean-room-layered-architecture.md)
- [ADR-003](../../adr/ADR-003-public-output-blocklist.md)
- [ADR-005](../../adr/ADR-005-source-profile-pattern.md)
- [ADR-014](../../adr/ADR-014-layered-input-mapping.md)
- [Project Overview](../../obsidian/00%20-%20Project%20Overview.md)

## Implementation Notes

- preserve factual current-state statements unless they are verified from repository files
- prefer clarifying and restructuring over expanding the README substantially
- treat this as repository-facing documentation work, not as an implementation task in the mapping pipeline

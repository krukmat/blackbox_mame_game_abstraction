# Blackbox MAME Game Abstraction — Agent Handoff Pack

This pack contains the architectural decision record and execution prompts for improving the first mapping phase of `blackbox_mame_game_abstraction`.

The goal is to reduce bootstrap friction by introducing a layered input mapping model while preserving the existing MAME harness.

## Core Decision

Introduce a compatibility layer:

```text
physical device profile
        ↓
canonical controller profile
        ↓
game action profile
        ↓
compiled input plan
        ↓
existing frame-level JSON / Lua / MAME execution
```

## Reading Order for the Agent

Read the files in this exact order:

1. `README.md` — this file.
2. `docs/ADR-0001-layered-input-mapping.md` — architectural decision, scope, risks, phases, and acceptance criteria.
3. `prompts/00_repository_orientation.md` — first prompt for Codex / Claude Code. Do not modify code yet.
4. `prompts/01_create_schemas_and_sample_profiles.md`
5. `prompts/02_add_mapping_profile_loader_and_validation.md`
6. `prompts/03_add_compiler_to_existing_input_plan.md`
7. `prompts/04_add_cli_map_validate_and_compile.md`
8. `prompts/05_documentation_update.md`

That sequence represents the recommended first PR.

After the first PR is stable, continue with:

9. `prompts/06_portable_environment_config_and_doctor.md`
10. `prompts/07_sdl_gamecontrollerdb_importer.md`
11. `prompts/08_retroarch_autoconfig_importer.md`
12. `prompts/09_cli_wizard_map_init.md`
13. `prompts/10_boot_calibration_spike.md`

For review or handoff between agent sessions, use:

14. `prompts/11_first_pr_review_prompt.md`
15. `prompts/12_compact_handoff_prompt_for_fresh_agent.md`

## Recommended Execution Strategy

### First session

Use:

```text
prompts/00_repository_orientation.md
```

The output should be a short technical summary, not code changes.

### First implementation PR

Use these prompts in order:

```text
prompts/01_create_schemas_and_sample_profiles.md
prompts/02_add_mapping_profile_loader_and_validation.md
prompts/03_add_compiler_to_existing_input_plan.md
prompts/04_add_cli_map_validate_and_compile.md
prompts/05_documentation_update.md
```

Do not include SDL importers, RetroArch importers, wizard, boot calibration, or major MAME harness rewrites in this first PR.

### Second PR

Use:

```text
prompts/06_portable_environment_config_and_doctor.md
```

This addresses local-machine assumptions and improves bootstrap portability.

### Later PRs

Use:

```text
prompts/07_sdl_gamecontrollerdb_importer.md
prompts/08_retroarch_autoconfig_importer.md
prompts/09_cli_wizard_map_init.md
prompts/10_boot_calibration_spike.md
```

These are intentionally deferred until the profile model is stable.

## Non-Negotiable Constraints

- Do not rewrite the MAME execution path in the first PR.
- Do not change the clean-room boundary.
- Public files must not contain ROMs, screenshots, audio, sprites, frame dumps, absolute local machine paths, or private evidence paths.
- Compile layered profiles into the current input plan format first.
- Keep schemas minimal.
- Add tests before introducing higher-level automation.
- Treat `gngb` as the first supported sample, not as a hardcoded architecture assumption.

## Definition of Done for First PR

The first PR is acceptable when:

- Existing tests pass.
- New tests pass.
- Sample layered profiles compile into a generated input plan.
- The generated input plan is parseable by the existing input planner.
- CLI supports `map validate` and `map compile`.
- Documentation explains the mapping layers.
- Public artifacts remain clean-room safe.

## Optional Documentation Prompt

After completing the repository orientation, use this prompt if the public positioning of the project needs to be improved before or alongside the technical refactor:

- `prompts/13_adjust_project_readme_intro.md`

Recommended usage: run it after `prompts/00_repository_orientation.md`, because the agent should understand the existing README and clean-room guardrails before rewriting the introduction. This prompt is intentionally separate from the mapping implementation sequence, so it can be executed as a documentation-only PR.


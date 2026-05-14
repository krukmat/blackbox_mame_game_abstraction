# CLAUDE.md

## Project Mission

This project builds a clean-room black-box game abstraction framework.

It observes a game running in MAME, captures private evidence, infers abstract gameplay mechanics, generates new original asset recipes, and supports an independent React Native implementation.

## Critical Guardrails

Never commit or generate as public output:

- ROM files
- original sprites
- original audio
- screenshots
- gameplay videos
- emulator save states
- copyrighted visual crops
- image-to-image derivatives of original sprites

Allowed outputs:

- abstract mechanics specs
- entity archetypes
- motion/timing metadata
- approximate collision metadata
- asset recipes for new original assets
- behavioral validation cases
- React Native implementation using new assets

## Clean-Room Rule

The framework may observe behavior but must not clone expressive content.

Use:

```text
observable behavior -> abstract spec -> new assets -> new theme -> independent implementation
```

Do not use:

```text
original sprite -> modified sprite -> reused asset
```

## Coding Standards

- Python 3.11+
- Type hints required
- Prefer dataclasses or Pydantic models
- Use pathlib
- Add tests for all guardrails
- Keep `evidence/private` gitignored
- Keep generated public specs free from original visual content

## Architecture Priorities

1. Reproducibility
2. Traceability
3. Legal/ethical separation
4. Deterministic validation
5. Mobile implementation readiness

## Testing

Every module that writes files must have tests proving it does not write private visual evidence into tracked directories.

Every asset recipe must include originality constraints.

## Architecture Decision Records

The `docs/adr/` directory contains the authoritative record of significant architectural and design decisions. Every agent must read the relevant ADRs before analyzing or implementing any feature that touches the boundaries they describe.

### ADR Index

| ADR | Decision | Touches |
|-----|----------|---------|
| ADR-001 | Four-layer clean-room architecture with programmatic enforcement | Any new module or package |
| ADR-002 | `private://` URI scheme for evidence session references | Any code that writes run metadata |
| ADR-003 | Three-layer public output blocklist (extension + directory + path marker) | Any public file writer |
| ADR-004 | Structured result objects in the MAME runner (no exceptions for operational outcomes) | `mame_runner.py`, CLI |
| ADR-005 | Source profile pattern; `gng.zip` must use driver `gngb` | Any game profile or preflight work |
| ADR-006 | Vision layer emits numeric output only — never path references | `packages/vision/`, entity candidates |
| ADR-007 | Every asset recipe must embed five prohibited similarity rules and `human_review_required: true` | `packages/asset-factory/` |
| ADR-008 | Behavioral validation uses abstract traces, never pixel or screenshot comparison | `packages/validation/` |
| ADR-009 | Input plans are deterministic YAML — same plan produces same frame sequence | `input_planner.py`, `plans/` |
| ADR-010 | Public original game definition layer between abstract mechanics and RN product work | T12 game definition artifacts, RN product direction |
| ADR-011 | Mechanics-to-scenario transformation and originality validation | T12 encounter grammar, scene recipes, validation gates |

### Known Gaps (consult before implementing)

These are documented limitations in the current implementation. An agent working in these areas must read the relevant ADR and treat the gap as a risk that may need to be resolved before the task can be marked complete.

- **ADR-002**: `_redact_command_paths` only catches `evidence/private/` as a literal substring. Absolute paths resolved via symlinks or `~` expansion bypass it.
- **ADR-003**: `BLOCKED_PUBLIC_SUFFIXES` is a static set. New evidence types (e.g., `.webp`) are not blocked without a manual update to `guardrails.py`.
- **ADR-004**: `MameExecution.stdout` and `stderr` are written verbatim to public metadata. They may contain local machine paths. Redaction of subprocess output is not yet implemented.
- **ADR-004**: `status` in `MameRunResult` is a plain `str`, not an `Enum`. Typos are not caught at definition time.
- **ADR-005**: Driver contract validation in `preflight.py` has a hardcoded `if profile.profile_id == "gng"` check. Adding a second game requires a new branch rather than a generic contract.
- **ADR-006**: The vision pipeline is a placeholder. Entity candidates are synthetic. Real pixel analysis is deferred.
- **ADR-006**: `_read_pgm` only supports P2 (ASCII) PGM. P5 (binary PGM) is not supported. MAME snapshot format compatibility needs verification.
- **ADR-007**: `suggested_new_theme_variants` are hardcoded identically for every entity. They should be varied.
- **ADR-008**: `movement_tolerance` default (1.0 unit) is a placeholder. Correct value depends on the game's coordinate scale, which is not yet determined from real captured evidence.
- **ADR-008**: State and event strings must match exactly. There is no canonical vocabulary — naming drift between observation and simulation layers causes false mismatches.

## Documentation and Vault

The `docs/obsidian/` directory is an Obsidian vault covering the full project. It contains:

- `00 - Project Overview.md` — pipeline, layout, ADR index, current phase status
- Module notes: `Guardrails`, `MAME Runner`, `Vision Layer`, `Asset Factory`, `Behavioral Validation`, `Source Profile`, `Preflight`, `Input Plan`, `React Native Prototype`, `Public Original Game Definition Layer`
- ADR summary notes with wikilinks
- `GNG Integration Plan.md` — T01–T11 task status table and next steps

Agents that need architectural context should read the relevant module note from `docs/obsidian/` before diving into source files. The module notes link directly to the source files and to the full ADRs they encode.

## Analysis Requirements

Before analyzing any existing module or proposing changes to it:

1. Read the ADR(s) that govern the module's boundary (see ADR Index above).
2. Check the Known Gaps list for any open risks in that area.
3. Read the corresponding module note in `docs/obsidian/` if one exists.
4. If the proposed change touches a clean-room boundary (private/public separation, asset recipe originality, validation method), bias the reasoning grade upward.

## New Feature Documentation Requirements

Every new feature that introduces an architectural decision must be documented before implementation begins.

A decision qualifies as architectural if it:
- introduces a new module, package, or layer
- changes how the private/public boundary is enforced or traversed
- changes how public outputs are written, redacted, or validated
- changes the asset recipe originality contract
- changes the behavioral validation method
- introduces a new external dependency or integration point
- establishes a new pattern that future tasks will replicate

When a feature qualifies:

1. Create a new ADR in `docs/adr/` following the existing format (Status, Date, Context, Decision, Consequences, Alternatives Considered, Related).
2. Create a corresponding summary note in `docs/obsidian/` with the same wikilink conventions as existing ADR notes.
3. Add the new ADR to the ADR Index table in both `CLAUDE.md` and `AGENTS.md`.
4. Add the new Obsidian note to the vault index in `docs/obsidian/README.md` and to the ADR index table in `docs/obsidian/00 - Project Overview.md`.
5. If the feature resolves a Known Gap, remove or update the gap entry in both `CLAUDE.md` and `AGENTS.md`.

ADR numbering: use the next available integer after the highest existing ADR number. Do not reuse numbers.

This documentation must be produced as part of the planning phase, before any implementation task begins.

## Planning Requirements

When asked to produce a plan, define the work as ordered tasks rather than as a loose idea list.

Each planned task must include:

- dependency order
- explicit dependencies
- reasoning grade
- effort grade
- recommended model

Use these task fields at minimum:

- Task ID and title
- Purpose
- Scope
- Out of scope
- Dependencies
- Reasoning grade: `Low | Medium | High`
- Effort grade: `Low | Medium | High`
- Recommended model
- Acceptance criteria

Planning constraints:

- the task list must be topologically ordered by execution dependency
- a task that blocks later work must appear before its dependents
- reasoning grade must reflect ambiguity, cross-module impact, and clean-room risk
- effort grade must reflect expected implementation and validation cost
- recommended model must be stated explicitly and should match task difficulty
- once a task or subtask has been assigned a reasoning grade or effort grade, do not change that cataloging implicitly later
- a previously assigned reasoning grade or effort grade may only change if the scope, dependency structure, or risk profile has materially changed
- any such recataloging must be stated explicitly and must include a short justification describing exactly what changed and why the new grade is warranted
- any plan presentation or task handoff must include a `Reference documents` section
- `Reference documents` must include the current task file, the parent plan file, `README.md`, `AGENTS.md`, and `CLAUDE.md` at minimum
- `Reference documents` must also include any ADR that governs the task's boundary (see ADR Index above)
- `Reference documents` must include the relevant `docs/obsidian/` module note if one exists
- add any additional task-specific docs required for safe execution and correct context loading

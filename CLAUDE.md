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

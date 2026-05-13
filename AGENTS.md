# AGENTS.md

## Objective

Build a clean-room black-box game abstraction framework.

The system observes games through MAME, captures private evidence, infers abstract mechanics, creates new asset recipes, and supports a React Native reimplementation.

## Forbidden

Do not:

- add ROMs
- add screenshots
- add videos
- add original sprites
- add audio captures
- add save states
- implement sprite ripping as a public output
- implement image-to-image transformation of original sprites
- create a clone-specific implementation

## Allowed

You may implement:

- MAME command runner
- dry-run command builder
- metadata capture
- frame manifest loading
- private evidence path management
- computer vision interfaces
- behavior inference interfaces
- abstract mechanics specs
- asset recipe generator
- originality guard placeholders
- React Native game engine scaffold

## Output Rule

All public output must be abstract.

Use this transformation:

```text
MAME observation
→ redacted metadata
→ abstract mechanics
→ new theme
→ new original assets
→ independent mobile game
```

## Test Requirements

Add tests for:

- private evidence isolation
- no generated asset uses original image paths
- no public spec includes frame paths or crop paths
- no output directory accepts ROM/video/screenshot extensions
- asset recipes include prohibited similarity rules

## Implementation Style

- Small commits
- Simple typed modules
- No unnecessary ML dependencies in early phases
- Prefer interfaces and placeholders over speculative complexity

## Planning Requirements

When a user asks for a plan, the plan must define tasks explicitly and in dependency order.

Every plan must include:

- tasks ordered by execution dependency
- an explicit dependency statement for each task
- the required reasoning grade for each task
- the expected effort level for each task
- the recommended model for each task

Use the following minimum planning fields per task:

- Task ID and title
- Objective
- Scope
- Out of scope
- Dependencies
- Reasoning grade: `Low | Medium | High`
- Effort grade: `Low | Medium | High`
- Recommended model
- Acceptance criteria

Planning rules:

- Do not present tasks as an unordered backlog when execution order matters.
- Do not omit dependency order when one task blocks another.
- Do not omit reasoning grade or effort grade.
- Recommended model must reflect real task difficulty and risk.
- If a task crosses a clean-room or public-output boundary, bias reasoning grade upward.

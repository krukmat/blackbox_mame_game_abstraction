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

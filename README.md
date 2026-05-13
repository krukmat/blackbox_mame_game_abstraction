# blackbox_mame_game_abstraction

This repository is a clean-room framework for studying how a game behaves through MAME and turning those observations into an independent new game.

The important point is the boundary:

- The system may observe behavior privately.
- The public outputs must stay abstract.
- The final mobile game must be original, independently themed, and built from new assets.

This is not a porting or cloning project.

## What the project is trying to do

The goal is to take a game that can be observed from the outside and build a new implementation based on mechanics, timing, collision rules, and interaction patterns rather than on copyrighted art or source material.

In practical terms, the repository is meant to support this workflow:

## Public pipeline

```text
MAME observation
-> redacted metadata
-> abstract mechanics
-> new theme
-> new original assets
-> independent mobile game
```

## What is public and what is private

There are two kinds of data in this project.

Private evidence:

- local frame captures
- local video
- local logs tied to a run
- emulator-side save-state references

Public outputs:

- redacted run metadata
- abstract mechanic and entity descriptions
- asset recipes for new original art
- behavioral validation cases and reports
- the independent gameplay prototype

Private evidence must stay under `evidence/private/` and must never leak into public specs.

## What this project does not do

The repository is explicitly designed to avoid clone-oriented or asset-reuse workflows.

It does not:

- store ROMs in git
- commit screenshots or gameplay video
- export original sprites or crops as public artifacts
- transform original sprites into derivative sprites
- validate by pixel-perfect image comparison
- produce a clone-specific implementation

## Current scope

The current implementation already covers the first useful layers of the pipeline:

- a Python MAME harness with deterministic dry-run command building
- private evidence session management
- input-plan loading and frame-level expansion
- redacted vision placeholders that emit numeric motion metadata only
- abstract asset recipe generation with originality guardrails
- a deterministic TypeScript gameplay prototype scaffold
- behavioral validation based on traces, timing, and events instead of pixels

## Repository layout

```text
apps/
  mame-harness/
  rn-prototype/
packages/
  schemas/
  vision/
  inference/
  asset-factory/
  validation/
docs/
  plans/
  tasks/
plans/
specs/
evidence/private/
```

## Guardrails

- Private evidence stays under `evidence/private/` and is gitignored.
- Public outputs may only contain redacted metadata, abstract mechanics, validation cases, and asset recipes.
- Asset generation must use abstract recipes only and must include originality constraints.
- ROMs, screenshots, videos, save states, and original expressive assets are forbidden as tracked outputs.

## Main entry points

There are two main areas in the repo:

- `apps/mame-harness`: Python tools for controlled observation, metadata capture, and public redacted outputs.
- `apps/rn-prototype`: TypeScript prototype for the independent gameplay implementation.

## CLI

The Python harness lives in `apps/mame-harness/cli.py`.

Typical commands:

```bash
python apps/mame-harness/cli.py init
python apps/mame-harness/cli.py run --rom pacman --dry-run --frames-to-run 300
python apps/mame-harness/cli.py analyze-placeholder --run-id demo
python apps/mame-harness/cli.py infer-placeholder
python apps/mame-harness/cli.py generate-asset-recipes-placeholder --entity-candidates specs/entities/sample_entity_candidates.json
python apps/mame-harness/cli.py validate-placeholder --observed-trace specs/validation/sample_observed_trace.json --simulated-trace specs/validation/sample_simulated_trace.json
```

What those commands mean:

- `init`: creates the expected directory structure.
- `run`: prepares or executes a MAME run; in `--dry-run` mode it only builds the command.
- `analyze-placeholder`: analyzes private frames and emits redacted entity metadata.
- `generate-asset-recipes-placeholder`: converts redacted entities into asset recipes for new art.
- `validate-placeholder`: compares abstract traces between observed behavior and the independent implementation.

## Development

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python3.11 -m pytest
cd apps/rn-prototype && npm install && npm test
```

## Current clean-room outputs

- `specs/run_metadata.json`: redacted run metadata with `private://` evidence references only.
- `specs/entities/sample_entity_candidates.json`: motion-only entity candidate metadata with no image paths.
- `specs/assets/sample_asset_recipes.yaml`: abstract asset recipe example with anti-similarity rules and human review requirements.
- `specs/validation/golden_master_cases.yaml`: behavioral assertions only; no pixel or audio comparison.

## If you want to understand the repo quickly

Read these files in this order:

1. `README.md`
2. `AGENTS.md`
3. `docs/legal_guardrails.md`
4. `docs/architecture.md`
5. `docs/clean_room_process.md`
6. `docs/plans/gng_source_integration_plan.md`
7. `docs/tasks/gng_source_integration/README.md`

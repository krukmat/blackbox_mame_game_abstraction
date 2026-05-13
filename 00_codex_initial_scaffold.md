# Prompt — Codex Initial Scaffold

You are working on a new repository called `blackbox_mame_game_abstraction`.

## Goal

Build the initial implementation scaffold for a black-box game abstraction framework. The framework must explore a game running in MAME, capture observable behavior, infer abstract mechanics, and support a clean-room React Native reimplementation with new original assets.

## Critical legal/ethical guardrails

- Do not implement ROM extraction.
- Do not extract, export, transform, recolor, or reuse copyrighted sprites.
- Do not store captured frames or videos in tracked git files.
- Evidence must remain local under `evidence/private/` and must be gitignored.
- The framework output must be abstract mechanics specs, entity archetypes, asset recipes, and validation metadata.
- Asset generation must use abstract recipes only, never original sprite crops as image-to-image input.

## Create the following

### 1. Repository structure

```text
apps/mame-harness
apps/rn-prototype
packages/schemas
packages/vision
packages/inference
packages/asset-factory
packages/validation
docs
specs
evidence/private
```

### 2. Documentation

Create:

```text
README.md
docs/architecture.md
docs/legal_guardrails.md
docs/exploration_strategy.md
docs/clean_room_process.md
docs/react_native_implementation_plan.md
```

### 3. Python package for `apps/mame-harness`

Create:

```text
cli.py
mame_runner.py
input_planner.py
capture_manager.py
state_manager.py
metadata_writer.py
tests/
```

Use `pytest`.

### 4. JSON schemas

Create:

```text
run.schema.json
input_plan.schema.json
entity_candidate.schema.json
mechanic.schema.json
asset_recipe.schema.json
validation_case.schema.json
```

### 5. Sample YAML files

Create:

```text
plans/basic_controls.yaml
specs/assets/sample_asset_recipes.yaml
specs/validation/sample_golden_master_cases.yaml
```

### 6. `.gitignore` rules

Add rules for:

```text
evidence/private/**
ROM files
video files
raw frame captures
emulator save states
generated private datasets
```

## Implementation constraints

- Use Python 3.11+.
- Use `pathlib`, `pydantic` or `dataclasses`, `subprocess`, `json`, `yaml`.
- No real MAME dependency is required for tests; provide dry-run mode.
- CLI must support:
  - `init`
  - `run`
  - `analyze-placeholder`
  - `infer-placeholder`
  - `generate-asset-recipes-placeholder`
  - `validate-placeholder`

## Testing

Add unit tests for:

- loading input plans;
- dry-run MAME command construction;
- ensuring private evidence paths are never placed under tracked output directories;
- validating asset recipes include prohibited similarity constraints.

## Deliverables

- Make the first commit-ready scaffold.
- Keep the code simple, typed, documented, and testable.
- Do not over-engineer.

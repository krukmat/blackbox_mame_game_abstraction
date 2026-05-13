# ADR-007 — Asset Recipe Originality Contract

## Status
Accepted

## Date
2026-05-13

## Context

The asset factory layer takes abstract entity candidate records and produces asset recipes for a new game theme. These recipes will eventually be used to commission or generate new original artwork.

The risk is that recipes could inadvertently describe the source game's visual style closely enough to constitute a derivative work. A recipe that says "create a knight character with armor identical to the protagonist of Ghosts'n Goblins" is not clean-room output.

Additionally, if recipes are fed as prompts into generative AI image tools, those tools could produce outputs similar to the original if the recipe does not include explicit anti-similarity constraints.

## Decision

Every asset recipe produced by `packages/asset-factory/recipe_generator.py` must include:

**1. Prohibited similarity rules** — a fixed list embedded in every recipe:
```python
PROHIBITED_SIMILARITY_RULES = [
    "do not reuse original palette",
    "do not copy original silhouette",
    "do not copy character identity",
    "do not use original crop as input",
    "do not copy animation frames",
]
```

**2. Originality guard block** — a machine-readable section requiring three similarity checks and human review:
```yaml
originality_guard:
  perceptual_hash_comparison: required
  silhouette_similarity_comparison: required
  palette_similarity_comparison: required
  human_review_required: true
```

**3. New theme variants** — every recipe includes at least three alternative theme suggestions, deliberately distant from the source game's aesthetic:
```python
"suggested_new_theme_variants": [
    "neon archaeology",
    "paper automata",
    "signal garden",
]
```

**4. Gameplay role abstraction** — recipes describe `gameplay_role` (e.g., `"moving_actor"`) and `size_class` (`"small"`, `"medium"`, `"large"`) rather than any identity tied to the source game.

The `write_asset_recipes` function calls `ensure_public_output_path` and `ensure_no_private_paths` before writing, providing a second layer of verification.

## Consequences

**Positive**
- Every recipe is self-documenting about its legal constraints — a downstream artist or AI pipeline reading the recipe knows what is prohibited.
- `human_review_required: true` is a machine-readable flag that an asset pipeline can use as a gate before accepting generated assets.
- The theme variants actively push creative direction away from the source material.

**Negative**
- The current prohibited similarity rules are static strings. They are advisory to humans and AI prompts, but there is no automated enforcement mechanism that actually checks whether a generated asset violates them. That check is deferred to the human review gate.
- The size classification (`_size_class` function) uses simple area thresholds derived from placeholder entity candidate data. Once real vision data is available, the thresholds and classification logic will need calibration.
- `suggested_new_theme_variants` are hardcoded as the same three themes for every entity. They should be varied or derived from the game's abstract mechanics to be more useful.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- [ADR-006](./ADR-006-vision-layer-numeric-only-output.md)
- `packages/asset-factory/recipe_generator.py`
- `apps/mame-harness/asset_recipe_generator.py`
- `docs/legal_guardrails.md`
- `docs/tasks/implemented_phases/04_asset_factory_phase5.md`
- `specs/assets/sample_asset_recipes.yaml`

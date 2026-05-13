# Asset Factory

tags: #assets #recipes #originality

`packages/asset-factory/recipe_generator.py`

## Purpose

Convert redacted entity candidates (numeric summaries from the [[Vision Layer]]) into abstract asset recipes that describe what kind of new original art to create — **without referencing, describing, or deriving from the original game's expressive content**.

## Pipeline

```
entity_candidates.json (numeric)
  → build_asset_recipes(candidates)
      → one recipe per candidate
  → write_asset_recipes(recipes, output_path)
      → ensure_public_output_path
      → ensure_no_private_paths
      → write YAML to specs/assets/
```

## Recipe Structure

Each recipe contains:

| Field | Type | Purpose |
|---|---|---|
| `id` | str | Derived from candidate_id (e.g., `asset_001`) |
| `gameplay_role` | str | Abstract role (`"moving_actor"`) |
| `size_class` | str | `"small"` / `"medium"` / `"large"` by pixel area |
| `approximate_canvas_size` | dict | width × height in pixels (from bbox stats) |
| `animation_frame_count` | int | From vision estimate |
| `motion_feel` | str | `"responsive_arcade_motion"` |
| `readability_requirements` | list | Contrast and silhouette requirements |
| `suggested_new_theme_variants` | list | Three alternative themes |
| `prohibited_similarity_rules` | list | Five anti-copy rules |
| `originality_guard` | dict | Three checks + `human_review_required: true` |

## The Originality Contract

Every recipe embeds five prohibited similarity rules and requires three automated similarity checks plus a human review gate before any generated asset is accepted. See [[ADR-007 Asset Recipe Originality Contract]] for the full reasoning.

## Known Limitations

- `suggested_new_theme_variants` are hardcoded (same three themes for every entity). Should be varied or derived from mechanics.
- `size_class` thresholds (area ≤ 16 = small, ≤ 64 = medium, > 64 = large) are placeholders — need calibration once real vision data is available.
- `gameplay_role` is always `"moving_actor"` regardless of entity type. A real inference layer would distinguish players, enemies, projectiles, pickups.

## Related

- [[Vision Layer]]
- [[Legal Guardrails]]
- [[ADR-007 Asset Recipe Originality Contract]]
- `packages/asset-factory/recipe_generator.py`
- `apps/mame-harness/asset_recipe_generator.py`
- `specs/assets/sample_asset_recipes.yaml`

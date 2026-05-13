# Prompt — Asset Factory Phase 5

Implement Phase 5: Asset Abstraction and Asset Recipe Generator.

## Goal

Convert redacted entity candidates into abstract asset recipes for new original assets.

Do not modify or transform original sprites.

## Input

Use `entity_candidate.json` files with:

```text
bbox stats
motion stats
animation estimates
interaction hints
```

## Output

Create:

```text
specs/assets/asset_recipes.generated.yaml
```

## Each asset recipe must include

```text
id
gameplay role
size class
approximate canvas size
animation frame count
motion feel
readability requirements
suggested new theme variants
```

## Each asset recipe must include prohibited similarity rules

Include:

```text
do not reuse original palette
do not copy original silhouette
do not copy character identity
do not use original crop as input
do not copy animation frames
```

## Each asset recipe must include originality guard configuration

Include placeholders for:

```text
perceptual hash comparison
silhouette similarity comparison
palette similarity comparison
human review required
```

## Important

The asset generator must not consume image files.  
It consumes only redacted metadata.

## Add tests proving

```text
no asset recipe contains source image paths
no asset recipe contains crop paths
each recipe has prohibited similarity rules
each recipe has human_review_required=true
```

# ADR-007 — Asset Recipe Originality Contract

tags: #adr #assets #legal

Status: **Accepted** | Date: 2026-05-13

> See the full ADR at `docs/adr/ADR-007-asset-recipe-originality-contract.md`

## Summary

Every asset recipe produced by the asset factory embeds five prohibited similarity rules, three automated similarity check requirements, three new theme variants, and `human_review_required: true`. This is the machine-readable form of the clean-room originality requirement.

## The Five Rules

```
do not reuse original palette
do not copy original silhouette
do not copy character identity
do not use original crop as input
do not copy animation frames
```

## The Three Checks

```
perceptual_hash_comparison: required
silhouette_similarity_comparison: required
palette_similarity_comparison: required
```

## Why In-File?

Rules in the recipe file travel with the artifact. A downstream artist or AI pipeline reading the recipe knows the constraints without consulting external documentation.

## Related

- [[Asset Factory]]
- [[Legal Guardrails]]
- [[ADR-006 Vision Layer Numeric Output]]

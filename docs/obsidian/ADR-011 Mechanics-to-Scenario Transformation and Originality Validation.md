# ADR-011 Mechanics-to-Scenario Transformation and Originality Validation

tags: #adr #validation #game-design #clean-room #t12

Decision: define explicit transformation and validation rules for turning observed abstract mechanics into new scenarios without copying expressive structure.

## Summary

ADR-011 permits reuse of abstract mechanical relationships, timing bands, role categories, and trace vocabularies. It requires transformation into new roles, new scene layouts, changed encounter order, original naming, and divergence notes.

It forbids copying exact level layouts, scene order, platform topology, spawn positions, source enemy catalogs, source names, source visual identity, or any private media/evidence reference.

## Validation Shape

Validation must cover:

- mechanics conformance to selected abstract mechanics
- originality divergence for scenes, names, theme, and encounter recipes

This complements [[ADR-007 Asset Recipe Originality Contract]] and [[ADR-008 Behavioral Validation No Pixels]].

## Related

- [[Public Original Game Definition Layer]]
- [[ADR-010 Public Original Game Definition Layer]]
- [[Behavioral Validation]]
- Full ADR: `docs/adr/ADR-011-mechanics-to-scenario-transformation-originality-validation.md`

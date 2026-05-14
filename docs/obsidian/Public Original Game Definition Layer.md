# Public Original Game Definition Layer

tags: #architecture #game-design #clean-room #t12

The Public Original Game Definition Layer is the clean-room bridge between calibrated abstract mechanics and a real original game prototype.

It exists because T10/T11 can prove a safe mechanics pipeline, but they do not define the new game. This layer defines the product direction, gameplay pillars, encounter grammar, scene recipes, progression model, and theme translation rules that make the React Native prototype an independent game instead of mechanics playback.

## Inputs

- Public abstract mechanics
- Public abstract traces
- Entity archetypes
- Asset recipes that satisfy [[ADR-007 Asset Recipe Originality Contract]]
- Behavioral validation reports that satisfy [[ADR-008 Behavioral Validation No Pixels]]

## Outputs

Future T12 tasks may create:

- `specs/game/signal_garden_design_brief.yaml`
- `specs/encounters/encounter_grammar.yaml`
- `specs/scenes/signal_garden_scene_recipes.yaml`
- `specs/transforms/mechanics_to_scene_rules.yaml`
- `specs/progression/signal_garden_progression.yaml`

These are proposed public artifacts only. They must contain original design intent and abstract rules, not source content.

## Product Direction

Signal Garden is the working original direction for T12. It is a mobile arcade-action prototype about readable signal fields, committed movement, timing pressure, pulse-like interactions, and compact authored scenes.

Signal Garden must not reuse source names, enemy identities, stage names, weapon identities, visual framing, exact level layouts, exact encounter order, or expressive theme.

## Related

- [[ADR-010 Public Original Game Definition Layer]]
- [[ADR-011 Mechanics-to-Scenario Transformation and Originality Validation]]
- [[React Native Prototype]]
- [[Asset Factory]]
- [[Behavioral Validation]]
- `docs/plans/original_game_definition_plan.md`

# ADR-009 — Input Plan Determinism and YAML Definition

## Status
Accepted

## Date
2026-05-13

## Context

MAME observation runs must be reproducible. If the same input sequence is applied to the same ROM at the same starting state, the game should produce the same output frames. This is the basis for being able to correlate observations across multiple runs and for building a stable abstract mechanics spec.

Ad hoc keyboard input during observation would be non-reproducible. The harness needs a declarative input description that can be:
- version-controlled alongside the run metadata
- expanded deterministically into a per-frame action sequence
- validated before any MAME invocation

## Decision

Define a YAML input plan format:

```yaml
plan_name: basic_controls
game_id: gng
steps:
  - action: insert_coin
    frames: 10
    notes: "insert coin to start"
  - action: press_start
    frames: 5
  - action: move_right
    frames: 60
  - action: jump
    frames: 15
```

Each step declares an `action` from a fixed vocabulary (`VALID_ACTIONS`) and a `frames` count (minimum 1). The plan is loaded by `input_planner.load_input_plan` which validates both fields.

`InputPlan.expand_to_frames` produces a flat `list[FrameInput]` where every frame has exactly one `action` and the corresponding `active_buttons` mapping. This expansion is deterministic given the same plan.

The button mapping (`_buttons_for_action`) is a pure dict lookup — no state, no side effects. The same action always produces the same buttons.

The valid action set is fixed at module level:
```python
VALID_ACTIONS = {
    "insert_coin", "press_start", "move_left", "move_right",
    "move_up", "move_down", "jump", "fire", "pause", "noop"
}
```

Any unknown action raises `ValueError` at load time, before any MAME invocation.

## Consequences

**Positive**
- Plans are human-readable and diffable in git.
- `expand_to_frames` length is used in run metadata (`frame_plan_length`) as a cross-check on the planned observation depth.
- Tests can load plans from string fixtures without filesystem access.

**Negative**
- The input plan format is flat — it does not support conditional branching (e.g., "if player died, restart"). Complex exploration strategies would need a scripting layer (e.g., MAME Lua scripting) that is out of scope for this phase.
- The button mapping is fixed for a generic arcade controller model. Games with non-standard button layouts would need profile-specific mappings, which are not currently supported.
- Frame duration is the only time unit. Plans cannot specify wall-clock durations or react to in-game events.

## Related

- [ADR-005](./ADR-005-source-profile-pattern.md)
- `apps/mame-harness/input_planner.py`
- `plans/basic_controls.yaml`
- `docs/exploration_strategy.md`

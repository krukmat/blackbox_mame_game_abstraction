# Input Plan

tags: #mame #determinism #input

`apps/mame-harness/input_planner.py`

## Purpose

Define a reproducible sequence of controller actions for a MAME observation run. Plans are YAML files stored in `plans/`. They are version-controlled and deterministically expanded to per-frame action sequences.

## YAML Format

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
  - action: noop
    frames: 60
```

## Valid Actions

```
insert_coin  press_start  move_left  move_right
move_up      move_down    jump       fire
pause        noop
```

Any other value raises `ValueError` at load time.

## Expansion

`InputPlan.expand_to_frames()` → `list[FrameInput]`

Each `FrameInput`:
- `frame_index`: absolute frame number (0-based)
- `action`: the action string
- `active_buttons`: list of button names (from the fixed mapping)

The expansion is deterministic: same plan → same frame list every time.

## Button Mapping

```python
{
    "insert_coin": ["coin"],
    "press_start": ["start"],
    "move_left":   ["left"],
    "move_right":  ["right"],
    "move_up":     ["up"],
    "move_down":   ["down"],
    "jump":        ["button1"],
    "fire":        ["button2"],
    "pause":       ["pause"],
    "noop":        [],
}
```

## Usage in Run Metadata

`len(plan.expand_to_frames())` is written as `frame_plan_length` in public run metadata — a cross-check that the planned observation depth matches what was requested.

## Limitations

- Flat sequence only. No conditional branching or event-reactive steps.
- Frame duration is the only time unit (no wall-clock or in-game-event waits).
- Button mapping is fixed for a generic arcade layout.

## Related

- [[MAME Runner]]
- [[ADR-009 Input Plan Determinism]]
- `apps/mame-harness/input_planner.py`
- `plans/basic_controls.yaml`

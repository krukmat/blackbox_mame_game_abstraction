# Prompt 03 - Add Compiler from Layered Profiles to Existing Input Plan

```text
Implement the compatibility compiler from layered mapping profiles to the existing input plan format.

Scope:

Add a new module:

- apps/mame-harness/mapping_compiler.py

Inputs:

- device_profile YAML
- controller_profile YAML
- game_action_profile YAML
- input_sequence YAML

Output:

- a generated YAML input plan compatible with the current `input_planner.py` behavior.

Design:

The compiler must preserve the existing execution path:

layered profiles -> generated input plan YAML -> existing input_planner.py -> per-frame JSON -> Lua/MAME.

Do not rewrite `input_planner.py` unless a very small compatibility helper is necessary.

Expected input sequence shape:

```yaml
schema_version: 1
sequence_type: input_sequence
id: gng_smoke_sequence
steps:
  - control: select
    frames: 4
  - control: start
    frames: 4
  - control: dpad_right
    frames: 30
  - control: south
    frames: 6
  - control: east
    frames: 6
```

Compiler behavior:

- Validate all profiles before compiling.
- Resolve input sequence `control` values against the controller profile.
- Map canonical controls to semantic game actions through the game action profile.
- Emit the existing input plan YAML format.
- Unknown controls must fail fast with clear error messages.
- Missing game action mapping should either fail or map to `noop`; choose the safer behavior based on existing repo conventions and document the choice.
- Generated plans must not include absolute paths or private evidence references.

Add tests:

- apps/mame-harness/tests/test_mapping_compiler.py

Test cases:

1. sample keyboard/controller/game profiles compile the smoke sequence;
2. compiled output contains only allowed semantic actions;
3. unknown sequence control fails;
4. missing required mapping fails or becomes noop according to documented behavior;
5. generated YAML can be parsed by the existing input planner.

After implementation, summarize changed files and test results.
```

# Prompt 01 - Create Schemas and Sample Profiles

```text
Implement Phase 1 foundation for layered input mapping.

Scope:

Add JSON Schemas and minimal sample profiles only. Do not modify MAME execution, Lua scripts, vision pipeline, trace extraction, or validation pipeline.

Create these directories if missing:

- profiles/devices/
- profiles/controllers/
- profiles/games/gngb/
- plans/sequences/
- plans/generated/

Create these schemas:

- packages/schemas/device_profile.schema.json
- packages/schemas/controller_profile.schema.json
- packages/schemas/game_action_profile.schema.json
- packages/schemas/input_sequence.schema.json

Create these sample YAML files:

- profiles/devices/keyboard_default.yaml
- profiles/controllers/arcade_2button.yaml
- profiles/games/gngb/default_actions.yaml
- plans/sequences/gng_smoke_sequence.yaml

Design constraints:

- Keep schemas minimal.
- Use `schema_version: 1`.
- Use `profile_type` to distinguish profile kinds.
- Do not store absolute paths.
- Do not store ROM names beyond the already-public source profile/driver abstraction.
- Do not store screenshots, audio, sprites, frame dumps, or private evidence references.
- Ensure the sample `gngb` action profile maps canonical controls to existing semantic actions supported by the current input planner, such as `insert_coin`, `press_start`, `move_left`, `move_right`, `move_up`, `move_down`, `jump`, `fire`, and `noop`.

Expected output:

- Files created.
- No behavioral changes.
- Existing tests should remain unaffected.
- Add or update a minimal test only if there is already a schema validation pattern in the repo.

After implementation, summarize:

- files created;
- assumptions made;
- commands to run tests.
```

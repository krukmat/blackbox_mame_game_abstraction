# Prompt 07 - SDL GameControllerDB Importer

```text
Implement the first external mapping importer: SDL GameControllerDB mapping line -> device_profile YAML.

Prerequisite:

Only run this after the internal `device_profile` schema and loader are stable.

Scope:

Add:

- apps/mame-harness/sdl_mapping_importer.py

CLI command:

```bash
blackbox map import-sdl \
  --mapping-line '<SDL_MAPPING_LINE>' \
  --out profiles/devices/imported_sdl_controller.yaml
```

Behavior:

- Parse a single SDL GameController mapping string.
- Extract GUID and device name.
- Map common SDL logical controls to the repository canonical controls:
  - a -> south
  - b -> east
  - x -> west
  - y -> north
  - start -> start
  - back -> select
  - dpup -> dpad_up
  - dpdown -> dpad_down
  - dpleft -> dpad_left
  - dpright -> dpad_right
  - leftshoulder -> l1
  - rightshoulder -> r1
- Ignore unsupported fields safely.
- Generate a valid `device_profile` YAML.
- Validate generated profile before writing.

Constraints:

- Do not fetch remote files from the internet in the implementation.
- Do not vendor the entire SDL database.
- Do not add heavy dependencies.
- Do not implement RetroArch importer in this task.

Tests:

- valid SDL mapping line generates valid profile;
- unsupported fields are ignored;
- malformed line fails clearly;
- generated profile passes existing profile validation.
```

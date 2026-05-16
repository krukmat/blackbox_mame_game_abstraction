# Prompt 09 - CLI Wizard `map init`

```text
Implement a minimal non-GUI mapping wizard.

Prerequisite:

Only run this after `map validate`, `map compile`, and the profile schemas are stable.

Scope:

Add:

```bash
blackbox map init
```

Goal:

Create a guided first-use flow that produces valid profile YAML without requiring the user to hand-author YAML.

Minimal behavior:

1. Ask device type:
   - keyboard;
   - controller;
   - arcade stick;
   - manual.

2. Offer existing presets:
   - keyboard_default;
   - arcade_2button.

3. Ask the user to bind canonical controls:
   - dpad_left;
   - dpad_right;
   - dpad_up;
   - dpad_down;
   - south;
   - east;
   - start;
   - select.

4. Detect duplicate bindings.
5. Allow optional controls to be skipped.
6. Save a valid `device_profile` YAML.
7. Print next command to validate and compile.

Constraints:

- Do not attempt full real-time OS-level input capture in the first version unless it is already trivial in the repo.
- A prompt-based wizard is acceptable for v1.
- Do not store absolute paths.
- Do not store private evidence references.
- Do not run MAME.
- Do not read ROMs.

Tests:

- simulate wizard input;
- generated profile validates;
- duplicate bindings are rejected or warned according to documented behavior;
- skipped optional controls behave correctly.
```

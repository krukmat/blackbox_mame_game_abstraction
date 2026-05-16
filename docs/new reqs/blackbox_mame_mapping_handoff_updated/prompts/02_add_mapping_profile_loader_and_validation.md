# Prompt 02 - Add Mapping Profile Loader and Validation

```text
Implement a profile loader and validator for the new layered input mapping profiles.

Scope:

Add a new module under the MAME harness, preferably:

- apps/mame-harness/mapping_profiles.py

The module should:

- load YAML profile files;
- identify profile type;
- validate required fields for:
  - device_profile;
  - controller_profile;
  - game_action_profile;
  - input_sequence;
- fail with clear actionable errors;
- reject absolute paths and obvious private evidence references in public profile files;
- avoid introducing a heavy dependency unless the repository already uses it.

Important:

- Reuse existing guardrail/redaction conventions where appropriate.
- Do not change input_planner behavior yet.
- Do not add SDL or RetroArch importers yet.
- Do not implement a wizard yet.

Add tests:

- apps/mame-harness/tests/test_mapping_profiles.py

Test cases:

1. valid sample profiles load successfully;
2. invalid `profile_type` fails;
3. missing required fields fail;
4. absolute local paths are rejected;
5. private evidence paths are rejected;
6. duplicate canonical controls or invalid controls are rejected where applicable.

After implementation, run the relevant test subset and summarize results.
```

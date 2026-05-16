# Prompt 12 - Compact Handoff Prompt for a Fresh Agent

Use this when opening a new Codex/Claude Code session.

```text
You are continuing work on `blackbox_mame_game_abstraction`.

Objective:

Reduce friction in the first mapping phase by introducing a layered input mapping model while preserving the existing MAME harness.

Architecture decision:

Add a compatibility layer:

physical device profile -> canonical controller profile -> game action profile -> compiled input plan -> existing input_planner.py -> frame JSON -> Lua -> MAME

Non-negotiable constraints:

- Do not rewrite the MAME execution path.
- Do not change clean-room boundaries.
- Public files must not contain ROMs, screenshots, audio, sprites, frame dumps, private evidence paths, or absolute local machine paths.
- Keep the first PR small.
- Implement schemas, sample profiles, loader/validator, compiler, CLI commands and tests before importers or wizard.

First PR target:

1. Add schemas:
   - packages/schemas/device_profile.schema.json
   - packages/schemas/controller_profile.schema.json
   - packages/schemas/game_action_profile.schema.json
   - packages/schemas/input_sequence.schema.json

2. Add sample files:
   - profiles/devices/keyboard_default.yaml
   - profiles/controllers/arcade_2button.yaml
   - profiles/games/gngb/default_actions.yaml
   - plans/sequences/gng_smoke_sequence.yaml

3. Add modules:
   - apps/mame-harness/mapping_profiles.py
   - apps/mame-harness/mapping_compiler.py

4. Extend CLI:
   - blackbox map validate --profile <path>
   - blackbox map compile --device <path> --controller <path> --game <path> --sequence <path> --out <path>

5. Add tests:
   - test_mapping_profiles.py
   - test_mapping_compiler.py
   - test_mapping_cli.py

6. Add docs:
   - docs/mapping.md
   - README pointer only

Definition of done:

- Existing tests pass.
- New tests pass.
- Generated plan can be parsed by current input_planner.py.
- No public artifact leaks local paths or private evidence.
- The docs explain the layered mapping model clearly.
```

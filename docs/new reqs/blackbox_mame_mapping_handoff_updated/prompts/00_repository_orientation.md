# Prompt 00 - Repository Orientation

Use this prompt first in Codex or Claude Code.

```text
You are working on the repository `blackbox_mame_game_abstraction`.

Goal: understand the existing architecture before making changes.

Read the following files first:

- README.md
- AGENTS.md
- CLAUDE.md
- apps/mame-harness/input_planner.py
- apps/mame-harness/cli.py
- apps/mame-harness/source_profiles.py
- apps/mame-harness/preflight.py
- apps/mame-harness/mame_runner.py
- apps/mame-harness/guardrails.py
- apps/mame-harness/metadata_writer.py
- scripts/mame_autoboot.lua
- packages/schemas/*
- apps/mame-harness/tests/test_input_planner.py
- apps/mame-harness/tests/test_cli.py
- apps/mame-harness/tests/test_public_artifact_guardrails.py

Context:

The repository uses MAME as a private black-box observation boundary. Public artifacts must never include ROMs, screenshots, audio, sprites, absolute local paths, or private evidence paths. The project extracts public behavioral abstractions only.

The current pain point is the first mapping phase. Today the flow jumps too quickly from physical input to game semantic actions. We need a layered mapping model:

1. device_profile: physical hardware or keyboard mapping.
2. controller_profile: canonical internal controls.
3. game_action_profile: game-specific semantic actions.
4. compiled input plan: compatible with the existing input planner and Lua/MAME flow.

Do not implement yet. First produce a concise technical summary of:

- current input plan format;
- CLI structure;
- existing schema conventions;
- existing guardrail conventions;
- safest integration points for adding `map validate` and `map compile`;
- any risks you see.

Keep the summary short and actionable.
```

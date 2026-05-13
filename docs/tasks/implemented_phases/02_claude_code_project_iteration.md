# Prompt — Claude Code Project Iteration

We are building `blackbox_mame_game_abstraction`, a clean-room framework to infer abstract game mechanics from observable MAME behavior and reimplement a new original mobile game in React Native.

## Read first

```text
README.md
AGENTS.md
CLAUDE.md
docs/legal_guardrails.md
docs/architecture.md
docs/exploration_strategy.md
docs/clean_room_process.md
```

## Non-negotiable constraints

- Never add ROMs, screenshots, videos, original sprites, original audio, emulator save states, or copyrighted assets to git.
- Never implement sprite ripping as an output.
- Never implement image-to-image transformation of original sprite crops.
- The framework can analyze captured frames locally, but generated public outputs must be abstract mechanics, entity archetypes, asset recipes, and validation metadata.
- Asset generation must use abstract recipes only.
- Any private evidence must remain under `evidence/private/` and be gitignored.

## Task

Review the repository and implement the next smallest valuable increment.

## Priority order

1. Ensure guardrails are encoded in docs, `.gitignore`, tests, and validation checks.
2. Improve the MAME harness dry-run and real-run separation.
3. Add the first vision placeholder pipeline:
   - frame manifest loader;
   - frame differencing placeholder;
   - entity candidate schema;
   - redacted metadata output.
4. Add asset recipe generation from entity candidates:
   - output abstract descriptions only;
   - include prohibited similarity constraints;
   - include originality guard placeholders.
5. Add tests for every guardrail.

## Development rules

- Work incrementally.
- Prefer small cohesive modules.
- Add tests before or alongside implementation.
- Keep public output asset-safe.
- Use typed Python.
- Do not introduce heavy ML dependencies yet.
- When uncertain, add an interface and a documented placeholder rather than guessing.

## Before coding

1. Summarize the current architecture.
2. Identify missing guardrails.
3. Propose a short implementation plan.
4. Then implement.

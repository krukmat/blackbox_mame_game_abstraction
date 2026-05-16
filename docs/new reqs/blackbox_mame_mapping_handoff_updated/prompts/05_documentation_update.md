# Prompt 05 - Documentation Update

```text
Update project documentation for the new mapping model.

Scope:

Create or update:

- docs/mapping.md
- README.md, only with a short pointer to docs/mapping.md
- AGENTS.md or CLAUDE.md only if they contain agent execution guidance that must mention the new flow

Content required in docs/mapping.md:

1. Explain the problem:
   - physical device mapping;
   - canonical controller mapping;
   - semantic game action mapping;
   - compiled input plan.

2. Include this diagram:

```text
physical device profile
        ↓
canonical controller profile
        ↓
game action profile
        ↓
compiled input plan
        ↓
existing frame-level JSON / Lua / MAME execution
```

3. Explain the clean-room boundary:
   - public profiles may contain abstract mappings;
   - public profiles must not contain ROMs, screenshots, audio, sprites, frame dumps, absolute local paths, or private evidence paths.

4. Include a minimal quickstart:

```bash
blackbox map validate --profile profiles/devices/keyboard_default.yaml

blackbox map compile \
  --device profiles/devices/keyboard_default.yaml \
  --controller profiles/controllers/arcade_2button.yaml \
  --game profiles/games/gngb/default_actions.yaml \
  --sequence plans/sequences/gng_smoke_sequence.yaml \
  --out plans/generated/gng_smoke_compiled.yaml
```

5. Explain that SDL/RetroArch importers and `map init` wizard are future work, not part of the first implementation.

Keep the documentation concise and contributor-oriented.
```

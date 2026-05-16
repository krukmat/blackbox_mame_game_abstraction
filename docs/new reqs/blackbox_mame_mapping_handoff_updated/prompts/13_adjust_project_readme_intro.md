# Prompt 13 - Improve the Project README Introduction and Positioning

Use this prompt as a separate documentation task after you have understood the repository. It can be executed independently from the mapping refactor, but it should preserve the architectural decisions introduced in ADR-0001.

```text
You are working on the repository `blackbox_mame_game_abstraction`.

Task:
Improve the project README so a first-time reader can understand the concept quickly, without needing deep knowledge of MAME, emulation, reverse engineering, computer vision, or clean-room development.

Primary goal:
Make the README introduction more approachable, clear, and compelling at a general technical level while preserving the project's clean-room positioning.

Read first:

- README.md
- AGENTS.md
- CLAUDE.md
- docs/adr/ if present
- docs/plans/ if present
- apps/mame-harness/guardrails.py
- apps/mame-harness/input_planner.py
- packages/vision/ if present
- packages/validation/ if present
- packages/asset-factory/ if present

Current README context to preserve:

- The project studies a game's feel and extracts abstract mechanics.
- MAME is used as a local observation boundary.
- ROMs, screenshots, videos, frame dumps, sprites, audio, crops, and other expressive artifacts stay private.
- Public outputs should contain only abstract mechanics, numeric summaries, behavioral traces, asset recipes, validation data, and original game-definition artifacts.
- Current case study: Ghosts 'n Goblins through the `gngb` MAME driver.
- The project is not trying to clone a game, dump assets, redistribute ROMs, or produce a derivative copy.
- The intended downstream use is an independent implementation with original art, a new theme, and a new identity.

Specific problem to fix:
The current README is technically useful, but the opening is still too compressed. A new reader may not immediately understand what the project contributes compared with MAME, RetroArch, BizHawk, Gym Retro, AntiMicroX, or a normal emulator frontend.

Add a clearer introduction that explains:

1. What the project is.
2. What problem it solves.
3. Why black-box observation is useful.
4. Why clean-room boundaries matter.
5. What comes out of the pipeline.
6. What the project is not.
7. Why the first mapping phase is being redesigned around layered input mapping.

Recommended opening structure:

```markdown
# blackbox_mame_game_abstraction

> Observe gameplay behavior. Extract abstract mechanics. Build something new.

## What this is

A short, human explanation in 2-4 paragraphs.

## Why this exists

Explain the gap: emulators can run games, RL environments can train agents, controller tools can map inputs, but this project tries to convert observed gameplay behavior into clean-room, implementation-ready abstractions.

## What this is not

A concise bullet list:

- not a ROM distribution project;
- not an asset extraction tool;
- not a cloning pipeline;
- not a generic emulator frontend;
- not an RL training environment.

## The core idea

Simple 5-step flow:

observe -> capture -> abstract -> validate -> reimplement independently

## Clean-room boundary

Explain private evidence vs public artifacts in plain language.

## Current case study

Mention GNG/gngb as the first subject, but avoid making the project sound hardcoded to that game.
```

Tone requirements:

- Clear, direct, and developer-friendly.
- More approachable than academic.
- Avoid legalistic overclaiming. Do not say the project guarantees legal safety.
- Avoid words like "clone", "copy", or "replicate" except in the explicit "what this is not" section.
- Use "independent implementation", "abstract mechanics", "observable behavior", "clean-room boundary", and "original game identity" consistently.
- Explain terms before using them heavily.
- Keep the introduction readable for a technical person who knows GitHub and games but not MAME internals.

Content constraints:

- Do not change factual project status unless verified from repository files.
- Do not invent completed features.
- Do not remove guardrail warnings.
- Do not remove the current diagrams unless replacing them with clearer equivalents.
- Do not remove Quick Start.
- Do not remove repository layout.
- Do not remove contribution guidance.
- Keep Mermaid diagrams valid.
- Keep all links relative and working.
- Keep examples clean-room safe: no screenshots, no ROM paths, no expressive assets.

Recommended addition: comparison paragraph

Add a short section or paragraph explaining the difference from adjacent tools:

```markdown
## How it differs from adjacent tools

MAME and RetroArch help run games. BizHawk and TAS tooling help automate and inspect emulated execution. Gym-style projects help train agents. Controller tools help map physical inputs.

This project uses some of those ideas, but targets a different output: a clean-room abstraction layer that turns observed gameplay behavior into public, implementation-ready mechanics data and validation specs.
```

Recommended addition: first-mapping-phase note

Add a short note that the input mapping model is being moved toward layers:

```markdown
physical device -> canonical controller -> game action -> observable effect -> abstract rule
```

Explain this in one paragraph, not as a deep implementation section.

Expected output:

1. Update README.md only, unless a tiny supporting docs link is clearly necessary.
2. Preserve all existing technical sections, but reorganize if it improves clarity.
3. Add a stronger general introduction before the detailed diagrams.
4. Keep the README concise enough that the first 60-90 seconds of reading explain the project.
5. At the end, summarize:
   - what sections changed;
   - what content was preserved;
   - any assumptions made;
   - whether any links or commands need follow-up validation.

Validation before finishing:

- Check Markdown renders cleanly.
- Check Mermaid blocks are syntactically plausible.
- Check no private paths or expressive game artifacts were introduced.
- Check the README does not sound like a game cloning pipeline.
- Check the first section answers: "What does this project add that MAME/RetroArch/Gym Retro do not?"
```

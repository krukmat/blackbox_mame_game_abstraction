# Handoff — Arthur Tracker

**Repo:** `/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction`
**Venv:** `apps/mame-harness/.venv/bin/python` — never system python
**Suite:** 243 passed

---

## Do these steps in order. Do not skip ahead.

### Step 1 — Record gameplay (agent runs, user plays)

Run this. It blocks until the user closes MAME:

```bash
cd /Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction
./scripts/launch_manual_capture_autoboot.sh
```

What happens:
- MAME launches and boots automatically (~25 seconds: coin insert + start + intro)
- At frame ~1505, Arthur is controllable — **user plays from here**
- When user closes MAME, the script returns

Tell the user: *"MAME is launching. The boot runs automatically (~25s). Controls once Arthur appears: ← → move, Left Alt jump, Left Ctrl fire. Close the window when you finish the level."*

### Step 2 — Extract frames and regenerate trace

Run this immediately after step 1 returns:

```bash
./scripts/extract_frames.sh
```

This extracts PNG frames from the AVI and regenerates `specs/traces/gng_trace.json`.

### Step 3 — Present Arthur Tracker task list for approval, then implement (TDD)

Read these files first:
- `docs/tasks/gng_source_integration/T10.5-arthur-tracker.md`
- `docs/adr/ADR-012-entity-signature-player-identification.md`
- `packages/vision/frame_differ.py`
- `packages/vision/trace_extractor.py`

Show the task list to the user. **Wait for explicit approval before writing any code.**
TDD: tests first, then implementation. Do not commit with broken tests.

### Step 4 — Continue artifact validation

Only after Arthur Tracker is implemented and trace is regenerated from the manual run:
- `docs/tasks/gng_source_integration/T10.4-public-artifact-generation.md`

---

## For Codex

Codex does not have terminal access by default. Before running any shell command, add it as a setup step in the Codex task configuration:

```
Setup commands (run before agent starts):
  cd /Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction
  source apps/mame-harness/.venv/bin/activate
```

Steps 1 and 2 (recording + frame extraction) require a display and user interaction — **skip them in Codex**. Assume `evidence/private/run_manual_01/frames/extracted_png/` already contains extracted PNG frames and `specs/traces/gng_trace.json` exists.

Codex entry prompt:
> Read `docs/handoff_arthur_tracker.md`. Skip steps 1 and 2 — recording is already done. Start at Step 3: read the four listed files, present the task list in Spanish, wait for approval, then implement with TDD using the activated venv.

---

## Hard rules

- Never ask for ROM path or MAME binary — they are in `CLAUDE.md § Manual Gameplay Recording`
- Never commit with broken tests
- Always show task list and wait for explicit user approval before implementing
- Always use `apps/mame-harness/.venv/bin/python` — never system python
- All user communication in Spanish — all technical docs in English

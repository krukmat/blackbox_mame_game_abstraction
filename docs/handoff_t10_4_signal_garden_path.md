# Handoff — T10.4 → Signal Garden Path

**Repo:** `/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction`
**Venv:** `apps/mame-harness/.venv/bin/python` — never system python
**Python suite:** 361 passed
**RN suite:** 3 passed

---

## What This Session Did

This session analyzed the full project state and produced all missing planning and task documentation for the path from GNG observation to Signal Garden (the new original game). Nothing was implemented — documentation only.

### Files created or updated

| File | What changed |
|------|-------------|
| `docs/obsidian/GNG Integration Plan.md` | T10.6 subtasks → ✅ Done; T11 subtasks + T12 tasks added to index |
| `docs/tasks/gng_source_integration/T10.4-public-artifact-generation.md` | Full rewrite: fresh capture required, quality gate thresholds, M effort |
| `docs/tasks/gng_source_integration/T11-rn-prototype-hookup.md` | Full rewrite: 5 subtasks (T11.1–T11.5), L effort aggregate |
| `docs/tasks/original_game_definition/T12.0-adrs-and-phase-plan.md` | Created |
| `docs/tasks/original_game_definition/T12.1-public-mechanics-capability-review.md` | Created |
| `docs/tasks/original_game_definition/T12.2-product-direction-and-gameplay-pillars.md` | Created |
| `docs/tasks/original_game_definition/T12.3-encounter-grammar-schema.md` | Created |
| `docs/tasks/original_game_definition/T12.4-scene-recipe-and-transformation-rules.md` | Created |
| `docs/tasks/original_game_definition/T12.5-progression-and-difficulty-model.md` | Created |
| `docs/tasks/original_game_definition/T12.6-theme-translation-and-asset-recipe-enrichment.md` | Created |
| `docs/tasks/original_game_definition/T12.7-rn-original-vertical-slice-hookup.md` | Created |
| `docs/tasks/original_game_definition/T12.8-originality-and-design-intent-validation-gate.md` | Created |
| `docs/tasks/original_game_definition/README.md` | Updated with links to all task files |
| `docs/plans/gng_source_integration_plan.md` | Dependency order + T11 subtasks + task index updated |
| `docs/plans/original_game_definition_plan.md` | Task file links, artifact table, task index added |

---

## Current State

### What is done (code + tests green)

- T01–T10.6: full GNG observation pipeline — 361 Python tests pass
- GNG-MAP-01–05: layered input mapping adoption — complete
- RN prototype scaffold: 3 TypeScript tests pass — but uses hardcoded sample data

### What is NOT done

- `specs/traces/gng_trace.json` is from before T10.6 (old pipeline, 477k hazard entries)
- RN prototype has no connection to real public artifacts
- T12 (Signal Garden) has not started

---

## The Execution Chain

```
T10.4 (fresh MAME capture + quality gate)
  → T11.1 (YAML loader in TypeScript)
  → T11.2 (episode extractor — Python)
  → T11.3 (physics calibration from trace)
  → T11.4 (episode-driven scene in RN)
  → T11.5 (clean-room verification)
  → T12.0 (ADRs + signal_garden_phase_plan.md)
  → T12.1 (mechanics affordance map)
  → T12.2 (Signal Garden design brief)
  → T12.3 (encounter grammar schema)
  → T12.4 (scene recipes + transformation rules)
  → T12.5 (progression model)
  → T12.6 (asset recipe enrichment)
  → T12.7 (RN vertical slice)
  → T12.8 (originality validation gate)
```

---

## Task to Implement Now: T10.4

Read this first:

- `docs/tasks/gng_source_integration/T10.4-public-artifact-generation.md` — full spec
- `docs/plans/gng_source_integration_plan.md` — phase context
- `CLAUDE.md` and `AGENTS.md` — project rules
- `docs/bootstrap.md` — local machine setup

### Step 1 — User plays MAME (required before any code)

The user must perform a fresh gameplay session. The existing evidence (`manual_01`, `manual_02`) was captured before T10.6 and is insufficient for T11.3 physics calibration.

```bash
./scripts/launch_manual_capture_autoboot.sh t10_4_01
```

MAME boots automatically (~25 seconds). Once Arthur appears, the user plays. Minimum gameplay required:

| Action | Minimum count | Purpose |
|--------|--------------|---------|
| Jumps | ≥ 20 | Jump arc calibration (T11.3) |
| Fires | ≥ 30 | Projectile velocity calibration (T11.3) |
| Walk left + right | continuous | moveSpeed calibration (T11.3) |
| Total frames | ≥ 3000 | Quality gate coverage |

Controls: `←` `→` move, `Option` jump, `Control` fire, `Esc` quit.

### Step 2 — Extract frames and regenerate trace

```bash
./scripts/extract_frames.sh t10_4_01
```

This regenerates `specs/traces/gng_trace.json` using the T10.6 OpenCV + MOG2 + gap-tolerance pipeline.

### Step 3 — Verify quality gate

Run this check after extraction:

```python
# apps/mame-harness/.venv/bin/python
import json
from pathlib import Path

with open("specs/traces/gng_trace.json") as f:
    data = json.load(f)
trace = data["trace"]

from collections import Counter
types = Counter(e["entity_type"] for e in trace)
events = Counter()
for e in trace:
    for ev in (e.get("events") or []):
        events[ev] += 1

all_frames = sorted(set(e["frame"] for e in trace))
gameplay_frames = [f for f in all_frames if f >= 1505]
player_frames = set(e["frame"] for e in trace if e["entity_type"] == "player")
gameplay_player_frames = player_frames & set(gameplay_frames)

print("Player detection rate:", len(gameplay_player_frames) / max(len(gameplay_frames), 1))
print("Player spawn count:", sum(1 for e in trace if e["entity_type"] == "player" and "spawn" in (e.get("events") or [])))
print("Hazard entries:", types.get("hazard", 0))
print("Jump events:", events.get("jump_start", 0))
print("Fire events:", events.get("fire", 0))
```

#### Minimum thresholds

| Metric | Minimum |
|--------|---------|
| Player detection rate | > 40% of gameplay frames |
| Player spawn count | ≤ 10 |
| Hazard entries | < 5,000 |
| Jump events | ≥ 20 |
| Fire events | ≥ 30 |

If thresholds are not met, repeat Step 1 with a new run ID (`t10_4_02`, etc.) and re-run Step 2.

### Step 4 — Guardrails and schema verification

```bash
apps/mame-harness/.venv/bin/python -c "
from pathlib import Path
import sys
sys.path.insert(0, 'apps/mame-harness')
sys.path.insert(0, 'packages/vision')
from guardrails import ensure_public_output_path, ensure_no_private_paths
import json

path = Path('specs/traces/gng_trace.json')
ensure_public_output_path(path)
with open(path) as f:
    payload = f.read()
ensure_no_private_paths(payload)
print('Guardrails: PASS')
"
```

```bash
# Schema validation
apps/mame-harness/.venv/bin/python -c "
import json, jsonschema
with open('specs/traces/gng_trace.json') as f:
    trace = json.load(f)
with open('packages/schemas/trace.schema.json') as f:
    schema = json.load(f)
for entry in trace['trace']:
    jsonschema.validate(entry, schema)
print('Schema: PASS — all entries valid')
"
```

### Step 5 — Full test suite

```bash
apps/mame-harness/.venv/bin/pytest apps/mame-harness/tests/ packages/vision/tests/ -q
```

All tests must pass. 361 is the current baseline.

### Step 6 — Update task file

Populate `## Artifact Evidence` in `docs/tasks/gng_source_integration/T10.4-public-artifact-generation.md` with:
- Capture run ID
- Quality metric results
- SHA-256 of the new trace file
- Mark status as ✅ Done

---

## After T10.4: Next Task Is T11.1

Once T10.4 is marked Done, proceed to T11.

Read: `docs/tasks/gng_source_integration/T11-rn-prototype-hookup.md`

T11.1 (first subtask) adds a YAML parser to `apps/rn-prototype` and wires `TimeStep` with the real `ms_per_frame` from `gng_abstract_mechanics.yaml`. It does not require code changes to the Python pipeline.

---

## Known Risks and Open Questions

| Risk | Where it matters |
|------|-----------------|
| Player detection rate may stay below 40% due to MOG2 ceiling (ADR-013 Known Gap) | T10.4 quality gate — may need multiple capture attempts |
| `velocity_x` values in trace are normalized ratios (÷ frame_width) — not pixel units | T11.3 calibration must account for this |
| `gng_abstract_mechanics.yaml` has `calibration: pending` on velocity fields | T11.3 must resolve these before T11.4 can wire PhysicsSystem |
| Episode extraction boundary logic must handle sparse player frames | T11.2 design decision |
| `signal_garden_phase_plan.md` does not yet exist | T12.0 creates it |

---

## Reference Documents

- `docs/tasks/gng_source_integration/T10.4-public-artifact-generation.md`
- `docs/tasks/gng_source_integration/T11-rn-prototype-hookup.md`
- `docs/tasks/original_game_definition/README.md`
- `docs/plans/gng_source_integration_plan.md`
- `docs/plans/original_game_definition_plan.md`
- `docs/adr/ADR-013-opencv-vision-backend.md`
- `docs/adr/ADR-010-public-original-game-definition-layer.md`
- `docs/bootstrap.md`
- `docs/mapping.md`
- `CLAUDE.md`
- `AGENTS.md`
- `README.md`

# Handoff — T10.6 Tuning: min_contour_area + Gap Tolerance

**Repo:** `/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction`
**Venv:** `apps/mame-harness/.venv/bin/python` — never system python
**Suite:** 299 passed (run before and after any change)

---

## Context

T10.6-A through T10.6-D are complete. The OpenCV + MOG2 pipeline is wired and running.
A parameter sweep was run against `manual_02` (3162 frames). Current results:

| Metric | Current | Target |
|--------|---------|--------|
| Player detection (gameplay frames 1505+) | 46% | >60% |
| Player spawns | 135 | 1 |
| Hazard entries | 72,116 | <5,000 |

**Sweep finding:** `min_contour_area=32` eliminates hazard noise entirely (72k → 0).
Player detection plateaus at 46% regardless of MOG2 params — MOG2 absorbs Arthur into
background when he moves slowly. Gap tolerance (T10.6-E) is expected to bridge
short detection gaps and raise effective detection rate.

---

## What to implement

### Step 1 — Update GNGVisionConfig default

File: `packages/vision/gng_vision_config.py`

Change `min_contour_area` default from `4` to `32`.

```python
min_contour_area: int = 32
```

Run full suite after: `apps/mame-harness/.venv/bin/pytest apps/mame-harness/tests packages/vision/tests -q`
**Expected:** some existing tests that assert `min_contour_area == 4` will need updating.
Find them with: `grep -r "min_contour_area" packages/ apps/mame-harness/tests/`

---

### Step 2 — Implement T10.6-E: player gap tolerance in extract_trace

File: `packages/vision/trace_extractor.py`

In `extract_trace`, add a `player_gap_counter: int = 0` that suppresses
false die/spawn events when the player is absent for ≤ `config.player_gap_tolerance` frames.

Logic:
- Read `player_gap_tolerance` from a `GNGVisionConfig` instance passed into `extract_trace`
  (add optional param `config: GNGVisionConfig | None = None`, default `None` → tolerance=0 = current behavior)
- When `find_arthur` returns `None`:
  - Increment `player_gap_counter`
  - If `player_gap_counter <= player_gap_tolerance`: do NOT emit `die`, carry forward last known `prev_region`
  - If `player_gap_counter > player_gap_tolerance`: emit `die` on last real entry, remove from `prev_seen_by_id`
- When `find_arthur` returns a match: reset `player_gap_counter = 0`
- Gap tolerance applies ONLY to `entity_id == "player"` — enemies keep immediate die behavior

**Important:** `extract_trace` currently receives `diff_stats: list[FrameDiffStat]` and `input_plan`.
The gap counter logic goes in the loop that iterates over `curr_stat` in `diff_stats`.

The relevant section to modify starts around line 260 in `trace_extractor.py`:
```python
for eid, last_frame in list(prev_seen_by_id.items()):
    if last_frame == curr_stat.start_frame - 1 and eid not in current_frame_ids:
        ...
```

---

### Step 3 — Update vision_pipeline.py to pass config to extract_trace

File: `apps/mame-harness/vision_pipeline.py`

In `extract_run_trace`, pass `_GNG_CONFIG` to `extract_trace`:
```python
entries = extract_trace(diff_stats, input_plan, config=_GNG_CONFIG)
```

---

### Step 4 — Measure results

Run this inline (no script file needed):

```bash
apps/mame-harness/.venv/bin/python - << 'EOF'
import sys, json
from pathlib import Path

ROOT = Path(".")
for p in ["apps/mame-harness", "packages/vision", "packages/validation"]:
    sys.path.insert(0, str(ROOT / p))

from vision_pipeline import extract_run_trace

output = ROOT / "specs/traces/gng_trace_tuned.json"
extract_run_trace("manual_02", ROOT / "plans/gng_boot_only.yaml", output)

data = json.loads(output.read_text())
trace = data["trace"]
total_gameplay = 1657

player_frames = len({e["frame"] for e in trace if e["entity_type"] == "player" and e["frame"] >= 1505})
player_spawns = sum(1 for e in trace if e["entity_type"] == "player" and "spawn" in e["events"])
hazard_count  = sum(1 for e in trace if e["entity_type"] == "hazard")

print(f"Player detection : {player_frames}/{total_gameplay} ({player_frames/total_gameplay*100:.1f}%)")
print(f"Player spawns    : {player_spawns}")
print(f"Hazard entries   : {hazard_count}")
EOF
```

---

## Acceptance criteria

| Metric | Minimum | Notes |
|--------|---------|-------|
| Player detection | >55% | MOG2 ceiling ~46%; gap tolerance expected to add 10–15pp |
| Player spawns | <10 | gap tolerance closes most short gaps |
| Hazard entries | 0 | already achieved with min_contour_area=32 |
| Full test suite | 299+ green | no regressions |

If player detection stays below 55% after gap tolerance, document the ceiling
and move forward — T10.6-F will capture the actual numbers as quality metrics.

---

## Hard rules

- Never use bare `python` or `pytest` — always venv prefix
- Run full suite before reporting done: `apps/mame-harness/.venv/bin/pytest apps/mame-harness/tests packages/vision/tests -q`
- All user communication in Spanish — technical docs in English
- Do not commit

## Reference documents

- `docs/tasks/gng_source_integration/T10.6-opencv-vision-backend.md` — subtask T10.6-E spec
- `docs/adr/ADR-013-opencv-vision-backend.md` — architectural decision
- `packages/vision/trace_extractor.py` — file to modify for gap tolerance
- `packages/vision/gng_vision_config.py` — file to modify for min_contour_area
- `apps/mame-harness/vision_pipeline.py` — file to update extract_run_trace call
- `CLAUDE.md` and `AGENTS.md` — project rules

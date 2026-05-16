# Handoff — T10.6 OpenCV Vision Backend

**Repo:** `/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction`
**Venv:** `apps/mame-harness/.venv/bin/python` — never system python
**Suite:** 282 passed

---

## Context

T10.5 (ArthurTracker, multi-entity pipeline) is complete. The current trace has three structural problems:

| Problem | Metric | Fix |
|---------|--------|-----|
| Arthur still → no diff signal | 24% player detection (769/3162 frames) | MOG2 background subtraction |
| GNG HUD → hazard noise | 144k hazard entries (87% of trace) | ROI mask: bottom 20px excluded |
| Quiet-frame gaps → spawn/die cascade | 111 player spawns instead of 1 | Gap tolerance (3 frames) |

## Task to implement: T10.6

Read these files before writing a single line of code:

- `docs/adr/ADR-013-opencv-vision-backend.md` — the architectural decision
- `docs/tasks/gng_source_integration/T10.6-opencv-vision-backend.md` — all subtasks
- `packages/vision/frame_differ.py` — current implementation to refactor
- `packages/vision/trace_extractor.py` — gap tolerance goes here
- `CLAUDE.md` and `AGENTS.md` — project rules

## Subtask order (do not skip ahead)

```
T10.6-A → T10.6-B → T10.6-C → T10.6-D → T10.6-E → T10.6-F
```

**T10.6-A** — Define `FrameDifferBackend` Protocol, extract `PurePythonBackend`, add `GNGVisionConfig` skeleton, install `opencv-python-headless`.

**T10.6-B** — HUD ROI mask in both backends (rows ≥ `hud_y_top=204` zeroed).

**T10.6-C** — `OpenCVBackend` using `cv2.connectedComponentsWithStats` replacing Python flood fill.

**T10.6-D** — MOG2 background subtraction in `OpenCVBackend.diff_manifest` (warm-up 50 frames, then foreground mask).

**T10.6-E** — `player_gap_tolerance=3` in `extract_trace`: suppress die/spawn for short gaps.

**T10.6-F** — Regenerate `specs/traces/gng_trace.json`, verify player detection >60%, player spawns=1, hazard <5k.

## Hard rules

- TDD: write tests before each subtask implementation
- Never commit with broken tests — run full suite before every commit:
  `apps/mame-harness/.venv/bin/pytest apps/mame-harness/tests packages/vision/tests -q`
- Present each subtask summary and wait for approval before moving to the next
- All user communication in Spanish — all technical docs in English
- Never use bare `python` or `pytest` — always use the venv prefix
- `PurePythonBackend` must keep all 282 existing tests green — no behavior change
- `OpenCVBackend` is used only by `vision_pipeline.py` in production runs

## Quality targets (T10.6-F)

| Metric | Current | Target |
|--------|---------|--------|
| Player detection rate | ~24% | >60% |
| Player spawn count | 111 | 1 |
| Hazard entries | 144,000 | <5,000 |
| Test suite | 282 green | 283+ green |

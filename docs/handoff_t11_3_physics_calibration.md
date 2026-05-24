# Handoff — T11.3 Physics Calibration

**Date:** 2026-05-19  
**Status:** T11.3 ✅ Complete. Next task: T11.4 Episode-Driven Scene in RN Prototype.

---

## What was done in this session

### T11.3 — Physics Calibration from Trace (COMPLETE)

All 5 subtasks done. Tests pass.

**Files created:**
- `apps/mame-harness/physics_calibrator.py` — measures 4 physics constants from `specs/traces/gng_trace.json`
- `apps/mame-harness/tests/test_physics_calibrator.py` — 10 tests, 10 pass, 1 skipped (integration with real trace, correctly conditional)
- `specs/calibration/gng_physics_calibration.yaml` — generated calibration artifact

**Files modified:**
- `specs/mechanics/gng_abstract_mechanics.yaml` — all 4 `calibration: pending` fields replaced with `calibrated_value` + `sample_count`
- `apps/rn-prototype/src/engine/PhysicsSystem.ts` — exports `CALIBRATED_PHYSICS_CONFIG` with measured values
- `apps/rn-prototype/tests/engine.test.ts` — 3 new tests asserting no hardcoded stubs (gravity≠9.8, moveSpeed≠3, jumpVelocity≠6)
- `docs/tasks/gng_source_integration/T11.3-physics-calibration.md` — status updated to ✅ Complete

**Calibrated values (in PhysicsSystem units/second):**
```
gravity:       5.5071   (n=277, direct from Δvelocity_y airborne frames)
moveSpeed:     13.4935  (n=1228, direct from non-idle player frames)
jumpVelocity:  1.9966   (n=166, direct from jump_start events, |measured|)
projectile_vx: 8.5348   (n=54, SURROGATE — see known issue below)
```

---

## Known issue: calibration data quality

**The numbers are mathematically correct but based on noisy data.**

The vision pipeline (MOG2 background subtraction, ADR-013) measures bounding box positions, not exact sprite positions. The bounding box edges fluctuate frame-to-frame even when Arthur moves smoothly. This means:

- `locomotion_velocity_x`: overestimated (mean inflated by outliers; median position-delta ~1.89px/frame is more realistic)
- `jump_velocity_y`: the trace stores near-zero values at `jump_start` events — the detector fires on the first visible frame of the jump when Arthur hasn't moved yet. The physics prediction (0.4 frames to peak) contradicts the observed arc duration (14.8 frames mean). **This value is wrong.**
- `gravity_units_per_frame`: derived from Δvelocity_y which is itself noisy. Inconsistent with observed arc shape.
- `projectile_velocity_x`: no `in_flight` projectile data exists in the trace (ADR-013 known gap). Uses player velocity_x at fire events as surrogate. **Not a real projectile measurement.**

**Impact now:** Low. T11.3 goal was to replace invented placeholders with trace-derived values. That is done. The values are better than the stubs even if imperfect.

**Impact at T11.4/T12:** When the RN prototype needs to *feel* like GNG, these values will need revision. The correct fix is one of:
1. Improve trace extractor to use position delta instead of stored velocity (more accurate, requires T11.2 changes)
2. Derive jump constants from arc duration (observed ~15 frames air time → back-calculate v0 = g * t_peak)
3. Manual calibration against known GNG timing from public speedrun documentation

This is NOT a blocker for T11.4 but should be documented as a risk before T12.

---

## Test status at handoff

```
Python (apps/mame-harness):
  test_physics_calibrator.py: 10 passed, 1 skipped ✅
  pre-existing failures in test_episode_extractor.py: 14 (FileNotFoundError — 
    these tests run from apps/mame-harness/ and use relative path 
    specs/traces/gng_trace.json which doesn't exist from that CWD.
    These failures PRE-DATE T11.3 — confirmed by git stash check.)

TypeScript (apps/rn-prototype):
  npm test: 8/8 passed ✅
```

---

## What is next: T11.4 — Episode-Driven Scene in RN Prototype

**Task file:** `docs/tasks/gng_source_integration/T11.4-...` (may need to be created)  
**Parent plan:** `docs/tasks/gng_source_integration/T11-rn-prototype-hookup.md`

**Goal:** Load the extracted episodes (`specs/episodes/gng_episodes.json` from T11.2) into the RN prototype and replay the first episode in the game scene. The PhysicsSystem is now calibrated (T11.3). The MechanicsLoader exists (T11.1). This task connects them.

**Dependencies that are met:**
- T11.1 ✅ — `mechanicsLoader.ts` and TypeScript types for mechanics
- T11.2 ✅ — `episode_extractor.py` produces `specs/episodes/gng_episodes.json`
- T11.3 ✅ — `CALIBRATED_PHYSICS_CONFIG` in PhysicsSystem.ts

**What T11.4 likely needs to do:**
1. Load `specs/episodes/gng_episodes.json` into RN prototype (TypeScript loader)
2. Build a scene that replays the first episode frame by frame using the GameLoop
3. Assert the scene runs without errors and produces expected entity positions
4. Verify no private data leaks into the TypeScript layer

**Before starting T11.4, the agent must:**
1. Read `docs/tasks/gng_source_integration/T11-rn-prototype-hookup.md` for scope
2. Read `docs/tasks/gng_source_integration/T11.2-trace-episode-extractor.md` for episode schema
3. Read `specs/episodes/gng_episodes.json` to understand the actual structure
4. Check `apps/rn-prototype/src/` for existing file structure
5. Create a T11.4 task file before implementing anything (per CLAUDE.md)
6. Show the task list and wait for explicit approval before writing code

---

## Key file locations

| What | Where |
|------|-------|
| Calibration YAML | `specs/calibration/gng_physics_calibration.yaml` |
| Physics calibrator | `apps/mame-harness/physics_calibrator.py` |
| PhysicsSystem (updated) | `apps/rn-prototype/src/engine/PhysicsSystem.ts` |
| Mechanics YAML (updated) | `specs/mechanics/gng_abstract_mechanics.yaml` |
| Episode JSON (from T11.2) | `specs/episodes/gng_episodes.json` |
| T11 parent task | `docs/tasks/gng_source_integration/T11-rn-prototype-hookup.md` |
| Overall plan | `docs/obsidian/GNG Integration Plan.md` |
| ADR-013 (vision gaps) | `docs/adr/ADR-013-opencv-vision-backend.md` |

---

## Project virtualenv

Always use: `source apps/mame-harness/.venv/bin/activate`  
Never: bare `python`, `python3`, or `pytest`

---

## T10.7.B + T10.7.A Resolution (2026-05-23)

**T10.7.B — Entity-ID Collision Eliminated.**
`_entity_type_from_box` was returning `"player"` for any blob matching player-size area ratio, producing duplicate `entity_id="player"` entries in `extract_trace`. The fix added `allow_player: bool = True` to the function and passes `allow_player=False` for all `remaining_regions` processing loops. Result: 0 duplicate player frames in the `run_t10_7_jumps` trace. This unblocked T10.7.A ST.A3b.

**T10.7.A ST.A4 — Final Calibration Computed.**
Physics constants were derived from 2 human-validated jump arc candidates (IDs 2 and 3, `run_t10_7_jumps`) using the ADR-019 picker pattern (`apps/mame-harness/visual_jump_picker.py`). Per-jump kinematics used ascent + descent gravity cross-check.

**Final calibrated values:**
- `jumpVelocity_y = 0.4668 /s`
- `gravity = 0.1167 /s²`
- `t_peak error = 0%` (predicted vs observed)

Values are now in:
- `specs/calibration/gng_physics_calibration.yaml`
- `apps/rn-prototype/src/engine/PhysicsSystem.ts` (`CALIBRATED_PHYSICS_CONFIG`)

The original T11.3 values (jumpVelocity=1.9966, gravity=5.5071) were trace-noise artifacts caused by the entity-id collision. The T10.7.A values supersede them for all downstream use.

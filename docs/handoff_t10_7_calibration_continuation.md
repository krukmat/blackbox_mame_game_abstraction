# Handoff — T10.7 Calibration Continuation (T10.7.C + T10.7.D + ST5)

**Date:** 2026-05-23  
**Status:** T10.7.A ✅ T10.7.B ✅ T10.7.C ✅ T10.7.D ✅ — next: T10.7.E → ST5

---

## What was done

| Task | Result |
|---|---|
| T10.7.A | jump/gravity calibrated via ADR-019 picker. `jumpVelocity=0.4668/s`, `gravity=0.1167/s²`, `t_peak error=0%`, 2 human-validated candidates from `run_t10_7_jumps` |
| T10.7.B | `_entity_type_from_box` now takes `allow_player: bool = True`; both `remaining_regions` loops in `extract_trace` pass `allow_player=False` — zero duplicate player frames |

**Values currently in PhysicsSystem.ts:**
```typescript
gravity:     0.1167   // ✅ T10.7.A
jumpVelocity: 0.4668  // ✅ T10.7.A
moveSpeed:   1.8709   // ⚠️ unreliable — from jump-only trace (n=83), conflicts with T11.3 value (13.4935, n=1228)
```

`specs/mechanics/gng_abstract_mechanics.yaml` still has **stale T11.3 values** for jump, gravity, locomotion, and projectile — not yet synced. That sync is ST5, which is blocked until T10.7.C and T10.7.D complete.

---

## What to do next

### Step 1 — T10.7.C ✅ Complete

Locomotion calibration completed from `run_t10_7_walk` using the ADR-019 picker workflow.

Accepted walk candidates: **3, 5, 8, 10**  
Computed values:
- `velocity_x_per_frame = 0.004671`
- `velocity_x_per_second = 0.2786`
- `sample_count = 24`

Artifacts updated:
- `specs/calibration/gng_physics_calibration.yaml`
- `specs/mechanics/gng_abstract_mechanics.yaml` (locomotion only)
- `apps/rn-prototype/src/engine/PhysicsSystem.ts`

### Step 2 — T10.7.E (Effort M, new implementation branch)

Read `docs/tasks/gng_source_integration/T10.7.E-projectile-in-flight-tracking.md` and `docs/adr/ADR-020-projectile-in-flight-tracking.md`.  
Implement real in-flight projectile tracking plus an ADR-019 picker workflow. Do not propagate a projectile calibration value from player-motion surrogates.

Evidence status update:
- `run_t10_7_walk` was rejected for projectile calibration because the expanded input plan contains no fire input; candidates were player-motion false positives.
- `run_e18611b8a7e7` has fire input, but reviewed candidate groups showed Arthur death / non-projectile motion, not visible projectile flight.
- Existing evidence is therefore insufficient for public `projectile_velocity_x` calibration.

Minimum next capture:
- controllable gameplay with player kept alive on stable ground
- at least 5 separated fire inputs
- at least 20 no-input frames after each fire input
- minimal player movement during the projectile sample window
- no enemy/body overlap near the projectile lane if possible
- goal: at least 3 projectile trajectories with 4+ consecutive visible frames each

### Step 3 — ST5 (after T10.7.E complete)

Propagate all four calibrated values to `specs/mechanics/gng_abstract_mechanics.yaml` in one pass.  
Regenerate `specs/episodes/gng_episodes.json` from the current `specs/traces/gng_trace.json`.  
Verify ≥ 3 episodes each with ≥ 1 `jump_start`.

---

## Critical constraints

```bash
# Always use the project venv — never bare python/pytest
source apps/mame-harness/.venv/bin/activate

# No commit if tests are broken
pytest apps/mame-harness/tests/
pytest packages/vision/tests/
cd apps/rn-prototype && npm test
```

- All agent-facing artifacts: English
- All user communication: Spanish
- Never present a task as ready without a task file
- Show task list + wait for explicit approval before implementation (per CLAUDE.md)
- T10.7.E is now the active blocker before ST5

### ST.C1 operator note

Because enemies appear quickly, the locomotion capture should prefer **short clean walking segments** over long risky ones:

- walk left for ~1–2 seconds
- pause briefly
- walk right for ~1–2 seconds
- pause briefly
- repeat for 2–3 cycles if possible
- if enemies force it, short defensive jumps are acceptable

Do not fire during the capture. Accepted locomotion segments must still be flat-ground walking only.

---

## Key file locations

| What | Where |
|---|---|
| T10.7.C task doc | `docs/tasks/gng_source_integration/T10.7.C-locomotion-calibration.md` |
| T10.7.D task doc | `docs/tasks/gng_source_integration/T10.7.D-projectile-velocity-decision.md` |
| T10.7.E task doc | `docs/tasks/gng_source_integration/T10.7.E-projectile-in-flight-tracking.md` |
| T10.7 parent task | `docs/tasks/gng_source_integration/T10.7-tracker-continuity-fix.md` |
| Calibration YAML | `specs/calibration/gng_physics_calibration.yaml` |
| Mechanics YAML | `specs/mechanics/gng_abstract_mechanics.yaml` |
| PhysicsSystem | `apps/rn-prototype/src/engine/PhysicsSystem.ts` |
| Reference picker | `apps/mame-harness/visual_jump_picker.py` (ADR-019 reference impl) |
| ADR-019 | `docs/adr/ADR-019-human-validated-calibration-candidates.md` |
| ADR-020 | `docs/adr/ADR-020-projectile-in-flight-tracking.md` |
| Integration plan | `docs/plans/gng_source_integration_plan.md` |

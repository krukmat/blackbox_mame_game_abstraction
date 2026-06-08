# ADR-024 — Designed Isolation-Experiment Calibration

## Status

Accepted (T20.3, 2026-06-07). Supersedes ADR-019 as the **default** calibration method;
ADR-019 (human-validated candidate pickers) is retained as the **fallback** for constants
that cannot be isolated by a designed experiment.

## Date

2026-06-07

## Context

Calibrating the physics constants (locomotion speed, jump velocity, gravity, projectile
speed, spawn delay) historically used freeform gameplay captures: the operator played, the
trace was extracted, and a per-constant picker (ADR-019) surfaced candidate frames that the
operator accepted/rejected against private PNGs. That workflow is correct but does not scale —
it requires synchronous human judgment per constant per game, and ADR-019 itself records that
it "reduces but does not eliminate" per-topic manual engineering. Pure automation over
freeform traces was rejected (ADR-019) because trace noise produced physically inconsistent
constants (`t_peak` off by ~40×).

The root cause is the *capture design*, not the math. Freeform play mixes every mechanic into
one noisy signal, so a human is needed to find the clean segments. Because the input layer is
deterministic YAML (ADR-009) and inputs are now ground-truth (ADR-023), we can instead **design
the capture** so each run exercises exactly one mechanic in isolation. A clean, single-variable
signal can be measured with a closed-form or regression with no human candidate selection.

## Decision

Adopt **designed isolation experiments** as the default calibration capture method. An
experiment is an ordinary input plan plus an embedded `experiment` block; each plan isolates
exactly one mechanic.

**Format.** The `experiment` block lives inside the input-plan YAML (so it runs through the
existing Lua path unchanged) and carries:

```yaml
experiment:
  experiment_id: walk_right
  isolated_variable: locomotion_velocity_x   # baseline | locomotion_velocity_x | jump_arc | projectile
  measurement_window: { start_frame: 1535, end_frame: 1645 }   # absolute expanded-frame indices
  expected_signal: monotone_x                # none | monotone_x | parabolic_y | linear_x
```

Schema: `packages/schemas/experiment_plan.schema.json`. Loaded and validated by
`input_planner.load_input_plan` (`ExperimentSpec`).

**Structural isolation guarantee.** `load_input_plan` validates that the measurement window is
within the expanded plan range, and that inside the window only the isolated variable's allowed
non-noop actions appear (`baseline`→{}, `locomotion_velocity_x`→{move_left,move_right},
`jump_arc`→{jump}, `projectile`→{fire}). A plan that mixes mechanics in its window fails to
load. Isolation is enforced, not documented.

**GNG battery** (`plans/sequences/`): `gng_exp_idle_baseline`, `gng_exp_walk_right`,
`gng_exp_jump_in_place`, `gng_exp_fire_stationary`. Each shares the calibrated boot prefix
(controllable at frame 1505) then performs one isolated action.

**Determinism.** Per ADR-009, the same experiment plan produces the same frame sequence; with
ground-truth inputs (ADR-023) the calibration (T20.4) is reproducible without human input.

**ADR-019 relationship.** ADR-019 is demoted from default to fallback: it remains the
mechanism for constants that genuinely cannot be isolated by a designed experiment, and for
auditing low-fit experiment results.

## Consequences

**Positive**
- Standard physics constants are calibrated with **no human picker**, removing the dominant
  per-constant manual cost and the tribal-knowledge risk ADR-019 flagged.
- Isolation is structurally enforced at load time, so a malformed/non-isolated experiment
  cannot silently produce a bad constant.
- Scales across games (ADR-005): a new title needs a battery of experiment plans, not bespoke
  picker tooling per constant.

**Negative**
- Requires designing experiments that truly isolate each variable and choosing clean
  measurement windows; a poorly designed window yields a poor constant (mitigated by the
  isolation check and by T20.4 fit-quality flags).
- Measurement windows use absolute frame indices, so they must be recomputed if the boot
  prefix or step durations change.
- Capturing the battery is an operator step (each plan must be run against the ROM once).

## Alternatives Considered

1. **Keep ADR-019 pickers as default.** Rejected — does not scale; retained as fallback.
2. **Pure automation over freeform traces.** Rejected (per ADR-019) — noise yields inconsistent
   constants.
3. **Relative measurement windows (offset from the isolated action).** Deferred — robust to
   boot changes but pushes offset-resolution logic into the calibrator; absolute indices were
   chosen for T20.3 simplicity.
4. **Separate experiment file referencing a plan.** Rejected — two files per experiment; the
   embedded block keeps the run and its metadata together and reuses the existing load path.

## Related

- [ADR-009](./ADR-009-input-plan-determinism.md) — deterministic input plans this builds on
- [ADR-019](./ADR-019-human-validated-calibration-candidates.md) — demoted to fallback by this ADR
- [ADR-023](./ADR-023-ground-truth-input-timeline.md) — ground-truth inputs that make isolation measurable
- [ADR-005](./ADR-005-source-profile-driver-contract.md) — multi-game scaling goal
- `packages/schemas/experiment_plan.schema.json`, `apps/mame-harness/input_planner.py`
- `plans/sequences/gng_exp_*.yaml` — the GNG battery
- `docs/plans/automated_mapping_pipeline_plan.md`, `docs/tasks/automated_mapping_pipeline/T20.3-experiment-battery.md`
- Consumer: T20.4 deterministic auto-calibrator

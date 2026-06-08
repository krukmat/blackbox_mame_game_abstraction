# ADR-024 — Designed Isolation-Experiment Calibration

tags: #adr #calibration #experiments

**Status**: Accepted (T20.3, 2026-06-07) — default method; [[ADR-019 Human-Validated Calibration Candidates]] demoted to fallback | **Date**: 2026-06-07

## Problem

Physics calibration used freeform captures + per-constant human pickers ([[ADR-019 Human-Validated Calibration Candidates]]). Correct but unscalable; pure automation over noisy freeform traces gave inconsistent constants (`t_peak` off ~40×). The root cause is capture *design* — freeform play mixes every mechanic into one noisy signal.

## Decision

Designed **isolation experiments** are the default. Each is an input plan with an embedded `experiment` block isolating one mechanic; a clean single-variable signal is measured with closed-form/regression — no human picker.

- Block lives in the input-plan YAML (runs through the existing Lua path), validated by `input_planner.load_input_plan` (`ExperimentSpec`); schema `packages/schemas/experiment_plan.schema.json`.
- `isolated_variable` ∈ {baseline, locomotion_velocity_x, jump_arc, projectile}; `measurement_window` = absolute expanded-frame indices; `expected_signal` ∈ {none, monotone_x, parabolic_y, linear_x}.
- **Isolation is structurally enforced**: only the variable's allowed non-noop actions may appear in the window, else the plan fails to load.
- GNG battery in `plans/sequences/`: idle_baseline, walk_right, jump_in_place, fire_stationary (shared boot prefix → controllable at 1505 → one isolated action).
- Deterministic ([[ADR-009 Input Plan Determinism]]) + ground-truth inputs ([[ADR-023 Ground-Truth Input Timeline]]) → reproducible calibration.

## Related

- [[ADR-009 Input Plan Determinism]]
- [[ADR-019 Human-Validated Calibration Candidates]] (fallback)
- [[ADR-023 Ground-Truth Input Timeline]]
- [[ADR-005 Source Profile Pattern]]
- Full ADR: `docs/adr/ADR-024-designed-experiment-calibration.md`
- Consumer: T20.4 deterministic auto-calibrator

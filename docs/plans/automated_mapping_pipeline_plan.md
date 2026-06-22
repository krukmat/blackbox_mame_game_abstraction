# Automated Mapping Pipeline Plan

## Status

Proposed — awaiting approval. Created 2026-06-07.

> **Partially superseded by ADR-028 (2026-06-18).** Levels 0–1 (T20.1–T20.4b, input timeline +
> isolation experiments) and the memory tap (T20.5, ADR-026) are retained and absorbed into the
> memory-mapping-first re-architecture (`docs/plans/memory_mapping_first_rearchitecture_plan.md`).
> Tasks **T20.7, T20.8, T20.9, T20.10** and the unauthored reservations **ADR-025** and
> **ADR-027** are **Deprecated** — their goals (scroll robustness, entity identity,
> generalization) are met by the memory-mapping + declarative-bundle design and may be revisited
> only as fallback hardening after the player-only vertical slice is verified.

## Purpose

Re-architect the "mapping" process (MAME observation → public abstract mechanics)
so that it is **as automated as possible** and **scales across MAME titles**, while
keeping the clean-room boundary intact.

The current pipeline reverse-engineers, from the rendered pixel output, almost
everything that the emulation already knows deterministically. That choice forced
a long tail of manual, per-entity, per-constant work (ADR-012 through ADR-022 are
largely patches to pixel-based reconstruction). This plan stops re-deriving known
signals and replaces hand-tuned, human-in-the-loop calibration with deterministic,
designed measurement.

This plan does **not** weaken the clean-room rule. Clean-room constrains what is
*published* (only abstract numbers cross the boundary). It does not constrain what
the framework *measures internally* to produce those numbers — provided the
measurement and its inputs never leak to public artifacts.

## Problem Statement (diagnosis)

Three structural inefficiencies in the current mapping process:

1. **Events are re-derived from CV when they are the inputs.** `movement_start/stop`,
   `jump_start`, `fire` are exactly the player inputs. The harness *generates* and
   *injects* them (`scripts/mame_autoboot.lua`, ADR-009). Scripted plans exploit this
   partially (`trace_extractor._infer_events` Rule 4); manual captures discard it and
   infer everything from noisy velocity thresholds.
2. **Quantitative physics comes 100% from pixel bbox centers.** Finite differences on
   frame-diff centroids are noisy. Pure automation produced physically inconsistent
   constants (ADR-019 records `t_peak` off by ~40×). That noise is the sole reason the
   human-validated picker apparatus (ADR-019: `visual_jump_picker`, `walk_segment_picker`,
   `projectile_trajectory_picker`, `enemy_signature_picker`) exists. Every constant needs
   a human.
3. **Entity identity needs a hand-calibrated CV signature per enemy** (ADR-012, ADR-021)
   plus scroll-reset hacks for camera motion (ADR-022). None of this transfers to a new
   game without redoing every signature.

Net effect: onboarding a new MAME title currently costs weeks of per-entity CV calibration
plus dozens of human picks. This contradicts the ADR-005 goal of scaling across games and
the ADR-019 admission that the picker pattern "reduces but does not eliminate" per-topic
manual engineering.

## Design Decisions

The work is organized into four capability levels plus generalization. Each level is
independently valuable and ordered by ROI/risk.

### Level 0 — Ground-truth input join (no legal risk)
Log the *actual* per-frame input state (including human keyboard during manual play) from
the Lua bridge into a private `input_timeline.json`, and derive `movement_*`, `jump_start`,
`fire` from it. CV event inference is demoted to a fallback for frames with no input record.

### Level 1 — Designed isolation experiments (no legal risk)
Replace freeform capture + human candidate-picking with a small battery of deterministic
input plans, each isolating exactly one variable (idle baseline, walk, jump-in-place,
fire-stationary). Because each experiment isolates one variable, calibration is a
closed-form/regression with no human picker. ADR-019 becomes the fallback for constants
that genuinely cannot be isolated, not the default.

### Level 2 — Modern vision (no legal risk)
Replace per-entity hand signatures and the MOG2 scroll-reset hack with:
- optical-flow global-motion estimation to detect and *compensate* camera scroll
  automatically (works on all stages, not just stage 1);
- generic motion segmentation + tracking-by-detection (SORT/ByteTrack-style) for
  persistent IDs without per-entity calibration.

### Level 3 — Internal-state observation + semantic extraction (requires explicit decision)
- **Memory tap (gated by a clean-room decision):** read entity position/state from MAME RAM
  via Lua, using *community cheat-database* addresses (community-authored, not derived from
  the ROM). This yields exact, noise-free state with no CV. It "enters the box," so it
  requires an explicit clean-room boundary decision (ADR-026) before any implementation.
- **VLM-assisted archetype labeling:** a vision-language model proposes entity archetypes
  and candidate mechanics from short clips; the human bulk-confirms instead of accepting
  candidates one by one.

### Generalization
A declarative per-game "mapping profile" binds the experiment battery, optional memory
addresses, and confirmed archetypes so that onboarding a new MAME title is configuration,
not bespoke CV engineering.

## Decision Gate (reshapes the plan)

`T20.0` authors ADR-026 (internal-state observation boundary) as **Proposed** and requires
the approver to decide Accepted/Rejected. The outcome prunes Phase 3:

- **Accepted** → memory-tap path (`T20.5`, `T20.6`) is in scope; the modern-vision path
  (`T20.7`, `T20.8`) becomes optional hardening rather than the primary positional source.
- **Rejected** → memory-tap tasks are dropped; modern vision (`T20.7`, `T20.8`) is the
  primary path to noise-reduced positions and entity identity.

Levels 0 and 1 do not depend on this decision and proceed regardless.

## New ADRs to author (planning deliverables)

Per the project's "New Feature Documentation Requirements," each architectural decision is
documented before its implementation begins. ADR numbers continue after the current highest
(ADR-022).

| ADR | Decision | Authored in |
|-----|----------|-------------|
| ADR-023 | Ground-truth input timeline supersedes CV event inference (CV is fallback) | T20.1 |
| ADR-024 | Designed isolation-experiment calibration; ADR-019 demoted to fallback | T20.3 |
| ADR-025 | DEPRECATED by ADR-028 (never authored) — Optical-flow scroll compensation + tracking-by-detection vision backend | T20.7 |
| ADR-026 | Internal-state (RAM) observation clean-room boundary — **decision gate** | T20.0 |
| ADR-027 | DEPRECATED by ADR-028 (never authored) — VLM-assisted archetype/mechanic labeling with bulk human confirmation | T20.9 |

Each ADR task must also update the ADR Index in `CLAUDE.md` and `AGENTS.md`, add an Obsidian
note, update `docs/obsidian/README.md` and `docs/obsidian/00 - Project Overview.md`, and
remove any Known Gap it resolves.

## Task List (topologically ordered)

| ID | Title | Depends on | Reasoning | Effort | Model |
|----|-------|-----------|-----------|--------|-------|
| T20.0 | Internal-state observation clean-room decision (ADR-026) | — | High | Low | Opus |
| T20.1 | Per-frame input-state logger (Lua → private input_timeline) (ADR-023) | — | Medium | Medium | Opus |
| T20.2 | Event derivation from input timeline (CV demoted to fallback) | T20.1 | Medium | Medium | Sonnet |
| T20.3 | Experiment-plan schema + GNG isolation battery (ADR-024) | T20.1 | Medium | Medium | Opus |
| T20.4 | Deterministic auto-calibrator (no human picker) | T20.3 | High | Medium | Opus |
| T20.4b | Battery orchestrator + fail-fast validation + robust windows (minimize manual, no retries) | T20.3, T20.4 | High | Medium | Opus |
| T20.5 | Lua memory-tap → private numeric state timeline (ADR-026 impl) | T20.0=Accepted | High | Medium | Opus |
| T20.6 | Memory-sourced calibration + RAM↔CV cross-check (plugs into T20.4b verdict) | T20.5, T20.4b | Medium | Medium | Sonnet |
| T20.7 | DEPRECATED (ADR-028) — Optical-flow scroll estimation + compensation (ADR-025 pt.1) | T20.0 | High | Medium | Opus |
| T20.8 | DEPRECATED (ADR-028) — Generic motion segmentation + tracking-by-detection (ADR-025 pt.2) | T20.7 | High | High | Opus |
| T20.9 | DEPRECATED (ADR-028) — VLM-assisted archetype + mechanic labeling (ADR-027) | T20.2, T20.4 | High | Medium | Opus |
| T20.10 | DEPRECATED (ADR-028; folded into the integration bundle) — Declarative per-game mapping profile | T20.3, T20.4, T20.9 | High | Medium | Opus |
| T20.11 | End-to-end clean-room + reproducibility verification | all | Medium | Medium | Sonnet |

## Dependency Rationale

- `T20.0` is first because its outcome (memory tap allowed or not) reshapes Phase 3. It is a
  decision, not an implementation; it gates `T20.5`/`T20.6`.
- `T20.1` before `T20.2`/`T20.3` because both consume the ground-truth input timeline.
- `T20.3` before `T20.4` because the calibrator runs the experiment battery.
- `T20.4b` (battery orchestrator) follows `T20.4` and exists to make operator participation
  minimal and retry-free: one command runs capture→extract→calibrate with fail-fast,
  experiment-specific validation and stable-sub-window auto-detection, so the operator never
  retries blindly. `T20.6` plugs its RAM↔CV cross-check into the orchestrator's verdict.
- `T20.5` before `T20.6`; both require `T20.0 = Accepted`.
- `T20.7` before `T20.8` because tracking-by-detection needs scroll-compensated frames.
- `T20.9` after `T20.2` and `T20.4` because archetype labeling needs clean traces and
  calibrated physics to ground its suggestions.
- `T20.10` last among capability work because the per-game profile binds all prior outputs.
- `T20.11` audits the whole graph after everything lands.

## Affected Modules (anticipated; finalized per task)

- `scripts/mame_autoboot.lua` — input-state logging (T20.1), memory tap (T20.5)
- `packages/vision/trace_extractor.py` — event source switch (T20.2)
- `apps/mame-harness/` — experiment battery + auto-calibrator (T20.3/T20.4), memory calibration
  (T20.6), mapping profile (T20.10)
- `packages/vision/frame_differ.py`, new `scroll/optical-flow` + `tracking` modules (T20.7/T20.8)
- `packages/schemas/` — experiment-plan schema, input-timeline schema, mapping-profile schema
- `specs/calibration/` — calibration outputs (regenerated deterministically)
- `docs/adr/`, `docs/obsidian/`, `CLAUDE.md`, `AGENTS.md` — ADR-023..027 + indices

## Module Dependency Notes

- Level 0/1 keep the existing OpenCV positional source; they only change *event* sourcing and
  *capture design*, so they are safe to land before any vision rewrite.
- Level 2 replaces positional/identity internals behind the existing `FrameDiffStat` /
  trace contract; downstream public artifacts must remain schema-stable.
- Level 3 memory tap must pass the same guardrails as every public writer: only numbers cross,
  no addresses or ROM-derived strings in public output.

## Deliverables

- ADR-023, ADR-024, ADR-025, ADR-026 (decision), ADR-027 with full index/vault updates.
- Private `input_timeline.json` produced for every capture; events sourced from it.
- An experiment battery (deterministic input plans) + an auto-calibrator producing
  `specs/calibration/*` with **zero human picks** for the standard constants.
- (If ADR-026 Accepted) a Lua memory-tap producing a private numeric state timeline + a
  CV-vs-memory consistency report.
- Modern vision: automatic scroll compensation + per-entity-signature-free tracking.
- VLM-assisted archetype labeling with bulk confirmation.
- A declarative per-game mapping profile that makes a new MAME title onboarding-by-config.
- An end-to-end verification proving determinism + clean-room safety.

## Exit Criteria

- Standard physics constants (walk, jump, gravity, projectile) are calibrated with **no
  human picker** for GNG via the experiment battery, and the values are reproducible from the
  same plans.
- Events in the public trace are sourced from ground-truth input for both scripted and manual
  captures.
- Adding a second MAME title requires defining a mapping profile (battery + optional addresses
  + archetype confirmations), not new per-entity CV code.
- All public artifacts still pass `ensure_no_private_paths`; no addresses, ROM paths, or
  pixel content leak.
- The clean-room decision (ADR-026) is recorded with an explicit Accepted/Rejected status.

## Progress Log

- **T20.0** ✅ **Complete (2026-06-07).** `docs/adr/ADR-026-internal-state-observation-boundary.md`
  authored and **Accepted under the constrained contract** (clauses 1–5; clause 4 binding —
  memory is a private measurement/verification accelerator, not the published source of truth).
  Approver decision recorded in the ADR. Obsidian note added; ADR Index updated in `CLAUDE.md`,
  `AGENTS.md`, `docs/obsidian/README.md`, `docs/obsidian/00 - Project Overview.md`.
  **Consequence for the plan:** T20.5/T20.6 (memory tap) are **in scope**; T20.7/T20.8 (modern
  vision) remain valuable hardening rather than the sole positional source.
- **T20.1** ✅ **Complete (2026-06-07).** `scripts/mame_autoboot.lua` now records the effective
  per-frame input state (injected plan OR human keyboard) to a private
  `evidence/private/run_<id>/logs/input_timeline.json` (read via `port:read()` +
  `(value ~ defvalue) & mask`; deterministic `BUTTON_ORDER`; count-only stdout). Wired
  `BLACKBOX_INPUT_TIMELINE_PATH` in `scripts/launch_manual_capture_autoboot.sh` and
  `apps/mame-harness/cli.py` (with a Lua fallback deriving the path from the plan path). Added
  `packages/schemas/input_timeline.schema.json` and `apps/mame-harness/input_timeline.py`
  (loader/validator + `timeline_matches_plan`). ADR-023 authored (Accepted); Obsidian note +
  ADR indices updated across `CLAUDE.md`, `AGENTS.md`, `docs/obsidian/README.md`,
  `docs/obsidian/00 - Project Overview.md`. Unit tests added
  (`apps/mame-harness/tests/test_input_timeline.py`, 17 cases passing). **Operator integration
  check pending:** real scripted/manual capture to confirm the MAME-produced timeline (HP-1/HP-2).
- **T20.2** ✅ **Complete (2026-06-07).** `trace_extractor` now sources input-driven player
  events from the ground-truth timeline: `_infer_events` gained an `input_events` mode where
  `fire`/`jump_start` come from real button edges (button2/button1) and the CV (Rule 3)
  `jump_start` is suppressed; `extract_trace` gained an `input_timeline` param and computes
  per-frame player button edges; `vision_pipeline.extract_run_trace` loads the private
  `input_timeline.json` (via `_resolve_input_timeline`) and passes it, falling back to the
  legacy plan/CV path when absent. Covered by ADR-023 (no new ADR).
- **T20.3** ✅ **Complete (2026-06-07).** Added `packages/schemas/experiment_plan.schema.json`
  and extended `apps/mame-harness/input_planner.py` with `ExperimentSpec`/`MeasurementWindow`
  (embedded `experiment` block; **structurally-enforced isolation** — only the isolated
  variable's allowed non-noop actions may appear in the measurement window, else the plan
  fails to load). Authored the GNG battery in `plans/sequences/`: `gng_exp_idle_baseline`,
  `gng_exp_walk_right`, `gng_exp_jump_in_place`, `gng_exp_fire_stationary` (shared boot prefix
  → controllable at 1505 → one isolated action; all four load + validate). ADR-024 authored
  (Accepted; default method) and ADR-019 demoted to fallback; ADR indices updated across
  `CLAUDE.md`, `AGENTS.md`, `docs/obsidian/README.md`, `docs/obsidian/00 - Project Overview.md`.
- **T20.4** ✅ **Complete (2026-06-07).** Added `apps/mame-harness/experiment_calibrator.py`:
  reads an experiment plan + public trace, slices to the measurement window, and measures
  constants by least-squares — locomotion (linear x), jump_velocity_y + gravity (quadratic y),
  projectile_velocity_x (linear projectile x) + spawn_delay (fire-edge → first projectile),
  baseline noise (idle std). Writes/merges the new public artifact
  `specs/calibration/gng_experiment_calibration.yaml` (numbers-only, guardrail-checked) with
  per-constant provenance (experiment_id, window, r²). Gates: `needs_human_review` when
  r² < 0.95 (ADR-019 fallback); jump `t_peak` consistency check (closes the ADR-019 ×40
  failure mode); projectile refuses a player-motion surrogate (ADR-020). No human picks.
  Synthetic verification recovered exact constants (r²=1.0, t_peak consistent). Covered by
  ADR-024 (no new ADR). **Operator step pending:** run the battery captures to produce real
  values.
- **T20.5** ✅ **Complete (2026-06-07).** Implemented the ADR-026 RAM memory tap.
  `scripts/mame_autoboot.lua` lazily loads a private JSON address map
  (`BLACKBOX_MEMORY_MAP_PATH`), reads per-entity fields each frame via
  `space:read_u8/u16`, and writes `{frame,entity,x,y,state_flags}` to a private
  `evidence/private/run_<id>/logs/state_timeline.json` — count-only stdout, never
  addresses/values (clause 2); inert with no config (clause 5). `apps/mame-harness/memory_map.py`
  loads/validates the operator's local YAML and exports it to the private JSON (YAML→JSON
  mirror of the input-plan flow); committed template `blackbox.local.memory_map.example.yaml`
  has placeholder addresses only; `.gitignore` covers the real `blackbox.local.memory_map.yaml`.
  Wired conversion + env (`BLACKBOX_MEMORY_MAP_PATH`/`BLACKBOX_STATE_TIMELINE_PATH`) in
  `apps/mame-harness/cli.py` and `scripts/launch_manual_capture_autoboot.sh`. Verified: YAML→JSON
  + validation, and `luac -p` Lua syntax. Implements ADR-026 (no new ADR). **Operator step
  pending:** populate the local YAML from a community cheat DB to produce real state.
- **T20.4b** ✅ **Complete (2026-06-07).** Added `apps/mame-harness/battery_calibrator.py` +
  the `calibrate-battery` CLI subcommand. One command, per experiment: capture (auto-launch
  scripted run via `run_mame` with `-nothrottle -sound none` + frames cap so MAME exits on its
  own; or reuse an existing run via `--run-id stem=<id>`) → ffmpeg frame extraction →
  `extract_run_trace` → **fail-fast specific validation** (player detected, capture covers the
  window, isolated entity present — each failure names the experiment + a concrete fix) →
  **stable sub-window auto-detection** (`detect_window`, robust to timing jitter) →
  `experiment_calibrator` (with `window_override`). Emits one verdict table
  (PASS/REVIEW/RERUN, "Re-run only: …") and writes `gng_experiment_calibration.yaml`. No blind
  operator retries; analysis-window widening is automatic/deterministic. Verified logic on
  synthetic data (jitter-robust window, specific RERUN reasons, table render) + subcommand
  registration. Operator-efficiency task per [[feedback-minimize-manual-participation]]; no new
  ADR (builds on ADR-024).
- T20.6 – T20.11 🔲 Not started.

## Reference Documents

- This plan: `docs/plans/automated_mapping_pipeline_plan.md`
- Parent context: `docs/plans/gng_source_integration_plan.md`
- `README.md`, `AGENTS.md`, `CLAUDE.md`
- Governing ADRs: ADR-001 (layered architecture), ADR-003 (public blocklist), ADR-006 (vision
  numeric-only), ADR-008 (behavioral validation), ADR-009 (input plan determinism),
  ADR-012/013/021/022 (current vision/tracking), ADR-019 (human-validated calibration —
  superseded as default by ADR-024)
- Obsidian: `docs/obsidian/Vision Layer.md`, `docs/obsidian/Input Plan.md`,
  `docs/obsidian/00 - Project Overview.md`
- Task files: `docs/tasks/automated_mapping_pipeline/T20.0` … `T20.11`

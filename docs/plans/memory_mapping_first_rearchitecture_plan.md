# Memory-Mapping-First Re-Architecture Plan

## Status

Proposed — awaiting approval. Created 2026-06-18.

## Objective

Replace the pixel/CV-primary extraction mechanism with the proven, industry-standard
**declarative memory-mapping** model used by the RL and retro-achievement ecosystems
(gym-retro / stable-retro, RetroAchievements, BizHawk), so that GNG produces **one
verified, clean, player-only abstract mechanics artifact from real data** — closing the
clean-room loop end-to-end once — and so that onboarding any future MAME title is
*configuration*, not bespoke CV engineering (the ADR-005 scaling goal).

The clean-room public boundary is **unchanged**: only abstract numbers cross it
(ADR-001/003/006), private evidence stays gitignored, and asset recipes keep their
originality contract (ADR-007/008). This plan changes only *how the framework measures
internally*, not what it publishes.

## Diagnosis (why the current path stalls)

- The framework re-derives, from rendered pixels, signals the emulator already knows
  deterministically. This forced a long tail of per-entity CV patches (ADR-012, 013, 019,
  020, 021, 022).
- The committed trace (`specs/traces/gng_trace.json`) is degenerate: 6972 unique entities,
  only 1 with a lifespan > 1 frame; 6978 `spawn` vs 6977 `die` (everything is born and
  dies in the same frame). Only the player track is usable.
- Every `automated_mapping_pipeline_plan.md` (T20.x) task is "code complete" but ends in
  "operator step pending": the pipeline has **never been run end-to-end against real MAME**.
  The execution environment does not exist on the current machine (no venv, no MAME, no
  ffmpeg, no `.env`, no Python 3.11, empty `evidence/private/`).
- Root cause is a process pattern, not a single bug: "Done" has meant *code committed +
  docs propagated*, never *real artifact verified*. Work advances in breadth, never in a
  verified vertical slice.

## Prior-Art Basis (the better design)

Observing an emulated game and extracting structured state at scale is a **solved problem**,
and none of the proven solutions use computer vision:

- **gym-retro / stable-retro** (~1000 integrated games): a declarative per-game bundle —
  `data.json` (variable → `{address, type}` with typed descriptors), `scenario.json`
  (events/reward/done derived from *operations* over variable deltas), per-level
  **savestates**, and a `rom.sha` ROM binding. Plus an **Integration UI** that *finds*
  addresses by watching value changes during play.
- **RetroAchievements / rcheevos** (tens of thousands of community memory maps): the
  **Memory Inspector** finds addresses with no ROM disassembly — reset → filter
  `!= last value` / `< last` / `> last` → narrow → verify by poking the value — plus
  crowdsourced **code notes** for provenance. This is the live proof that ADR-026's memory
  tap is the correct, legally-grounded path (addresses found by *observation*, not
  disassembly).
- **MAME `mamestate` + Lua read/write taps**: per-game driver pattern reading critical
  addresses, with BCD→decimal conversion for arcade scores.
- **BizHawk**: declarative RAM-watch files + savestate-anchored determinism.
- **OpenRA / devilutionX**: confirm the clean-room legal posture this project already keeps
  (spec from community observation, never disassemble; strict engine↔asset separation).

The three pieces this project is missing relative to that model: (1) a typed variable +
scenario schema, (2) a guided address-search tool, (3) a savestate determinism anchor.

## Scope

- Author the re-architecture decision (ADR-028) and re-anchor the workstream around it.
- Stand up a verified execution environment and a deterministic savestate anchor for GNG.
- Build the guided RAM address-search tool (the linchpin that unblocks mapping).
- Define the declarative integration schema (typed variables + scenario + rom.sha + BCD).
- Wire the memory tap to read typed variables → private state timeline.
- Calibrate player physics constants from savestate-anchored isolation experiments (no human
  picker), from RAM.
- Regenerate the PUBLIC **player-only** mechanics spec from real verified data, replacing the
  degenerate trace.
- One RN player-only vertical slice consuming the verified public spec.

## Out of Scope (frozen until the player-only slice is green)

- Enemy / boss / projectile tracking via CV (T10.8, T10.9).
- Optical-flow scroll compensation and tracking-by-detection (T20.7, T20.8; unauthored
  ADR-025).
- VLM-assisted archetype labeling (T20.9; unauthored ADR-027 reservation).
- Multi-game generalization profile (T20.10).
- Original Game Definition phase (T12) and all downstream product work.
- Enemy mechanics of any kind in the public spec (player-only first).

## Task List (topologically ordered)

| ID | Title | Depends on | Reasoning | Effort | Claude model |
|----|-------|-----------|-----------|--------|--------------|
| T30.0a | Create ADR-028 file + Obsidian note (content pre-authored) | — | Low | Low | Sonnet (thinking off) |
| T30.0b | Propagate ADR-028 into the 4 ADR indices (exact rows) | T30.0a | Low | Low | Sonnet (thinking off) |
| T30.0c | Annotate deprecations in `automated_mapping_pipeline_plan.md` | T30.0a | Low | Low | Sonnet (thinking off) |
| T30.1 | Execution environment + GNG savestate anchor; `doctor` + `pytest` green | T30.0a–c | Low | Medium | Sonnet |
| T30.2 | Guided RAM address-search tool (Lua scan + Python TUI; reset/filter/verify-poke) | T30.1 | High | High | Opus |
| T30.3 | Declarative integration schema (typed variables + scenario events + rom.sha + BCD) | T30.0 | Medium | Medium | Opus |
| T30.4 | Memory tap reads typed variables/frame → private state timeline; guardrail extension | T30.2, T30.3 | Medium | Medium | Sonnet |
| T30.5 | Savestate-anchored isolation experiments → player constants from RAM (no picker) | T30.4 | High | Medium | Opus |
| T30.6 | Regenerate PUBLIC player-only mechanics spec from real data; replace degenerate trace | T30.5 | Medium | Low | Sonnet |
| T30.7 | RN player-only vertical slice consuming the verified public spec | T30.6 | Low | Medium | Sonnet |

## Dependency Rationale

- T30.0 is first: this is an architectural pivot (it supersedes the CV-primary path and
  deprecates unauthored ADR-025/027 vision reservations). Per the repo's New Feature
  Documentation Requirements, the decision is recorded before implementation begins.
- T30.1 before everything executable: the environment and a deterministic savestate anchor
  are the real blocker; nothing downstream can be verified without them.
- T30.2 is the linchpin — without guided address discovery, "populate the memory map" is the
  step that stalls. It depends on a working environment + savestate (T30.1).
- T30.3 (schema) depends only on the decision (T30.0) and can proceed in parallel with T30.2.
- T30.4 needs both the discovered addresses (T30.2) and the schema to bind them (T30.3).
- T30.5 calibrates from the typed state timeline (T30.4), anchored to the T30.1 savestate.
- T30.6 publishes only after constants are real and verified (T30.5).
- T30.7 consumes the verified public spec last.

## Definition of Done (workflow correction)

A task in this plan is **not complete** while any "operator step pending" remains. Completion
requires a **real, verified artifact** produced from a real run, not committed code alone.
This is the explicit correction of the pattern that produced the current stalled state.

## Exit Criteria

- ADR-028 recorded (Accepted), with CV ADRs demoted to fallback and the vision-rewrite
  reservations deprecated; indices propagated.
- `cli.py doctor` and the full `pytest` suite pass on a real venv; a private GNG savestate at
  the controllable state exists.
- The guided search tool produces verified player x/y/state addresses for GNG in one session.
- A declarative GNG integration (typed variables + scenario + rom.sha) drives a private state
  timeline with no CV.
- Player physics constants (walk, jump, gravity, projectile) are calibrated from RAM with
  **zero human pickers** and are reproducible.
- A PUBLIC player-only `gng_abstract_mechanics` artifact derived from real data replaces the
  degenerate trace and passes `ensure_no_private_paths`.
- One RN scene runs from the public spec only (no ROM, no private evidence).

## Progress Log

- **2026-06-18** Plan created. T30.0 task file authored. Awaiting approval to execute T30.0.
- **2026-06-18 — explicit recataloging of T30.0.** Original grade: Reasoning **High**,
  Effort **Low**, model **Opus (thinking On)**. New grade: split into T30.0a/b/c, each
  Reasoning **Low**, Effort **Low**, model **Sonnet (thinking Off)**.
  **Justification (what changed):** the judgement-bearing content (ADR-028 decision prose,
  Obsidian note, exact index rows, exact deprecation annotations) was authored at planning time
  and embedded verbatim in the subtask files. Execution is now transcription + exact `old`→`new`
  edits with no synthesis and a small per-run blast radius, which is the definition of a Low
  reasoning, mechanical task. The architectural reasoning did not disappear — it moved upstream
  into the plan, so the *executor's* reasoning load is genuinely Low.

## Reference Documents

- This plan: `docs/plans/memory_mapping_first_rearchitecture_plan.md`
- Superseded/parent context: `docs/plans/automated_mapping_pipeline_plan.md`,
  `docs/plans/gng_source_integration_plan.md`
- `README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/playbooks/AGENT_WORKFLOW_GUIDE.md`
- Governing ADRs: ADR-001, ADR-003, ADR-005, ADR-006, ADR-007, ADR-008, ADR-023, ADR-024,
  ADR-026 (kept/extended); ADR-012, ADR-013, ADR-019, ADR-020, ADR-021, ADR-022 (demoted to
  fallback by ADR-028)
- Obsidian: `docs/obsidian/00 - Project Overview.md`, `docs/obsidian/Vision Layer.md`,
  `docs/obsidian/Input Plan.md`, `docs/obsidian/Guardrails.md`
- Task files: `docs/tasks/memory_mapping_first/T30.0` … `T30.7`
</content>
</invoke>

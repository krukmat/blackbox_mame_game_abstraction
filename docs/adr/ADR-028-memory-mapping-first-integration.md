# ADR-028 — Memory-Mapping-First Game Integration

## Status

**Accepted** — 2026-06-18. The memory tap (ADR-026) is promoted to the **default**
position/state source; the CV stack (ADR-012, ADR-013, ADR-021, ADR-022) and calibration
pickers (ADR-019, ADR-020) are demoted to fallback; the unauthored vision-rewrite reservations
(ADR-025 optical-flow, ADR-027 VLM) and tasks T20.7–T20.10 in
`docs/plans/automated_mapping_pipeline_plan.md` are Deprecated/Superseded.

## Date

2026-06-18

## Context

The mapping pipeline reconstructs quantitative gameplay facts (position, velocity, entity
identity, state) from rendered pixels: MAME → AVI → ffmpeg PNG → OpenCV frame diffs. This
forced a long tail of per-entity CV patches (ADR-012 signatures, ADR-013 MOG2, ADR-021 entity
tracking, ADR-022 scroll reset) plus a human-picker apparatus for every physics constant
(ADR-019, ADR-020). It is neither robust nor scalable. The committed trace
(`specs/traces/gng_trace.json`) is degenerate: 6972 unique entities, only 1 with a lifespan
> 1 frame; 6978 `spawn` vs 6977 `die` (entities born and dead in the same frame). Only the
player track is usable. No real end-to-end capture has ever been verified; every T20.x task is
"code complete, operator step pending".

Observing an emulated game and extracting structured state at scale is a solved problem, and
none of the proven solutions use computer vision:

- **gym-retro / stable-retro** (~1000 integrated games): a declarative per-game bundle —
  typed RAM variables (`data.json`: `{address, type}`), a scenario layer deriving
  events/reward/done from operations over variables (`scenario.json`), per-level savestates,
  and a `rom.sha` ROM binding; plus an Integration UI that finds addresses by watching value
  changes during play.
- **RetroAchievements / rcheevos** (tens of thousands of community memory maps): a Memory
  Inspector that finds addresses with no ROM disassembly (reset → filter `!=`/`<`/`>` last
  value → narrow → verify by poke) plus crowdsourced code notes for provenance.
- **MAME `mamestate` + Lua read/write taps**: a per-game driver reading critical addresses,
  with BCD→decimal conversion for arcade scores.
- **BizHawk**: declarative RAM-watch files + savestate-anchored determinism.
- **OpenRA / devilutionX**: confirm this project's clean-room legal posture (spec from
  community observation, never disassemble; engine↔asset separation).

ADR-026 already Accepted RAM observation as a private measurement/verification accelerator.
This ADR promotes it from accelerator to the **default** positional/state source and adopts
the surrounding declarative-integration + guided-search + savestate-anchor design that makes
the memory approach robust and game-agnostic — the architecture ADR-026 enabled but did not
itself specify.

## Decision

1. The MAME Lua memory tap (within ADR-026 clauses 1–5) is the **default** source of entity
   position and state. The CV pipeline (ADR-012/013/021/022) is retained only as optional
   fallback (no address config available) and as a cross-check.
2. Per-game observation is defined by a **declarative integration bundle** (schema authored in
   T30.3), modeled on gym-retro:
   - typed variables: `{address, type}` with gym-retro-style descriptors
     (endianness/format/bytes, including BCD `d`/`n`);
   - a scenario layer: game-state events (death, hit, score, level-complete) derived from
     operations over variable deltas (`delta`/`absolute`, `nonzero`/`equal`+`reference`);
   - a `rom.sha` binding tying the integration to an exact ROM;
   - a savestate anchor capturing the controllable state for deterministic, boot-free runs.
3. Player-input events continue to come from the ground-truth input timeline (ADR-023).
   Game-state events come from the scenario layer. CV event inference is fallback only.
4. Physics constants are calibrated from savestate-anchored isolation experiments (ADR-024)
   over the typed RAM state timeline. ADR-019 human pickers and ADR-020 pixel projectile
   calibration are fallback only.
5. Address discovery uses a guided in-emulator search tool (T30.2): reset → filter by value
   change → verify by poke. Addresses are community-method observational facts (ADR-026
   clause 1), never ROM-disassembled. Discovered addresses and raw values stay private
   (ADR-026 clauses 2–3).
6. The public boundary is unchanged: only abstract numbers cross it; `guardrails.py` and
   ADR-001/003/006 apply unchanged (extended for addresses/raw values per ADR-026).
7. ADR-026 clause-4 invariant restated: public calibration values must remain explainable as
   observable behavior.

## Consequences

**Positive:** exact, noise-free positional/state truth; eliminates per-entity CV calibration
and per-constant human pickers as the default; onboarding a new MAME title becomes
configuration (a bundle + a short guided-search session) rather than bespoke CV code (the
ADR-005 scaling goal); deterministic, boot-free runs via savestate; resolves the
degenerate-trace failure mode.

**Negative:** requires building the guided-search tool (T30.2) and the bundle schema (T30.3);
shifts provenance discipline onto the search-method audit (must remain observational, never
disassembly); the CV stack becomes maintenance-mode fallback rather than the primary path.

**Scope effects:** tasks T20.7 (optical-flow scroll), T20.8 (tracking-by-detection),
T20.9 (VLM), T20.10 (multi-game profile) and the unauthored reservations ADR-025/ADR-027 are
Deprecated/Superseded by this ADR — their goals (scroll robustness, identity, generalization)
are met by the memory-mapping + bundle design. They may be revisited only as fallback
hardening after the player-only vertical slice is verified.

## Alternatives Considered

1. **Keep CV primary, harden with modern vision (optical-flow + tracking-by-detection).**
   Rejected as default: higher effort, still inferential/noisy, unproven at scale here;
   retained as fallback.
2. **RAM as accelerator only (status quo, ADR-026).** Rejected as insufficient: it left CV as
   the primary source, so the degenerate-trace and non-scaling problems persisted.
3. **RAM as sole truth with no observational explainability.** Rejected: violates ADR-026
   clause 4; abandons the observational identity for published facts.
4. **ROM disassembly to find addresses.** Rejected unconditionally: derives from the protected
   work; breaks clean-room.

## Related

- [ADR-026](./ADR-026-internal-state-observation-boundary.md) — RAM observation boundary
  (promoted here from accelerator to default)
- [ADR-023](./ADR-023-ground-truth-input-timeline.md) — input timeline (player-input event
  source, kept)
- [ADR-024](./ADR-024-designed-experiment-calibration.md) — isolation experiments (calibration
  method, kept; now over RAM state)
- [ADR-001](./ADR-001-clean-room-layered-architecture.md),
  [ADR-003](./ADR-003-public-output-blocklist.md),
  [ADR-006](./ADR-006-vision-layer-numeric-only-output.md) — public boundary (unchanged)
- [ADR-012](./ADR-012-entity-signature-based-player-identification.md),
  [ADR-013](./ADR-013-opencv-vision-backend.md),
  [ADR-021](./ADR-021-enemy-tracking-continuity.md),
  [ADR-022](./ADR-022-scroll-aware-vision-pipeline.md) — CV pipeline (demoted to fallback)
- [ADR-019](./ADR-019-human-validated-calibration-candidates.md),
  [ADR-020](./ADR-020-projectile-in-flight-tracking.md) — pickers (fallback only)
- Deprecated/Superseded: ADR-025 (optical-flow, unauthored), ADR-027 (VLM, unauthored); tasks
  T20.7–T20.10
- `docs/plans/memory_mapping_first_rearchitecture_plan.md` — parent plan
- `docs/plans/automated_mapping_pipeline_plan.md` — superseded context

## Approver decision (recorded)

**Accepted, 2026-06-18.** Memory-mapping-first is the default positional/state source for
the GNG integration. The CV pipeline is demoted to fallback. The declarative integration
bundle (typed variables + scenario + rom.sha + savestate), the guided address-search tool
(T30.2), and savestate-anchored isolation experiments (T30.5) are in scope. ADR-025, ADR-027,
and T20.7–T20.10 are Deprecated. ADR-026 clause 4 remains binding.
</content>

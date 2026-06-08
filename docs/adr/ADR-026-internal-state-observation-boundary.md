# ADR-026 — Internal-State Observation Boundary

## Status

**Accepted** (T20.0, 2026-06-07) — under the constrained contract below, scoped as a private
measurement/verification accelerator. Clause 4 (memory is not the published sole truth) is
binding: public values must remain explainable as observable behavior. This unblocks T20.5
and T20.6.

## Date

2026-06-07

## Context

The mapping pipeline currently reconstructs every quantitative fact about gameplay
(positions, velocities, entity identity) from the **rendered pixel output**: MAME records an
AVI, ffmpeg extracts PNG frames, and the OpenCV vision layer infers motion from frame diffs.
This choice produced a long tail of manual, fragile machinery — per-entity hand-calibrated
signatures (ADR-012, ADR-021), MOG2 scroll-reset handling (ADR-022), and a human-validated
candidate-picker workflow for every physics constant (ADR-019). Pure automation from pixels
yielded physically inconsistent constants (ADR-019 records a `t_peak` prediction off by ~40×).

MAME exposes the full emulated machine state to the Lua bridge that the project already uses
to inject inputs (`scripts/mame_autoboot.lua`). Reading a few RAM addresses each frame
(`manager.machine.devices[":maincpu"].spaces["program"]:read_u8/u16(addr)`) would yield
**exact, noise-free** entity position and state with no computer vision at all. Address maps
for arcade titles are widely published in **community cheat databases** (MAME cheat XML, cheat
collections) that are authored by the community and are *not* derived from disassembling the
protected ROM in this repository.

This ADR exists because that capability directly contradicts a stance the project has already
taken informally. **ADR-022 explicitly rejected "ROM-state scroll address inspection via MAME
Lua"** with the rationale: *"the project policy is observational, not introspective. Reading
internal state bypasses the abstraction layer that the whole framework is designed to
maintain."* ADR-026 revisits and formalizes that stance as a deliberate, documented decision
rather than an aside in a vision ADR.

The `automated_mapping_pipeline_plan.md` re-architecture cannot proceed on its memory-tap
tasks (T20.5, T20.6) until this boundary is settled, because the decision reshapes the rest of
the plan (it determines whether modern vision is the primary positional source or optional
hardening).

## The two clean-room arguments

### Argument FOR (RAM reading is clean-room-safe)

1. **What is published does not change.** Clean-room here constrains the *public boundary*:
   only abstract numbers cross (ADR-001, ADR-003, ADR-006). RAM values are numeric behavioral
   facts (an x-coordinate, a state flag). They are not expressive content (no sprite, palette,
   audio, or character identity). Facts are not copyrightable.
2. **Addresses are community facts, not ROM derivations.** Using a cited community cheat-DB
   address is equivalent to reading public documentation about the machine, not disassembling
   the protected work. The repository never disassembles its ROM.
3. **Legal precedent permits intermediate observation.** Clean-room reverse engineering
   doctrine (e.g., Sega v. Accolade, Sony v. Connectix) treats intermediate copying/observation
   for idea-and-function extraction as fair use, provided the *output* carries no protected
   expression. Reading RAM is a stronger-isolated version of what the project already does by
   reading the screen.
4. **It removes the dominant source of manual labor and error.** Exact state eliminates the
   per-entity signature calibration, the scroll-reset hacks, and the per-constant human
   pickers — the very machinery that ADR-019 admits "reduces but does not eliminate" manual
   per-topic engineering, and that does not scale across games (ADR-005 goal).

### Argument AGAINST (RAM reading erodes the project's posture)

1. **It breaks the stated identity.** The framework is defined as *observational, not
   introspective* (ADR-022). "Observe behavior like a player sees it" is the conceptual spine;
   reading RAM is seeing what a player cannot.
2. **It widens the access footprint.** The purest two-team clean-room posture minimizes how
   much of the original system the abstraction layer touches. Reaching into memory increases
   that surface even if the published output is identical.
3. **Provenance discipline becomes load-bearing.** The safety of the FOR argument depends
   entirely on addresses being genuinely community-sourced and never ROM-disassembled. That is
   a process guarantee that must be enforced and audited, not assumed.
4. **The benefit may be obtainable without it.** Levels 0 and 1 of the plan (ground-truth
   input join + designed isolation experiments) already remove most manual labor *without*
   crossing this line. Modern vision (Level 2) can fix identity/scroll observationally. RAM
   reading may be convenience, not necessity.

## Decision (proposed contract if Accepted)

If the approver Accepts, internal-state observation is permitted **only** under this contract:

1. **Source restriction.** RAM addresses come exclusively from cited community cheat
   databases, stored in a **local/private, uncommitted** config. ROM disassembly to discover
   addresses is prohibited.
2. **Private-only raw layer.** Raw addresses and raw read values are private artifacts under
   `evidence/private/` (gitignored). They never appear in any public artifact, in stdout, or
   in committed config.
3. **Numbers-only public output, unchanged.** Only derived abstract numbers reach public
   specs, exactly as today. Guardrails (`guardrails.py`, ADR-003/006) apply unchanged and are
   extended to reject addresses and raw memory values.
4. **Memory is a measurement/verification source, not the sole truth.** Public calibration
   values must remain explainable as observable behavior. The memory tap is used to measure
   and to cross-check the observational pipeline (T20.6), not to publish facts that could only
   be obtained by introspection.
5. **Graceful absence.** With no address config present, the pipeline falls back to the
   observational path with no loss of correctness — only of convenience.

If the approver Rejects, the memory-tap tasks (T20.5, T20.6) are removed from the plan and the
observational modern-vision path (T20.7, T20.8) becomes the primary positional source. ADR-022's
informal rejection stands as the formal, ADR-level policy.

## Recommendation

**Accept under the constrained contract above, scoped as a measurement/verification
accelerator — not as the published source of truth.** Rationale: the public boundary and the
project's defensibility are governed by what crosses (numbers only), which is unchanged; the
constraint in clause 4 preserves the observational *identity* for the published artifacts while
clauses 1–3 keep the legal footprint minimal and auditable. This captures the automation/
accuracy upside (especially as a cross-check that finally closes the ADR-019 `t_peak` failure
mode) without abandoning the observational spine for anything that is actually published.

If the project prioritizes posture purity over automation, Reject is fully defensible — Levels
0–2 already deliver most of the automation gain without crossing the line.

**This recommendation is advisory. The Accepted/Rejected decision is the approver's and must be
recorded here before T20.5 may begin.**

### Approver decision (recorded)

**Accepted under the constrained contract (clauses 1–5), 2026-06-07.** RAM observation is
permitted only as a private measurement/verification accelerator and cross-check. Clause 4 is
binding: the memory tap must not become the published source of truth — public calibration
values must remain explainable as observable behavior. T20.5 and T20.6 are in scope; the
observational modern-vision path (T20.7/T20.8) remains valuable hardening rather than the sole
positional source.

## Consequences

**If Accepted**

- Positive: exact positional/state truth; eliminates per-entity CV calibration and per-constant
  human pickers as the *default*; provides an authoritative cross-check that resolves the
  ADR-019 inconsistency class; scales cleanly across games via per-game address configs.
- Negative: introduces a provenance-discipline obligation (clause 1) that must be audited;
  shifts the project from a purely observational stance to a constrained-introspective one;
  requires guardrail extensions for addresses/raw values.

**If Rejected**

- Positive: the observational identity is preserved without exception; no new provenance
  surface to audit.
- Negative: noise-reduction and identity must come entirely from modern vision (T20.7/T20.8),
  which is higher effort; some constants may still require ADR-019 human fallback.

## Alternatives Considered

1. **Status quo (pixels only).** Rejected as the default because it is the documented source of
   the manual-labor and inconsistency problems this re-architecture targets. (It remains the
   fallback under either decision.)
2. **Read RAM with no constraints (memory as sole truth).** Rejected: would let introspection-
   only facts drive public output, abandoning the observational identity entirely and maximizing
   the access footprint.
3. **Discover addresses by disassembling the ROM.** Rejected unconditionally: directly derives
   from the protected work and breaks the clean-room premise regardless of the decision here.
4. **MAME `-record`/`.inp` only (no RAM).** Useful and already partly adopted for inputs (see
   ADR-023), but `.inp` carries inputs, not entity state, so it does not provide positions. Not
   a substitute for this decision; complementary.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md) — structural-not-advisory enforcement
- [ADR-003](./ADR-003-public-output-blocklist.md) — public output blocklist (extended if Accepted)
- [ADR-006](./ADR-006-vision-layer-numeric-only-output.md) — numeric-only output the contract preserves
- [ADR-019](./ADR-019-human-validated-calibration-candidates.md) — manual pattern this would reduce
- [ADR-022](./ADR-022-scroll-aware-vision-pipeline.md) — informal rejection this ADR formalizes/revisits
- [ADR-023](./ADR-023-ground-truth-input-timeline.md) — complementary input-truth source (T20.1)
- `docs/plans/automated_mapping_pipeline_plan.md` — parent plan (decision gate)
- `docs/tasks/automated_mapping_pipeline/T20.0-internal-state-observation-decision.md` — this task
- `docs/tasks/automated_mapping_pipeline/T20.5-lua-memory-tap.md` — implementation gated by this ADR
- `apps/mame-harness/guardrails.py` — guardrails extended if Accepted

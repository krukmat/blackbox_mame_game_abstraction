# ADR-019 — Human-Validated Calibration Candidates Pattern

## Status
Accepted

## Date
2026-05-23

## Context

Several calibration tasks in this repository require inferring numeric constants from observed gameplay traces. Examples already in scope or anticipated:

- physics calibration (jump velocity, gravity, locomotion speed, projectile speed)
- boot calibration (per ADR-018 — semantic phase markers)
- per-entity behavioral timing (enemy spawn periods, hit-window durations)

Two extreme approaches have proven unworkable as defaults:

- **Pure automation from the trace** is brittle. Real trace data contains tracker noise (see T10.7 entity-id-collision discovery), spurious detections from sprite swaps, and edge cases that no fixed heuristic catches. Calibration values derived purely from noisy traces produce physically inconsistent constants — verified by the T11.3 outcome where `t_peak` predicted from automated calibration was off by 40× from observed.
- **Pure manual operator workflow** (the operator scrolls thousands of frames and dictates frame numbers) produces correct values once, but the derivation is unauditable, unreproducible, and tribal. Re-calibration months later requires re-acquiring the operator's mental protocol from documentation rather than from executable code.

Per ADR-001, *"enforcement must be structural, not advisory."* That principle applies here: the calibration workflow itself should be codified, not left as a ritual described in `CLAUDE.md`.

Additionally, the repository will need to apply the same calibration pipelines to other games (per ADR-005 source profile pattern). A pattern that scales without growing tribal knowledge per game is required.

## Decision

Adopt a **candidate detection + human validation** pattern for calibration tools that require human judgment on borderline cases. The pattern has three phases with a strict contract between them:

```text
public trace / observation artifact
  -> picker tool (machine)
     -> structured candidate set + per-candidate auto-validation flags
  -> human validation (operator inspects private evidence)
     -> list of accepted candidate IDs
  -> downstream calculator (machine)
     -> calibrated public artifact
```

### Picker tool contract

A picker tool implementing this pattern must:

1. Read only **public artifacts** (e.g., `specs/traces/gng_trace.json`). It must not read raw frames, video, or other private visual content.
2. Apply an explicit, parameterized algorithm to surface candidates. Algorithm parameters (e.g., `min_distance`, `min_prominence`) must be source-visible constants in the tool, not hidden literals.
3. Output a structured candidate table to stdout containing only frame numbers and numeric metadata. Each candidate carries deterministic auto-validation flags (e.g., `flat_ok`, `sym_ok`) computed from the public input.
4. Write a structured candidate artifact to `evidence/private/run_<id>/logs/<picker_name>_candidates.json` for downstream consumption. This file is private (under `evidence/private/`, gitignored).
5. Never emit private paths to stdout. The path convention may be **stated once** as a human-readable reminder (e.g., "open `evidence/private/run_<id>/frames/extracted_png/<NNNN>.png` to verify any candidate"), but individual candidate rows must show frame numbers only.

### Human validation handshake

The operator's role is bounded to **accept/reject decisions on the candidates produced by the picker**. The operator may inspect private evidence (PNGs, video) to inform that decision but does not contribute new frame numbers outside the candidate set.

The handshake protocol:

1. Picker outputs candidates with explicit IDs.
2. Operator responds with one of:
   - `accept N, M, ...` — accept these candidate IDs
   - `reject K — <reason>` — reject specific IDs with a brief note
   - `accept all flat_ok and sym_ok` — bulk acceptance shorthand
3. Agent records accepted IDs and proceeds to the downstream calculator.

### Downstream calculator contract

The downstream calculator (e.g., physics constant aggregator) consumes the picker's `<picker_name>_candidates.json` filtered by the operator's accepted IDs, computes the calibrated values, and writes a **public** artifact (e.g., `specs/calibration/<topic>_calibration.yaml`).

The calculator must:

1. Validate that every accepted candidate ID exists in the picker output. Fail explicitly if not.
2. Apply numeric aggregation (median, mean, regression) per its task definition.
3. Write only public artifacts. Private candidate references must not leak into the public output.

### Tool location

All picker tools live in `apps/mame-harness/`, alongside `physics_calibrator.py` and `boot_calibration.py`. Per ADR-001, this is the orchestration layer for the public-side calibration pipeline.

## Consequences

**Positive**

- The calibration workflow is encoded as executable structure rather than documented ritual. New contributors and agents discover the workflow by reading the picker source, not by reading prose.
- Validation flags (auto-pass / auto-fail per candidate) bound the operator's cognitive load to the borderline cases.
- Path discipline is preserved: pickers operate on public traces and emit only frame-number metadata to stdout. Candidate JSONs are private artifacts under `evidence/private/`, gitignored.
- The pattern scales across calibration topics and across games (per ADR-005). Each new picker shares the same handshake and the same downstream calculator contract.
- Recalibration is reproducible: the same trace + same picker parameters yield the same candidates; only the human acceptance set varies.

**Negative**

- Each new calibration topic requires a new picker implementation. The pattern reduces but does not eliminate per-topic engineering.
- The interactive validation step requires synchronous operator availability. Fully autonomous re-calibration in CI is out of scope for this pattern.
- The pattern depends on a public trace existing for the topic being calibrated. New calibrations on topics without trace coverage require trace extensions first.

## Future Scaling — Anticipated Picker Instances

This pattern is intended to be applied to multiple calibration topics, not only the first one (jump physics). The current and anticipated picker instances:

| Picker tool | Topic | Detection algorithm | Status |
|-------------|-------|---------------------|--------|
| `visual_jump_picker.py` | Jump physics (`jumpVelocity_y`, `gravity_y`) | Local minima in player y(t) — peak finder | First instance (T10.7.A) |
| `visual_locomotion_picker.py` | Walking speed (`locomotion_velocity_x`) | Runs of consecutive `walking_*` states with stable vx | Anticipated |
| `visual_projectile_picker.py` | Projectile speed (`projectile_velocity_x`) | Trajectories where `entity_type=projectile` shows sustained linear motion | Anticipated |

### Rule of three for shared base extraction

To avoid premature abstraction, do **not** extract a shared `CalibrationPickerBase` class until the third picker instance is being implemented. Until then, each picker is a standalone module of ~150 lines. The third implementation reveals the genuine commonalities; the abstraction extracted at that point is grounded in three concrete instances rather than guessed from one.

### Common contract every picker must satisfy

Independent of the specific detection algorithm, every picker conforming to this ADR must:

1. CLI signature: `python <picker>.py <run_id> [--trace <path>]`
2. Reads only public artifacts (default `specs/traces/gng_trace.json`)
3. Writes structured candidates to `evidence/private/run_<id>/logs/<picker_name>_candidates.json`
4. Stdout shows frame numbers + numeric metadata only — no private paths
5. Algorithm parameters declared as source-visible module constants (uppercase top-level)
6. Per-candidate auto-validation flags computed deterministically from public input
7. Unit tests cover at least: positive detection, negative-filter rejection, output-contract compliance (no private paths in stdout)

When the third picker exists, refactor common scaffolding into `apps/mame-harness/calibration_picker_base.py` and update this ADR with the resulting base contract.

## Alternatives Considered

**Pure automation from trace**

Rejected because trace noise produces incorrect calibration values. Verified by T11.3 outcome: automated calibration of jump physics yielded `t_peak ≈ 0.36 frames` against an observed `≈ 16 frames`.

**Pure manual operator workflow**

Rejected because the workflow becomes tribal knowledge. Re-calibration loses the protocol; agents handed off the task replay the same mistakes.

**Full GUI calibration tool**

Rejected for the first implementation because it requires UI dependencies (Electron, Qt, web frontend) and a separate UX surface. The agent/operator dialog within the existing CLI/IDE workflow is sufficient. A GUI may be added later as an optional front-end over the same picker contract if the volume of calibration work grows.

**Picker writes public candidate JSON instead of private**

Rejected because the picker's candidate list references run-specific frame numbers, which are meaningful only in the context of a private evidence run. Promoting the candidates to a public artifact would inflate the public surface without consumer demand.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md) — structural-not-advisory principle this pattern extends
- [ADR-002](./ADR-002-private-evidence-uri-scheme.md) — private artifact location convention
- [ADR-003](./ADR-003-public-output-blocklist.md) — what must not leak to public
- [ADR-005](./ADR-005-source-profile-driver-contract.md) — the source-profile pattern this scales across
- [ADR-006](./ADR-006-vision-layer-numeric-only-output.md) — the public-trace foundation pickers consume
- [ADR-007](./ADR-007-asset-recipe-originality-contract.md) — human-in-loop validation precedent
- [ADR-018](./ADR-018-boot-calibration-public-contract.md) — sibling calibration pattern with different topic
- [docs/plans/T10.7.A-visual-calibration-pivot.md](../plans/T10.7.A-visual-calibration-pivot.md) — first invocation
- [docs/tasks/gng_source_integration/T10.7.A-visual-calibration.md](../tasks/gng_source_integration/T10.7.A-visual-calibration.md) — first task
- `apps/mame-harness/visual_jump_picker.py` — first implementation (T10.7.A ST.A3a)
- `apps/mame-harness/physics_calibrator.py` — downstream calculator

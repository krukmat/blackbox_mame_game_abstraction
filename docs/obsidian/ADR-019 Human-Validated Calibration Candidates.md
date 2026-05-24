# ADR-019 — Human-Validated Calibration Candidates

tags: #adr #calibration #human-in-the-loop #clean-room #pattern

Source: `docs/adr/ADR-019-human-validated-calibration-candidates.md`
Plan: `docs/plans/T10.7.A-visual-calibration-pivot.md`

## Decision

Calibration tools that need operator judgment follow a three-phase pattern with a strict contract between phases:

```text
public trace
  -> picker tool (machine) — surfaces candidates with auto-validation flags
  -> human validation       — accept/reject IDs based on private evidence
  -> downstream calculator  — computes calibrated public artifact
```

## Rules

- Pickers read public artifacts only (trace JSON); never raw frames or video.
- Picker stdout shows frame numbers and numeric metadata. No private paths.
- Picker writes structured candidates to `evidence/private/run_<id>/logs/<picker_name>_candidates.json` (private, gitignored).
- Algorithm parameters (e.g. `min_distance`, `min_prominence`) are explicit source constants.
- Operator role bounded to accept/reject decisions on the picker's candidates.
- Downstream calculator writes public artifacts; private candidate references must not leak.
- All picker tools live in `apps/mame-harness/`.

## Why

Per [[ADR-001 Clean-Room Layered Architecture]]: enforcement must be structural, not advisory. Pure-automation calibration is brittle (trace noise); pure-manual calibration is tribal. The codified handshake makes the workflow reproducible across recalibrations and replicable across games (per [[ADR-005 Source Profile Driver Contract]]).

## Related

- [[ADR-001 Clean-Room Layered Architecture]] — structural principle extended
- [[ADR-002 Private URI Scheme]] — candidate JSON private location
- [[ADR-003 Public Output Blocklist]] — what must not leak
- [[ADR-005 Source Profile Driver Contract]] — pattern scales across games
- [[ADR-006 Vision Numeric Only]] — public trace foundation
- [[ADR-007 Asset Recipe Originality]] — human-in-loop precedent
- [[ADR-018 Boot Calibration Public Contract]] — sibling calibration pattern

# ADR-020 — Projectile In-Flight Tracking

tags: #adr #vision #calibration #projectile

Source: `docs/adr/ADR-020-projectile-in-flight-tracking.md`
Task: `docs/tasks/gng_source_integration/T10.7.E-projectile-in-flight-tracking.md`

## Decision

Stop treating player-motion surrogates as calibrated projectile velocity. Public `projectile_velocity_x` must come from real in-flight projectile motion tracked across frames.

## Why

Two different surrogate values exist in public artifacts today:

- calibration YAML: `0.1871/s`
- mechanics YAML: `8.5348/s`

Neither measures projectile motion. Both sample player velocity at fire events. That breaks traceability and makes the calibration surface look more real than it is.

## Pattern

1. Link projectile-sized regions across adjacent frames into short trajectories
2. Run an ADR-019 picker over those trajectories
3. Have the operator accept/reject real in-flight candidates
4. Compute `projectile_velocity_x` from accepted x-displacement data

## Scope Boundary

- This is a calibration-oriented tracker first, not a generic entity continuity framework
- The minimum output is stable temporary trajectory IDs plus per-frame x positions
- Human validation remains mandatory

## Related

- [[ADR-013 OpenCV Vision Backend]]
- [[ADR-019 Human-Validated Calibration Candidates]]
- [[Vision Layer]]

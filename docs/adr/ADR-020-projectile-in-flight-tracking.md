# ADR-020 — Cross-Frame Projectile Continuity for In-Flight Velocity Calibration

## Status
Accepted

## Date
2026-05-23

## Context

`projectile_velocity_x` is currently inconsistent across public artifacts and does not reflect a real projectile measurement:

- `specs/calibration/gng_physics_calibration.yaml` stores `0.1871/s`
- `specs/mechanics/gng_abstract_mechanics.yaml` stores `8.5348/s`

Both values come from the same surrogate method: player velocity sampled at fire events. Neither value tracks a projectile blob across frames, so neither measures projectile motion.

That surrogate was tolerable only as a temporary placeholder. It is no longer acceptable for this project state because:

1. The constant is presented as calibrated public mechanics data.
2. T10.7 introduced a calibration workflow that explicitly distinguishes machine inference from human-validated observation (ADR-019).
3. Accepting a non-physical surrogate in a public mechanics artifact weakens traceability and makes downstream RN tuning appear more grounded than it is.

The current vision layer emits per-frame projectile candidates but does not preserve projectile identity across frames. ADR-013 already documents this as a Known Gap for enemies; the same structural gap applies to projectiles.

## Decision

Introduce a dedicated projectile continuity pattern for calibration work before accepting any public `projectile_velocity_x` value as calibrated.

The pattern has three parts:

### 1. Cross-frame projectile identity in the vision/calibration path

Add a narrowly scoped projectile tracker that links projectile-sized motion regions across adjacent frames into short-lived trajectories.

This tracker is not a generic multi-entity continuity framework. It is a calibration-oriented component whose minimum responsibility is:

- identify candidate projectile regions in consecutive frames
- assign a stable temporary `trajectory_id`
- record per-frame x positions for each accepted trajectory

The tracker may live in the orchestration/calibration path first, without widening the public trace schema immediately.

### 2. ADR-019 picker handshake remains mandatory

Even with cross-frame linking, projectile calibration still requires the human-validated picker pattern from ADR-019:

```text
public trace / numeric candidate stream
  -> projectile picker
  -> operator accept/reject of trajectories
  -> calculator
  -> public calibration artifact
```

The operator validates that a candidate trajectory is a real in-flight projectile segment rather than noise, overlap, or partial occlusion.

### 3. Public calibration value must come from real projectile motion

`projectile_velocity_x` may be written or updated in public artifacts only from accepted trajectory measurements derived from projectile x displacement across frames.

Player-motion surrogates are no longer valid as calibrated output once this ADR is adopted.

## Consequences

**Positive**

- The public mechanics constant regains physical meaning and traceability.
- Calibration semantics become consistent across jump, locomotion, and projectile work: every value corresponds to the observed entity, not a proxy.
- The repository stops presenting surrogate projectile data as if it were measured reality.

**Negative**

- T11.4 remains blocked by incomplete projectile calibration until this work is done or the dependency is explicitly relaxed in a later task.
- A new tracker/picker/calculator slice must be implemented and tested.
- Projectile blobs are small and fast; matching across frames will be less stable than player tracking and will likely need tighter heuristics.

## Alternatives Considered

**Keep the surrogate and document it better**

Rejected. Better labeling does not change the fact that the value is not measuring the thing it claims to measure.

**Remove `projectile_velocity_x` from public artifacts entirely**

Rejected for now. The mechanics surface expects a projectile field, and removing it would create a broader schema and consumer change than this decision requires.

**Build a generic continuity system for all entity classes first**

Rejected as premature. The immediate need is projectile calibration. A calibration-scoped tracker is a smaller and more defensible first step.

## Related

- [ADR-013](./ADR-013-opencv-vision-backend.md)
- [ADR-019](./ADR-019-human-validated-calibration-candidates.md)
- [docs/tasks/gng_source_integration/T10.7.D-projectile-velocity-decision.md](../tasks/gng_source_integration/T10.7.D-projectile-velocity-decision.md)
- [docs/tasks/gng_source_integration/T10.7.E-projectile-in-flight-tracking.md](../tasks/gng_source_integration/T10.7.E-projectile-in-flight-tracking.md)

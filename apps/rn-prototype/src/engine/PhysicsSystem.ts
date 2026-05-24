import type { EntityState } from "../entities/Entity.js";
import type { InputState } from "../input/InputState.js";

export interface PhysicsConfig {
  gravity: number;
  moveSpeed: number;
  jumpVelocity: number;
}

// T10.7.A / T10.7.C — values from human-validated calibration candidates (ADR-019).
// Source: specs/calibration/gng_physics_calibration.yaml.
// Coordinates: normalized (0–1 per screen dimension) per second.
// Jump: run_t10_7_jumps, kinematic gate PASS. Locomotion: run_t10_7_walk,
// walk candidates IDs 3, 5, 8, 10 accepted by operator review.
export const CALIBRATED_PHYSICS_CONFIG: PhysicsConfig = {
  gravity: 0.1167,      // normalized/s²  (n=2, human_validated_kinematic)
  moveSpeed: 0.2786,    // normalized/s   (n=24, human_validated_walk_segment)
  jumpVelocity: 0.4668, // normalized/s   (n=2, human_validated_kinematic, |measured_vy|)
};

export class PhysicsSystem {
  constructor(private readonly config: PhysicsConfig) {}

  public step(entity: EntityState, input: InputState, deltaSeconds: number): EntityState {
    const horizontal = input.left ? -1 : input.right ? 1 : 0;
    let nextVelocityY = entity.velocity.y - this.config.gravity * deltaSeconds;
    if (input.jump && entity.grounded) {
      nextVelocityY = this.config.jumpVelocity;
    }

    const nextY = Math.max(0, entity.position.y + nextVelocityY * deltaSeconds);
    const grounded = nextY === 0;
    if (grounded) {
      nextVelocityY = 0;
    }

    return {
      ...entity,
      position: {
        x: entity.position.x + horizontal * this.config.moveSpeed * deltaSeconds,
        y: nextY
      },
      velocity: {
        x: horizontal * this.config.moveSpeed,
        y: nextVelocityY
      },
      grounded
    };
  }
}

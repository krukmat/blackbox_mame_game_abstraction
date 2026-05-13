import type { EntityState } from "../entities/Entity.js";
import type { InputState } from "../input/InputState.js";

export interface PhysicsConfig {
  gravity: number;
  moveSpeed: number;
  jumpVelocity: number;
}

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

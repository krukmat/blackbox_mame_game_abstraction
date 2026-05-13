import type { EntityState } from "../entities/Entity.js";

export interface CollisionResult {
  collided: boolean;
  pair: [string, string] | null;
}

export class CollisionSystem {
  public collide(a: EntityState, b: EntityState): CollisionResult {
    const overlapX = Math.abs(a.position.x - b.position.x) * 2 < a.size.x + b.size.x;
    const overlapY = Math.abs(a.position.y - b.position.y) * 2 < a.size.y + b.size.y;
    return {
      collided: overlapX && overlapY,
      pair: overlapX && overlapY ? [a.id, b.id] : null
    };
  }
}

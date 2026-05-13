import type { EntityState } from "./Entity.js";

export function createEnemy(): EntityState {
  return {
    id: "enemy_patrol",
    kind: "enemy",
    position: { x: 4, y: 0 },
    velocity: { x: -1, y: 0 },
    size: { x: 1, y: 2 },
    grounded: true,
    active: true
  };
}

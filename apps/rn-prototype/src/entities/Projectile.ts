import type { EntityState } from "./Entity.js";

export function createProjectile(): EntityState {
  return {
    id: "projectile_001",
    kind: "projectile",
    position: { x: 0, y: 0 },
    velocity: { x: 4, y: 0 },
    size: { x: 0.5, y: 0.5 },
    grounded: false,
    active: false
  };
}

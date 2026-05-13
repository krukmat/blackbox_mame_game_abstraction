import type { EntityState } from "./Entity.js";

export function createPickup(): EntityState {
  return {
    id: "pickup_001",
    kind: "pickup",
    position: { x: 2, y: 0 },
    velocity: { x: 0, y: 0 },
    size: { x: 0.75, y: 0.75 },
    grounded: true,
    active: true
  };
}

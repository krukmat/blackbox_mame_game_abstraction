import type { EntityState } from "./Entity.js";

export function createHazard(): EntityState {
  return {
    id: "hazard_001",
    kind: "hazard",
    position: { x: 6, y: 0 },
    velocity: { x: 0, y: 0 },
    size: { x: 1, y: 1 },
    grounded: true,
    active: true
  };
}

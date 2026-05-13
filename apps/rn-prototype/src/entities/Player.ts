import type { EntityState } from "./Entity.js";

export function createPlayer(): EntityState {
  return {
    id: "player",
    kind: "player",
    position: { x: 0, y: 0 },
    velocity: { x: 0, y: 0 },
    size: { x: 1, y: 2 },
    grounded: true,
    active: true
  };
}

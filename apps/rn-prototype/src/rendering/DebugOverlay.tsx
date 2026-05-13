import type { EntityState } from "../entities/Entity.js";

export function buildDebugOverlay(entities: EntityState[]): string[] {
  return entities.map(
    (entity) =>
      `${entity.id}:${entity.kind}@(${entity.position.x.toFixed(2)},${entity.position.y.toFixed(2)})`
  );
}

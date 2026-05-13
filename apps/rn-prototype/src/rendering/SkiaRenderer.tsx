import type { EntityState } from "../entities/Entity.js";
import type { CameraFrame } from "./Camera.js";

export interface RenderShape {
  id: string;
  kind: EntityState["kind"];
  x: number;
  y: number;
  width: number;
  height: number;
}

export class SkiaRenderer {
  public buildShapes(entities: EntityState[], camera: CameraFrame): RenderShape[] {
    return entities
      .filter((entity) => entity.active)
      .map((entity) => ({
        id: entity.id,
        kind: entity.kind,
        x: entity.position.x - camera.x,
        y: entity.position.y - camera.y,
        width: entity.size.x,
        height: entity.size.y
      }));
  }
}

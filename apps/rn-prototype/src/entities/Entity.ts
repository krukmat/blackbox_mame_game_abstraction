export type EntityKind = "player" | "enemy" | "projectile" | "pickup" | "hazard";

export interface Vector2 {
  x: number;
  y: number;
}

export interface EntityState {
  id: string;
  kind: EntityKind;
  position: Vector2;
  velocity: Vector2;
  size: Vector2;
  grounded: boolean;
  active: boolean;
}

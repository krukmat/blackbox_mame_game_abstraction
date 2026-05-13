import { createEnemy } from "../entities/Enemy.js";
import type { EntityState } from "../entities/Entity.js";
import { createHazard } from "../entities/Hazard.js";
import { createPickup } from "../entities/Pickup.js";
import { createPlayer } from "../entities/Player.js";

export interface SceneState {
  entities: EntityState[];
}

export class SceneManager {
  public createPlayableScene(): SceneState {
    return {
      entities: [createPlayer(), createEnemy(), createPickup(), createHazard()]
    };
  }
}

import type { EntityState } from "../entities/Entity.js";
import type { InputState } from "../input/InputState.js";
import { EventBus } from "./EventBus.js";
import { PhysicsSystem } from "./PhysicsSystem.js";
import { TimeStep } from "./TimeStep.js";

export class GameLoop {
  constructor(
    private readonly timeStep: TimeStep,
    private readonly physics: PhysicsSystem,
    private readonly eventBus: EventBus
  ) {}

  public tick(player: EntityState, input: InputState): EntityState {
    const nextPlayer = this.physics.step(player, input, this.timeStep.seconds());
    if (input.jump && player.grounded) {
      this.eventBus.emit("player_jump");
    }
    return nextPlayer;
  }
}

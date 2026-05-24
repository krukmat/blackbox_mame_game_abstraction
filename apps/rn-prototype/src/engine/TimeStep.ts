import type { AbstractMechanics } from "../specs/mechanicsLoader.js";

export class TimeStep {
  constructor(public readonly fixedDeltaMs: number) {}

  public static fromMechanics(mechanics: Pick<AbstractMechanics, "timing">): TimeStep {
    return new TimeStep(mechanics.timing.ms_per_frame);
  }

  public seconds(): number {
    return this.fixedDeltaMs / 1000;
  }
}

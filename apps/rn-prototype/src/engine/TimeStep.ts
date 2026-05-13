export class TimeStep {
  constructor(public readonly fixedDeltaMs: number = 16) {}

  public seconds(): number {
    return this.fixedDeltaMs / 1000;
  }
}

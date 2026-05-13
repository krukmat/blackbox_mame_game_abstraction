import type { InputState } from "./InputState.js";

export class VirtualGamepad {
  private state: InputState = { left: false, right: false, jump: false };

  public press(nextState: Partial<InputState>): void {
    this.state = { ...this.state, ...nextState };
  }

  public snapshot(): InputState {
    return { ...this.state };
  }
}

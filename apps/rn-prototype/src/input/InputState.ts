export interface InputState {
  left: boolean;
  right: boolean;
  jump: boolean;
}

export function createNeutralInput(): InputState {
  return { left: false, right: false, jump: false };
}

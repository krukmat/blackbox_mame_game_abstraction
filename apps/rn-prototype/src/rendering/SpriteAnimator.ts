export class SpriteAnimator {
  public frameAt(tick: number, frameCount: number): number {
    return frameCount <= 0 ? 0 : tick % frameCount;
  }
}

export class EventBus {
  private events: string[] = [];

  public emit(event: string): void {
    this.events.push(event);
  }

  public drain(): string[] {
    const snapshot = [...this.events];
    this.events = [];
    return snapshot;
  }
}

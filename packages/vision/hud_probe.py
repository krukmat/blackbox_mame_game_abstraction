from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class HudSignal:
    score_delta: int | None = None
    lives_delta: int | None = None
    timer_delta: int | None = None


class HUDProbe(Protocol):
    def observe(self, frame_index: int) -> HudSignal:
        ...

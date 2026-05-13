from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json

from guardrails import ensure_no_private_paths, ensure_public_output_path


@dataclass(slots=True)
class RunState:
    run_id: str
    phase: str = "initialized"
    notes: list[str] = field(default_factory=list)

    def transition(self, next_phase: str, note: str = "") -> None:
        self.phase = next_phase
        if note:
            self.notes.append(note)


@dataclass(slots=True)
class StateReference:
    state_id: str
    description: str
    source_run_id: str


@dataclass(slots=True)
class StateRegistry:
    states: dict[str, StateReference] = field(default_factory=dict)

    def register(self, state: StateReference) -> None:
        self.states[state.state_id] = state

    def resolve(self, state_id: str) -> StateReference:
        if state_id not in self.states:
            raise KeyError(state_id)
        return self.states[state_id]

    def write_metadata(self, output_path: Path) -> Path:
        ensure_public_output_path(output_path)
        payload = {"states": [asdict(state) for state in self.states.values()]}
        ensure_no_private_paths(payload)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return output_path

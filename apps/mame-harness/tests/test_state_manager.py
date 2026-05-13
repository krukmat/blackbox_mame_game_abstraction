from __future__ import annotations

from pathlib import Path
import json

from state_manager import StateReference, StateRegistry


def test_state_registry_writes_metadata_without_private_paths(tmp_path: Path) -> None:
    registry = StateRegistry()
    registry.register(
        StateReference(
            state_id="boot_ready",
            description="Abstract state captured after title transition.",
            source_run_id="run_001",
        )
    )
    output_path = tmp_path / "specs" / "state_registry.json"
    registry.write_metadata(output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["states"][0]["state_id"] == "boot_ready"

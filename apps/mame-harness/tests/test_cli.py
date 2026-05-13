from __future__ import annotations

from cli import _redact_command_paths


def test_redact_command_paths_removes_private_evidence_locations() -> None:
    redacted = _redact_command_paths(
        [
            "mame",
            "pacman",
            "-snapshot_directory",
            "evidence/private/run_demo123/frames",
        ],
        run_id="demo123",
    )
    assert redacted[-1] == "private://demo123/frames"

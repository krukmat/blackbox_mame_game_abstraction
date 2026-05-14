from __future__ import annotations

from pathlib import Path

import pytest

from capture_manager import create_capture_session
from guardrails import ensure_private_evidence_path, ensure_private_or_allowed_metadata_path, ensure_public_output_path


def test_private_evidence_path_isolation(tmp_path: Path) -> None:
    session = create_capture_session("run-001", evidence_root=tmp_path / "evidence" / "private")
    assert session.root.as_posix().endswith("evidence/private/run_run-001")
    assert session.frames_dir.exists()
    assert session.video_dir.exists()
    assert session.logs_dir.exists()
    assert session.metadata_dir.exists()


def test_capture_session_has_states_dir(tmp_path: Path) -> None:
    # T08.2.5 — states_dir must be pre-created so MAME can write save states
    session = create_capture_session("run-002", evidence_root=tmp_path / "evidence" / "private")
    assert hasattr(session, "states_dir")
    assert session.states_dir.exists()
    assert session.states_dir.as_posix().endswith("evidence/private/run_run-002/states")


def test_private_evidence_rejects_tracked_directory() -> None:
    with pytest.raises(ValueError):
        ensure_private_evidence_path(Path("specs/public"))


def test_public_metadata_directory_can_be_explicitly_allowed(tmp_path: Path) -> None:
    allowed = ensure_private_or_allowed_metadata_path(tmp_path / "specs" / "derived", allow_public_metadata=True)
    assert allowed.as_posix().endswith("specs/derived")


@pytest.mark.parametrize("suffix", [".png", ".mp4", ".zip", ".state"])
def test_public_output_rejects_blocked_suffixes(suffix: str) -> None:
    with pytest.raises(ValueError):
        ensure_public_output_path(Path(f"specs/output{suffix}"))

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from guardrails import (
    PRIVATE_EVIDENCE_ROOT,
    ensure_private_evidence_path,
    ensure_private_or_allowed_metadata_path,
)


@dataclass(slots=True)
class CaptureSession:
    run_id: str
    root: Path
    frames_dir: Path
    video_dir: Path
    logs_dir: Path
    metadata_dir: Path
    public_metadata_dir: Path | None = None


def create_capture_session(
    run_id: str,
    evidence_root: Path = PRIVATE_EVIDENCE_ROOT,
    public_metadata_dir: Path | None = None,
) -> CaptureSession:
    root = ensure_private_evidence_path(evidence_root / f"run_{run_id}")
    frames_dir = root / "frames"
    video_dir = root / "video"
    logs_dir = root / "logs"
    metadata_dir = root / "metadata"
    for directory in (frames_dir, video_dir, logs_dir, metadata_dir):
        directory.mkdir(parents=True, exist_ok=True)

    checked_public_dir = None
    if public_metadata_dir is not None:
        checked_public_dir = ensure_private_or_allowed_metadata_path(
            public_metadata_dir,
            allow_public_metadata=True,
        )
        checked_public_dir.mkdir(parents=True, exist_ok=True)

    return CaptureSession(
        run_id=run_id,
        root=root,
        frames_dir=frames_dir,
        video_dir=video_dir,
        logs_dir=logs_dir,
        metadata_dir=metadata_dir,
        public_metadata_dir=checked_public_dir,
    )

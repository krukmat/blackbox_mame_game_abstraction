from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from guardrails import ensure_private_evidence_path


@dataclass(slots=True)
class FrameRecord:
    frame_index: int
    private_path: Path
    width: int
    height: int
    frame_number: int
    timestamp_ms: int


@dataclass(slots=True)
class FrameManifest:
    run_id: str
    frames: list[FrameRecord]

    @classmethod
    def from_run(cls, run_id: str, frames_dir: Path) -> "FrameManifest":
        records: list[FrameRecord] = []
        for index, path in enumerate(sorted(frames_dir.glob("*.pgm"))):
            private_path = ensure_private_evidence_path(path)
            width, height, _ = _read_pgm(path)
            records.append(
                FrameRecord(
                    frame_index=index,
                    private_path=private_path,
                    width=width,
                    height=height,
                    frame_number=index,
                    timestamp_ms=index * 16,
                )
            )
        return cls(run_id=run_id, frames=records)


def load_frame_pixels(path: Path) -> list[list[int]]:
    _, _, pixels = _read_pgm(path)
    return pixels


def _read_pgm(path: Path) -> tuple[int, int, list[list[int]]]:
    lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not lines or lines[0] != "P2":
        raise ValueError(f"unsupported frame format: {path}")
    width, height = [int(value) for value in lines[1].split()]
    max_value = int(lines[2])
    if max_value <= 0:
        raise ValueError("invalid PGM max value")
    values = [int(value) for chunk in lines[3:] for value in chunk.split()]
    if len(values) != width * height:
        raise ValueError("PGM pixel count does not match declared dimensions")

    rows: list[list[int]] = []
    for row_index in range(height):
        start = row_index * width
        rows.append(values[start : start + width])
    return width, height, rows

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from guardrails import ensure_private_evidence_path

# T10.3 — import calibrated timing constants; guard against path when running outside harness
try:
    from fps_calibration import GNG_MS_PER_FRAME, timestamp_ms_for_frame
except ModuleNotFoundError:  # vision package used standalone without harness on sys.path
    GNG_MS_PER_FRAME: float = 16.768  # type: ignore[assignment]

    def timestamp_ms_for_frame(frame_index: int, ms_per_frame: float) -> int:  # type: ignore[misc]
        return int(frame_index * ms_per_frame)

_PNG_SUFFIXES = {".png"}
_PGM_SUFFIXES = {".pgm"}


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
    def from_run(
        cls,
        run_id: str,
        frames_dir: Path,
        ms_per_frame: float = GNG_MS_PER_FRAME,  # T10.3: real interval, not hardcoded 16
    ) -> "FrameManifest":
        # T10.2.1.2 — support extracted_png/ directories produced by ffmpeg (T10.2.1.1 decision)
        png_paths = sorted(frames_dir.glob("*.png"))
        pgm_paths = sorted(frames_dir.glob("*.pgm"))

        if png_paths:
            return cls._from_paths(run_id, png_paths, _read_png, ms_per_frame)
        return cls._from_paths(run_id, pgm_paths, _read_pgm, ms_per_frame)

    @classmethod
    def _from_paths(
        cls,
        run_id: str,
        paths: list[Path],
        reader: object,
        ms_per_frame: float = GNG_MS_PER_FRAME,  # T10.3
    ) -> "FrameManifest":
        records: list[FrameRecord] = []
        for index, path in enumerate(paths):
            private_path = ensure_private_evidence_path(path)
            width, height, _ = reader(path)  # type: ignore[operator]
            records.append(
                FrameRecord(
                    frame_index=index,
                    private_path=private_path,
                    width=width,
                    height=height,
                    frame_number=index,
                    timestamp_ms=timestamp_ms_for_frame(index, ms_per_frame),  # T10.3
                )
            )
        return cls(run_id=run_id, frames=records)


def load_frame_pixels(path: Path) -> list[list[int]]:
    if path.suffix.lower() in _PNG_SUFFIXES:
        _, _, pixels = _read_png(path)
        return pixels
    _, _, pixels = _read_pgm(path)
    return pixels


def _read_png(path: Path) -> tuple[int, int, list[list[int]]]:
    # T10.2.1.2 — read real MAME frame PNGs; convert to grayscale for FrameDiffer
    img = Image.open(path).convert("L")
    width, height = img.size
    raw = list(img.get_flattened_data())
    rows: list[list[int]] = []
    for row_index in range(height):
        start = row_index * width
        rows.append([int(v) for v in raw[start : start + width]])
    return width, height, rows


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

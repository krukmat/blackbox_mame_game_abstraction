from __future__ import annotations

# T10.3 — FPS calibration derived from real capture evidence.
# All values measured from evidence/private/run_*/video/capture.avi via ffprobe.
# Source: run_9d1153ff6637 (1075 frames), run_c935b5ea9321 (359 frames),
#         run_9e02ab7d907c (300 frames) — all agree: r_frame_rate = 536870910/9002251.
#
# Coordinate scale: GNG native resolution is 256x224 pixels.
# One abstract unit = one pixel. movement_tolerance = 2.0 covers sub-pixel
# rounding without masking real position errors.

import json
import subprocess
from fractions import Fraction
from pathlib import Path

# Calibrated constants — derived from real capture AVI, not hardcoded guesses.
GNG_FPS: float = float(Fraction(536870910, 9002251))   # ~59.6374 fps
GNG_MS_PER_FRAME: float = round(1000.0 / GNG_FPS, 3)  # ~16.768 ms
GNG_MOVEMENT_TOLERANCE: float = 2.0                    # units; 256x224 px space, 1 unit = 1 px


def ms_per_frame_from_fps(fps: float) -> float:
    if fps <= 0:
        raise ValueError(f"fps must be positive, got {fps}")
    return round(1000.0 / fps, 3)


def timestamp_ms_for_frame(frame_index: int, ms_per_frame: float) -> int:
    if frame_index < 0:
        raise ValueError(f"frame_index must be >= 0, got {frame_index}")
    if ms_per_frame <= 0:
        raise ValueError(f"ms_per_frame must be positive, got {ms_per_frame}")
    return int(frame_index * ms_per_frame)


def read_avi_fps(avi_path: Path) -> float:
    if not avi_path.exists():
        raise FileNotFoundError(f"AVI not found: {avi_path}")

    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            str(avi_path),
        ],
        capture_output=True,
        text=True,
    )

    data = json.loads(result.stdout) if result.stdout else {}
    video_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]

    if not video_streams:
        raise ValueError(f"no video stream found in {avi_path}")

    rate_str: str = video_streams[0].get("r_frame_rate", "0/0")
    parts = rate_str.split("/")
    num, den = int(parts[0]), int(parts[1]) if len(parts) == 2 else (int(parts[0]), 1)

    if den == 0:
        raise ValueError(f"invalid frame rate '{rate_str}' in {avi_path}")

    return float(Fraction(num, den))

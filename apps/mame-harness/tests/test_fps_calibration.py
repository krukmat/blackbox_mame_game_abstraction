from __future__ import annotations

# T10.3 — Tests for fps_calibration module.
# TDD: these tests must fail before fps_calibration.py is implemented.

import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import fps_calibration
from fps_calibration import (
    GNG_FPS,
    GNG_MS_PER_FRAME,
    GNG_MOVEMENT_TOLERANCE,
    read_avi_fps,
    ms_per_frame_from_fps,
    timestamp_ms_for_frame,
)


# ---------------------------------------------------------------------------
# Constants are numeric and within expected ranges
# ---------------------------------------------------------------------------


def test_gng_fps_is_approximately_59_64() -> None:
    assert 59.0 < GNG_FPS < 60.5


def test_gng_ms_per_frame_is_approximately_16_77() -> None:
    assert 16.5 < GNG_MS_PER_FRAME < 17.0


def test_gng_movement_tolerance_is_positive_and_sub_pixel() -> None:
    # 2.0 units covers sub-pixel rounding in 256x224 abstract coordinate space
    assert 0.5 <= GNG_MOVEMENT_TOLERANCE <= 4.0


# ---------------------------------------------------------------------------
# ms_per_frame_from_fps pure function
# ---------------------------------------------------------------------------


def test_ms_per_frame_from_fps_exact_60() -> None:
    assert abs(ms_per_frame_from_fps(60.0) - 16.667) < 0.01


def test_ms_per_frame_from_fps_gng_nominal() -> None:
    result = ms_per_frame_from_fps(59.6374)
    assert abs(result - 16.768) < 0.01


def test_ms_per_frame_from_fps_rejects_zero() -> None:
    with pytest.raises(ValueError, match="fps must be positive"):
        ms_per_frame_from_fps(0.0)


def test_ms_per_frame_from_fps_rejects_negative() -> None:
    with pytest.raises(ValueError, match="fps must be positive"):
        ms_per_frame_from_fps(-1.0)


# ---------------------------------------------------------------------------
# timestamp_ms_for_frame pure function
# ---------------------------------------------------------------------------


def test_timestamp_ms_for_frame_zero() -> None:
    assert timestamp_ms_for_frame(0, 16.768) == 0


def test_timestamp_ms_for_frame_first() -> None:
    assert timestamp_ms_for_frame(1, 16.768) == 16


def test_timestamp_ms_for_frame_is_integer() -> None:
    result = timestamp_ms_for_frame(5, 16.768)
    assert isinstance(result, int)


def test_timestamp_ms_for_frame_truncates_not_rounds() -> None:
    # frame 10 * 16.768 = 167.68 → 167
    assert timestamp_ms_for_frame(10, 16.768) == 167


def test_timestamp_ms_for_frame_rejects_negative_index() -> None:
    with pytest.raises(ValueError, match="frame_index must be >= 0"):
        timestamp_ms_for_frame(-1, 16.768)


def test_timestamp_ms_for_frame_rejects_non_positive_ms() -> None:
    with pytest.raises(ValueError, match="ms_per_frame must be positive"):
        timestamp_ms_for_frame(0, 0.0)


# ---------------------------------------------------------------------------
# read_avi_fps — calls ffprobe, returns float
# ---------------------------------------------------------------------------


def _ffprobe_output(num: int, den: int, nb_frames: str = "300") -> str:
    return json.dumps({
        "streams": [
            {
                "codec_type": "video",
                "r_frame_rate": f"{num}/{den}",
                "avg_frame_rate": f"{num}/{den}",
                "nb_frames": nb_frames,
            }
        ]
    })


def test_read_avi_fps_parses_ffprobe_output(tmp_path: Path) -> None:
    fake_avi = tmp_path / "evidence" / "private" / "run_test" / "video" / "capture.avi"
    fake_avi.parent.mkdir(parents=True)
    fake_avi.touch()

    mock_result = MagicMock()
    mock_result.stdout = _ffprobe_output(536870910, 9002251)
    mock_result.returncode = 0

    with patch.object(subprocess, "run", return_value=mock_result):
        fps = read_avi_fps(fake_avi)

    assert abs(fps - 59.6374) < 0.001


def test_read_avi_fps_exact_60(tmp_path: Path) -> None:
    fake_avi = tmp_path / "evidence" / "private" / "run_test" / "video" / "capture.avi"
    fake_avi.parent.mkdir(parents=True)
    fake_avi.touch()

    mock_result = MagicMock()
    mock_result.stdout = _ffprobe_output(60, 1)
    mock_result.returncode = 0

    with patch.object(subprocess, "run", return_value=mock_result):
        fps = read_avi_fps(fake_avi)

    assert abs(fps - 60.0) < 0.001


def test_read_avi_fps_raises_if_file_missing(tmp_path: Path) -> None:
    missing = tmp_path / "evidence" / "private" / "run_x" / "video" / "capture.avi"
    with pytest.raises(FileNotFoundError):
        read_avi_fps(missing)


def test_read_avi_fps_raises_if_ffprobe_fails(tmp_path: Path) -> None:
    fake_avi = tmp_path / "evidence" / "private" / "run_test2" / "video" / "capture.avi"
    fake_avi.parent.mkdir(parents=True)
    fake_avi.touch()

    mock_result = MagicMock()
    mock_result.stdout = "{}"
    mock_result.returncode = 1

    with patch.object(subprocess, "run", return_value=mock_result):
        with pytest.raises(ValueError, match="no video stream"):
            read_avi_fps(fake_avi)


def test_read_avi_fps_raises_on_zero_denominator(tmp_path: Path) -> None:
    fake_avi = tmp_path / "evidence" / "private" / "run_test3" / "video" / "capture.avi"
    fake_avi.parent.mkdir(parents=True)
    fake_avi.touch()

    mock_result = MagicMock()
    mock_result.stdout = json.dumps({
        "streams": [{"codec_type": "video", "r_frame_rate": "60/0"}]
    })
    mock_result.returncode = 0

    with patch.object(subprocess, "run", return_value=mock_result):
        with pytest.raises(ValueError, match="invalid frame rate"):
            read_avi_fps(fake_avi)


# ---------------------------------------------------------------------------
# FrameManifest integration — timestamp_ms uses real ms_per_frame
# ---------------------------------------------------------------------------


def test_frame_manifest_uses_real_ms_per_frame(tmp_path: Path) -> None:
    from PIL import Image
    from frame_manifest import FrameManifest

    frames_dir = tmp_path / "evidence" / "private" / "run_cal" / "frames" / "extracted_png"
    frames_dir.mkdir(parents=True)

    for i in range(3):
        img = Image.frombytes("L", (2, 2), bytes([0, 0, 0, 0]))
        img.save(frames_dir / f"{i:04d}.png")

    ms = 16.768
    manifest = FrameManifest.from_run("run_cal", frames_dir, ms_per_frame=ms)

    assert manifest.frames[0].timestamp_ms == 0
    assert manifest.frames[1].timestamp_ms == 16   # int(1 * 16.768)
    assert manifest.frames[2].timestamp_ms == 33   # int(2 * 16.768)


def test_frame_manifest_default_ms_per_frame_unchanged(tmp_path: Path) -> None:
    # When no ms_per_frame is supplied, falls back to GNG_MS_PER_FRAME (not hardcoded 16)
    from PIL import Image
    from frame_manifest import FrameManifest

    frames_dir = tmp_path / "evidence" / "private" / "run_def" / "frames" / "extracted_png"
    frames_dir.mkdir(parents=True)

    img = Image.frombytes("L", (2, 2), bytes([0, 0, 0, 0]))
    img.save(frames_dir / "0000.png")

    manifest = FrameManifest.from_run("run_def", frames_dir)
    assert manifest.frames[0].timestamp_ms == 0

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HARNESS_DIR = ROOT / "apps" / "mame-harness"
VISION_DIR = ROOT / "packages" / "vision"

for candidate in (ROOT, HARNESS_DIR, VISION_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from arthur_tracker import ArthurSignature, ArthurTracker
from frame_differ import FrameDiffStat, MotionBox


def _region(
    x: int,
    y: int,
    width: int,
    height: int,
) -> MotionBox:
    return MotionBox(
        x=x,
        y=y,
        width=width,
        height=height,
        center_x=x + ((width - 1) / 2),
        center_y=y + ((height - 1) / 2),
    )


def _stat(start_frame: int, regions: list[MotionBox]) -> FrameDiffStat:
    return FrameDiffStat(
        start_frame=start_frame,
        end_frame=start_frame + 1,
        changed_pixel_ratio=0.01,
        changed_regions=regions,
    )


class TestArthurTracker:
    def test_find_arthur_returns_none_for_empty_regions(self) -> None:
        tracker = ArthurTracker()
        sig = ArthurSignature()

        assert tracker.find_arthur([], sig) is None

    def test_find_arthur_returns_none_when_all_regions_are_too_short(self) -> None:
        tracker = ArthurTracker()
        sig = ArthurSignature()
        regions = [_region(10, 150, width=12, height=20)]

        assert tracker.find_arthur(regions, sig) is None

    def test_find_arthur_returns_none_when_all_regions_are_too_tall(self) -> None:
        tracker = ArthurTracker()
        sig = ArthurSignature()
        regions = [_region(10, 150, width=12, height=40)]

        assert tracker.find_arthur(regions, sig) is None

    def test_find_arthur_returns_none_when_center_y_is_out_of_range(self) -> None:
        tracker = ArthurTracker()
        sig = ArthurSignature()
        # height=25 and ar=0.88 pass all filters except center_y (y=90 → center_y=102)
        regions = [_region(10, 90, width=22, height=25)]

        assert tracker.find_arthur(regions, sig) is None

    def test_find_arthur_returns_none_when_aspect_ratio_too_low(self) -> None:
        tracker = ArthurTracker()
        sig = ArthurSignature()
        # width=9, height=25 → ar=0.36, below aspect_ratio_min=0.40 (T10.5: lowered from 0.75)
        regions = [_region(20, 160, width=9, height=25)]

        assert tracker.find_arthur(regions, sig) is None

    def test_find_arthur_returns_single_qualifying_region(self) -> None:
        tracker = ArthurTracker()
        sig = ArthurSignature()
        # width=22, height=25 → ar=0.88 — calibrated from GNG manual_01 Arthur sprite
        region = _region(20, 160, width=22, height=25)

        assert tracker.find_arthur([region], sig) == region

    def test_find_arthur_returns_nearest_qualifying_region_to_prev_center(self) -> None:
        tracker = ArthurTracker()
        sig = ArthurSignature()
        near = _region(40, 160, width=22, height=25)
        far = _region(160, 160, width=22, height=25)

        assert tracker.find_arthur([far, near], sig, prev_center=(50.0, 170.0)) == near

    def test_track_sequence_returns_same_length_and_none_for_misses(self) -> None:
        tracker = ArthurTracker()
        sig = ArthurSignature()
        diffs = [
            _stat(0, [_region(20, 160, width=22, height=25)]),
            _stat(1, [_region(22, 162, width=22, height=25)]),
            _stat(2, [_region(22, 120, width=14, height=16)]),  # out of center_y range
        ]

        result = tracker.track_sequence(diffs, sig)

        assert len(result) == len(diffs)
        assert result[0] is not None
        assert result[1] is not None
        assert result[2] is None

    def test_track_sequence_outputs_motion_boxes_or_none_only(self) -> None:
        tracker = ArthurTracker()
        sig = ArthurSignature()
        diffs = [_stat(0, [_region(20, 160, width=22, height=25)])]

        result = tracker.track_sequence(diffs, sig)

        assert len(result) == 1
        assert result[0] is None or isinstance(result[0].center_x, (int, float))
        assert result[0] is None or isinstance(result[0].center_y, (int, float))

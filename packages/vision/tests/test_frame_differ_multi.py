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

from frame_differ import MIN_COMPONENT_PIXELS, FrameDiffer


def _blank(width: int = 8, height: int = 8) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _with_points(
    base: list[list[int]],
    points: list[tuple[int, int]],
    value: int = 255,
) -> list[list[int]]:
    result = [row[:] for row in base]
    for x, y in points:
        result[y][x] = value
    return result


class TestFrameDifferMultiRegion:
    def test_two_separated_blobs_produce_two_regions(self) -> None:
        previous = _blank()
        current = _with_points(
            previous,
            points=[
                (1, 1), (2, 1), (1, 2), (2, 2),
                (5, 4), (6, 4), (5, 5), (6, 5),
            ],
        )

        stat = FrameDiffer()._diff_pair(0, 1, previous, current)

        assert len(stat.changed_regions) == 2
        boxes = sorted(
            [(region.x, region.y, region.width, region.height) for region in stat.changed_regions]
        )
        assert boxes == [(1, 1, 2, 2), (5, 4, 2, 2)]

    def test_three_pixel_component_is_discarded_as_noise(self) -> None:
        previous = _blank()
        current = _with_points(previous, points=[(1, 1), (2, 1), (1, 2)])

        stat = FrameDiffer()._diff_pair(10, 11, previous, current)

        assert MIN_COMPONENT_PIXELS == 4
        assert stat.changed_regions == []

    def test_four_pixel_component_is_kept(self) -> None:
        previous = _blank()
        current = _with_points(previous, points=[(1, 1), (2, 1), (1, 2), (2, 2)])

        stat = FrameDiffer()._diff_pair(20, 21, previous, current)

        assert MIN_COMPONENT_PIXELS == 4
        assert len(stat.changed_regions) == 1
        region = stat.changed_regions[0]
        assert (region.x, region.y, region.width, region.height) == (1, 1, 2, 2)

    def test_single_blob_still_produces_one_region(self) -> None:
        previous = _blank()
        current = _with_points(
            previous,
            points=[(2, 2), (3, 2), (4, 2), (2, 3), (3, 3), (4, 3)],
        )

        stat = FrameDiffer()._diff_pair(30, 31, previous, current)

        assert len(stat.changed_regions) == 1
        region = stat.changed_regions[0]
        assert (region.x, region.y, region.width, region.height) == (2, 2, 3, 2)

    def test_no_change_still_returns_empty_regions(self) -> None:
        previous = _blank()
        current = _blank()

        stat = FrameDiffer()._diff_pair(40, 41, previous, current)

        assert stat.changed_regions == []
        assert stat.changed_pixel_ratio == 0.0

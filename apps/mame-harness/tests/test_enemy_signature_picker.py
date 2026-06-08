"""Regression tests for enemy_signature_picker."""
from __future__ import annotations

from enemy_signature_picker import (
    build_candidate_clusters,
    collect_candidate_observations,
    render_table,
)
from frame_differ import FrameDiffStat, MotionBox


def _region(x: int, y: int, width: int, height: int) -> MotionBox:
    return MotionBox(
        x=x,
        y=y,
        width=width,
        height=height,
        center_x=x + ((width - 1) / 2),
        center_y=y + ((height - 1) / 2),
    )


def _stat(frame: int, regions: list[MotionBox]) -> FrameDiffStat:
    return FrameDiffStat(
        start_frame=frame - 1,
        end_frame=frame,
        changed_pixel_ratio=0.01,
        changed_regions=regions,
    )


def test_collect_candidate_observations_excludes_player_claimed_regions() -> None:
    diffs = [
        _stat(
            10,
            [
                _region(40, 160, 22, 25),  # Arthur-sized region
                _region(120, 166, 18, 29),  # non-player candidate
            ],
        )
    ]

    observations = collect_candidate_observations(diffs)

    assert len(observations) == 1
    assert observations[0].frame == 10
    assert observations[0].width == 18
    assert observations[0].height == 29


def test_build_candidate_clusters_requires_sustained_windows() -> None:
    observations = collect_candidate_observations(
        [
            _stat(20, [_region(120, 166, 18, 29)]),
            _stat(21, [_region(122, 166, 18, 29)]),
            _stat(22, [_region(124, 166, 18, 29)]),
            _stat(23, [_region(126, 166, 18, 29)]),
        ]
    )

    candidates = build_candidate_clusters(observations)

    assert len(candidates) == 1
    assert candidates[0]["sample_count"] == 4
    assert candidates[0]["start_frame"] == 20
    assert candidates[0]["end_frame"] == 23


def test_render_table_contains_no_private_paths() -> None:
    table = render_table(
        [
            {
                "id": 1,
                "start_frame": 1500,
                "end_frame": 1504,
                "sample_count": 5,
                "height_median_px": 29.0,
                "aspect_ratio_median": 0.62,
                "center_y_median_px": 176.0,
                "accepted_as": "zombi",
            }
        ]
    )
    for token in ("evidence/private", "/frames/", ".png", ".avi"):
        assert token not in table

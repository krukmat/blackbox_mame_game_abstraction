from __future__ import annotations

from dataclasses import dataclass

from frame_differ import FrameDiffStat, MotionBox


@dataclass(slots=True)
class ArthurSignature:
    height_min_px: int = 24
    # Calibrated from GNG manual_01: Arthur h=25-27px; zombi/devil h=29-31px
    height_max_px: int = 28
    # Expanded upward for jump frames: manual_02 frames 1356-1375 show cy=144-154px (T10.5)
    center_y_min_px: int = 140
    center_y_max_px: int = 195
    # Lowered for walking-leg diff blobs: manual_02 frames 1415-1426 show ar=0.43-0.61 (T10.5)
    aspect_ratio_min: float = 0.40
    aspect_ratio_max: float = 1.10
    # T10.7: empirically calibrated upper bound — bimodal |Δy| valley at 20-30px (real max ~14px)
    max_frame_jump_px: float = 24.0


class ArthurTracker:
    def find_arthur(
        self,
        regions: list[MotionBox],
        sig: ArthurSignature,
        prev_center: tuple[float, float] | None = None,
    ) -> MotionBox | None:
        candidates = [
            region
            for region in regions
            if sig.height_min_px <= region.height <= sig.height_max_px
            and sig.center_y_min_px <= region.center_y <= sig.center_y_max_px
            and sig.aspect_ratio_min <= (region.width / region.height) <= sig.aspect_ratio_max
        ]
        if not candidates:
            return None

        if prev_center is None:
            return candidates[0]

        prev_x, prev_y = prev_center
        # T10.7: drop candidates that teleported beyond the empirical velocity ceiling
        max_d_sq = sig.max_frame_jump_px ** 2
        candidates = [
            region for region in candidates
            if (region.center_x - prev_x) ** 2 + (region.center_y - prev_y) ** 2 <= max_d_sq
        ]
        if not candidates:
            return None

        return min(
            candidates,
            key=lambda region: (
                (region.center_x - prev_x) ** 2 + (region.center_y - prev_y) ** 2
            ),
        )

    def track_sequence(
        self,
        diffs: list[FrameDiffStat],
        sig: ArthurSignature,
    ) -> list[MotionBox | None]:
        tracked: list[MotionBox | None] = []
        prev_center: tuple[float, float] | None = None

        for diff in diffs:
            match = self.find_arthur(diff.changed_regions, sig, prev_center=prev_center)
            tracked.append(match)
            if match is not None:
                prev_center = (match.center_x, match.center_y)

        return tracked

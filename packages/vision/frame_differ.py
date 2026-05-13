from __future__ import annotations

from dataclasses import asdict, dataclass

from frame_manifest import FrameManifest, load_frame_pixels


@dataclass(slots=True)
class MotionBox:
    x: int
    y: int
    width: int
    height: int
    center_x: float
    center_y: float


@dataclass(slots=True)
class FrameDiffStat:
    start_frame: int
    end_frame: int
    changed_pixel_ratio: float
    changed_regions: list[MotionBox]

    def to_public_dict(self) -> dict[str, object]:
        return {
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "changed_pixel_ratio": round(self.changed_pixel_ratio, 4),
            "changed_regions": [asdict(region) for region in self.changed_regions],
        }


class FrameDiffer:
    def diff_manifest(self, manifest: FrameManifest) -> list[FrameDiffStat]:
        if len(manifest.frames) < 2:
            return []

        stats: list[FrameDiffStat] = []
        for previous, current in zip(manifest.frames, manifest.frames[1:]):
            previous_pixels = load_frame_pixels(previous.private_path)
            current_pixels = load_frame_pixels(current.private_path)
            stats.append(
                self._diff_pair(
                    previous.frame_number,
                    current.frame_number,
                    previous_pixels,
                    current_pixels,
                )
            )
        return stats

    def _diff_pair(
        self,
        start_frame: int,
        end_frame: int,
        previous_pixels: list[list[int]],
        current_pixels: list[list[int]],
    ) -> FrameDiffStat:
        changed_points: list[tuple[int, int]] = []
        height = len(previous_pixels)
        width = len(previous_pixels[0]) if previous_pixels else 0

        for y in range(height):
            for x in range(width):
                if previous_pixels[y][x] != current_pixels[y][x]:
                    changed_points.append((x, y))

        if not changed_points or width == 0 or height == 0:
            return FrameDiffStat(
                start_frame=start_frame,
                end_frame=end_frame,
                changed_pixel_ratio=0.0,
                changed_regions=[],
            )

        min_x = min(point[0] for point in changed_points)
        max_x = max(point[0] for point in changed_points)
        min_y = min(point[1] for point in changed_points)
        max_y = max(point[1] for point in changed_points)
        region = MotionBox(
            x=min_x,
            y=min_y,
            width=(max_x - min_x) + 1,
            height=(max_y - min_y) + 1,
            center_x=(min_x + max_x) / 2,
            center_y=(min_y + max_y) / 2,
        )
        ratio = len(changed_points) / float(width * height)
        return FrameDiffStat(
            start_frame=start_frame,
            end_frame=end_frame,
            changed_pixel_ratio=ratio,
            changed_regions=[region],
        )

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from frame_differ import FrameDiffStat
from metadata_writer import write_public_metadata


@dataclass(slots=True)
class EntityCandidate:
    candidate_id: str
    bbox_stats: dict[str, float]
    motion_stats: dict[str, float]
    observed_frame_ranges: list[dict[str, int]]
    interaction_hints: list[str]
    animation_estimate: dict[str, int]


class EntityCandidateBuilder:
    def build(self, diff_stats: list[FrameDiffStat]) -> list[EntityCandidate]:
        candidates: list[EntityCandidate] = []
        for index, stat in enumerate(diff_stats):
            if not stat.changed_regions:
                continue
            region = stat.changed_regions[0]
            candidates.append(
                EntityCandidate(
                    candidate_id=f"candidate_{index + 1:03d}",
                    bbox_stats={
                        "mean_width": float(region.width),
                        "mean_height": float(region.height),
                        "mean_center_x": float(region.center_x),
                        "mean_center_y": float(region.center_y),
                    },
                    motion_stats={
                        "changed_pixel_ratio": float(stat.changed_pixel_ratio),
                        "travel_frames": float(stat.end_frame - stat.start_frame),
                    },
                    observed_frame_ranges=[
                        {"start_frame": stat.start_frame, "end_frame": stat.end_frame}
                    ],
                    interaction_hints=["movement_detected"],
                    animation_estimate={"frame_count": max(1, stat.end_frame - stat.start_frame)},
                )
            )
        return candidates

    def write_public_output(self, candidates: list[EntityCandidate], output_path: Path) -> Path:
        payload = {"entity_candidates": [asdict(candidate) for candidate in candidates]}
        return write_public_metadata(output_path, payload)

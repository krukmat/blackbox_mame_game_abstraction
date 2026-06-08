"""T10.8.1 — Enemy signature candidate picker.

Reads private frame evidence for a run, extracts non-player motion regions,
groups them into sustained geometry bands, and writes a private candidate JSON
for human review.

Output discipline:
- stdout contains numeric summaries only
- candidate JSON lives under evidence/private/run_<id>/logs/
- no private frame paths are emitted to stdout
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
VISION_DIR = ROOT / "packages" / "vision"
if str(VISION_DIR) not in sys.path:
    sys.path.insert(0, str(VISION_DIR))

from arthur_tracker import ArthurSignature, ArthurTracker
from frame_differ import FrameDiffStat, FrameDiffer, MotionBox, OpenCVBackend
from frame_manifest import FrameManifest
from gng_vision_config import GNGVisionConfig


HEIGHT_BAND_PX: int = 4
ASPECT_RATIO_BAND: float = 0.20
CENTER_Y_BAND_PX: int = 8
MIN_CLUSTER_FRAMES: int = 4
MAX_REVIEW_FRAMES: int = 5
GAMEPLAY_FRAME_MARGIN: int = 30
MIN_ENEMY_HEIGHT_PX: int = 12
MAX_ENEMY_HEIGHT_PX: int = 40
MIN_ENEMY_ASPECT_RATIO: float = 0.35
MAX_ENEMY_ASPECT_RATIO: float = 1.80
MIN_ENEMY_CENTER_Y_PX: int = 70
MAX_ENEMY_CENTER_Y_PX: int = 195
MERGE_FRAME_GAP: int = 2
MERGE_HEIGHT_DELTA_PX: float = 2.0
MERGE_ASPECT_RATIO_DELTA: float = 0.15
MERGE_CENTER_Y_DELTA_PX: float = 6.0


@dataclass(slots=True)
class ObservedRegion:
    frame: int
    x: int
    y: int
    width: int
    height: int
    center_x: float
    center_y: float
    aspect_ratio: float
    area: int


@dataclass(slots=True)
class _ActiveCluster:
    band_key: tuple[int, int, int]
    observations: list[ObservedRegion]
    last_frame: int
    last_center_x: float


def _resolve_frames_dir(run_id: str) -> Path:
    base_frames_dir = ROOT / "evidence" / "private" / f"run_{run_id}" / "frames"
    extracted_png_dir = base_frames_dir / "extracted_png"
    if extracted_png_dir.exists():
        return extracted_png_dir
    return base_frames_dir


def _band_key(observation: ObservedRegion) -> tuple[int, int, int]:
    return (
        observation.height // HEIGHT_BAND_PX,
        int(observation.aspect_ratio / ASPECT_RATIO_BAND),
        int(observation.center_y // CENTER_Y_BAND_PX),
    )


def collect_candidate_observations(
    diff_stats: list[FrameDiffStat],
    tracker: ArthurTracker | None = None,
    signature: ArthurSignature | None = None,
) -> list[ObservedRegion]:
    """Return non-player motion regions with Arthur-claimed boxes removed."""
    tracker = tracker or ArthurTracker()
    signature = signature or ArthurSignature()

    observations: list[ObservedRegion] = []
    player_frames: list[int] = []
    prev_center: tuple[float, float] | None = None

    for diff in diff_stats:
        player_region = tracker.find_arthur(
            diff.changed_regions,
            signature,
            prev_center=prev_center,
        )
        if player_region is not None:
            prev_center = (player_region.center_x, player_region.center_y)
            player_frames.append(diff.end_frame)

        for region in diff.changed_regions:
            if region is player_region:
                continue
            aspect_ratio = (region.width / region.height) if region.height else 0.0
            if not _is_plausible_enemy_region(region, aspect_ratio):
                continue
            observations.append(
                ObservedRegion(
                    frame=diff.end_frame,
                    x=region.x,
                    y=region.y,
                    width=region.width,
                    height=region.height,
                    center_x=region.center_x,
                    center_y=region.center_y,
                    aspect_ratio=aspect_ratio,
                    area=region.width * region.height,
                )
            )

    if player_frames:
        start = min(player_frames) - GAMEPLAY_FRAME_MARGIN
        end = max(player_frames) + GAMEPLAY_FRAME_MARGIN
        observations = [
            observation
            for observation in observations
            if start <= observation.frame <= end
        ]
    return observations


def _is_plausible_enemy_region(region: MotionBox, aspect_ratio: float) -> bool:
    return (
        MIN_ENEMY_HEIGHT_PX <= region.height <= MAX_ENEMY_HEIGHT_PX
        and MIN_ENEMY_ASPECT_RATIO <= aspect_ratio <= MAX_ENEMY_ASPECT_RATIO
        and MIN_ENEMY_CENTER_Y_PX <= region.center_y <= MAX_ENEMY_CENTER_Y_PX
    )


def _finalize_cluster(
    cluster_id: int,
    cluster: _ActiveCluster,
) -> dict[str, Any] | None:
    observations = cluster.observations
    if len(observations) < MIN_CLUSTER_FRAMES:
        return None

    heights = [obs.height for obs in observations]
    widths = [obs.width for obs in observations]
    aspects = [obs.aspect_ratio for obs in observations]
    center_ys = [obs.center_y for obs in observations]
    center_xs = [obs.center_x for obs in observations]
    areas = [obs.area for obs in observations]
    frames = [obs.frame for obs in observations]

    review_frames = sorted(
        {
            frames[0],
            frames[len(frames) // 2],
            frames[-1],
            *frames[: min(len(frames), MAX_REVIEW_FRAMES)],
        }
    )

    return {
        "id": cluster_id,
        "start_frame": frames[0],
        "end_frame": frames[-1],
        "frame_span": frames[-1] - frames[0] + 1,
        "sample_count": len(observations),
        "band": {
            "height_band_px": HEIGHT_BAND_PX,
            "height_band_index": cluster.band_key[0],
            "aspect_ratio_band": ASPECT_RATIO_BAND,
            "aspect_ratio_band_index": cluster.band_key[1],
            "center_y_band_px": CENTER_Y_BAND_PX,
            "center_y_band_index": cluster.band_key[2],
        },
        "height_min_px": min(heights),
        "height_max_px": max(heights),
        "height_median_px": round(statistics.median(heights), 3),
        "width_min_px": min(widths),
        "width_max_px": max(widths),
        "width_median_px": round(statistics.median(widths), 3),
        "area_min_px2": min(areas),
        "area_max_px2": max(areas),
        "aspect_ratio_min": round(min(aspects), 4),
        "aspect_ratio_max": round(max(aspects), 4),
        "aspect_ratio_median": round(statistics.median(aspects), 4),
        "center_y_min_px": round(min(center_ys), 3),
        "center_y_max_px": round(max(center_ys), 3),
        "center_y_median_px": round(statistics.median(center_ys), 3),
        "center_x_min_px": round(min(center_xs), 3),
        "center_x_max_px": round(max(center_xs), 3),
        "review_frames": review_frames,
        "accepted_as": None,
        "review_notes": "",
        "points": [
            {
                "frame": obs.frame,
                "x": obs.x,
                "y": obs.y,
                "width": obs.width,
                "height": obs.height,
                "center_x": round(obs.center_x, 3),
                "center_y": round(obs.center_y, 3),
                "aspect_ratio": round(obs.aspect_ratio, 4),
                "area": obs.area,
            }
            for obs in observations
        ],
    }


def build_candidate_clusters(
    observations: list[ObservedRegion],
) -> list[dict[str, Any]]:
    """Group observations into sustained band-constrained windows."""
    if not observations:
        return []

    observations = sorted(observations, key=lambda obs: (obs.frame, obs.center_y, obs.center_x))
    by_frame: dict[int, list[ObservedRegion]] = {}
    for observation in observations:
        by_frame.setdefault(observation.frame, []).append(observation)

    active_by_key: dict[tuple[int, int, int], list[_ActiveCluster]] = {}
    completed: list[dict[str, Any]] = []
    next_id = 1

    for frame in sorted(by_frame):
        for band_key in list(active_by_key):
            still_active: list[_ActiveCluster] = []
            for cluster in active_by_key[band_key]:
                if frame - cluster.last_frame > 1:
                    finalized = _finalize_cluster(next_id, cluster)
                    if finalized is not None:
                        completed.append(finalized)
                        next_id += 1
                else:
                    still_active.append(cluster)
            if still_active:
                active_by_key[band_key] = still_active
            else:
                del active_by_key[band_key]

        frame_groups: dict[tuple[int, int, int], list[ObservedRegion]] = {}
        for observation in by_frame[frame]:
            frame_groups.setdefault(_band_key(observation), []).append(observation)

        for band_key, candidates in frame_groups.items():
            active_clusters = active_by_key.setdefault(band_key, [])
            matches: list[tuple[float, int, int]] = []
            for cluster_index, cluster in enumerate(active_clusters):
                for candidate_index, candidate in enumerate(candidates):
                    matches.append(
                        (
                            abs(candidate.center_x - cluster.last_center_x),
                            cluster_index,
                            candidate_index,
                        )
                    )

            used_clusters: set[int] = set()
            used_candidates: set[int] = set()
            for _, cluster_index, candidate_index in sorted(matches):
                if cluster_index in used_clusters or candidate_index in used_candidates:
                    continue
                candidate = candidates[candidate_index]
                cluster = active_clusters[cluster_index]
                cluster.observations.append(candidate)
                cluster.last_frame = frame
                cluster.last_center_x = candidate.center_x
                used_clusters.add(cluster_index)
                used_candidates.add(candidate_index)

            for candidate_index, candidate in enumerate(candidates):
                if candidate_index in used_candidates:
                    continue
                active_clusters.append(
                    _ActiveCluster(
                        band_key=band_key,
                        observations=[candidate],
                        last_frame=frame,
                        last_center_x=candidate.center_x,
                    )
                )

    for clusters in active_by_key.values():
        for cluster in clusters:
            finalized = _finalize_cluster(next_id, cluster)
            if finalized is not None:
                completed.append(finalized)
                next_id += 1

    completed = merge_candidate_clusters(completed)
    completed.sort(key=lambda candidate: (candidate["start_frame"], candidate["center_y_median_px"]))
    for index, candidate in enumerate(completed, start=1):
        candidate["id"] = index
    return completed


def merge_candidate_clusters(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not candidates:
        return []

    merged: list[dict[str, Any]] = []
    for candidate in sorted(candidates, key=lambda item: (item["start_frame"], item["center_y_median_px"])):
        target: dict[str, Any] | None = None
        for existing in merged:
            if _should_merge(existing, candidate):
                target = existing
                break
        if target is None:
            merged.append(candidate)
            continue
        target["points"].extend(candidate["points"])
        target["points"].sort(key=lambda point: point["frame"])
        _rebuild_candidate_summary(target)
    return merged


def _should_merge(left: dict[str, Any], right: dict[str, Any]) -> bool:
    frames_overlap = (
        right["start_frame"] <= (left["end_frame"] + MERGE_FRAME_GAP)
        and left["start_frame"] <= (right["end_frame"] + MERGE_FRAME_GAP)
    )
    if not frames_overlap:
        return False
    return (
        abs(left["height_median_px"] - right["height_median_px"]) <= MERGE_HEIGHT_DELTA_PX
        and abs(left["aspect_ratio_median"] - right["aspect_ratio_median"]) <= MERGE_ASPECT_RATIO_DELTA
        and abs(left["center_y_median_px"] - right["center_y_median_px"]) <= MERGE_CENTER_Y_DELTA_PX
    )


def _rebuild_candidate_summary(candidate: dict[str, Any]) -> None:
    points = sorted(candidate["points"], key=lambda point: point["frame"])
    heights = [int(point["height"]) for point in points]
    widths = [int(point["width"]) for point in points]
    aspects = [float(point["aspect_ratio"]) for point in points]
    center_ys = [float(point["center_y"]) for point in points]
    center_xs = [float(point["center_x"]) for point in points]
    areas = [int(point["area"]) for point in points]
    frames = [int(point["frame"]) for point in points]
    review_frames = sorted(
        {
            frames[0],
            frames[len(frames) // 2],
            frames[-1],
            *frames[: min(len(frames), MAX_REVIEW_FRAMES)],
        }
    )

    candidate.update(
        {
            "start_frame": frames[0],
            "end_frame": frames[-1],
            "frame_span": frames[-1] - frames[0] + 1,
            "sample_count": len(points),
            "height_min_px": min(heights),
            "height_max_px": max(heights),
            "height_median_px": round(statistics.median(heights), 3),
            "width_min_px": min(widths),
            "width_max_px": max(widths),
            "width_median_px": round(statistics.median(widths), 3),
            "area_min_px2": min(areas),
            "area_max_px2": max(areas),
            "aspect_ratio_min": round(min(aspects), 4),
            "aspect_ratio_max": round(max(aspects), 4),
            "aspect_ratio_median": round(statistics.median(aspects), 4),
            "center_y_min_px": round(min(center_ys), 3),
            "center_y_max_px": round(max(center_ys), 3),
            "center_y_median_px": round(statistics.median(center_ys), 3),
            "center_x_min_px": round(min(center_xs), 3),
            "center_x_max_px": round(max(center_xs), 3),
            "review_frames": review_frames,
        }
    )


def parse_id_list(raw: str | None) -> list[int]:
    if raw is None or raw.strip() == "":
        return []
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def apply_review_labels(
    candidates: list[dict[str, Any]],
    zombi_ids: list[int],
    crow_ids: list[int],
    rejected_ids: list[int],
) -> dict[str, Any]:
    known_ids = {int(candidate["id"]) for candidate in candidates}
    label_sets = {
        "zombi": set(zombi_ids),
        "crow": set(crow_ids),
        "reject": set(rejected_ids),
    }
    unknown_ids = set().union(*label_sets.values()) - known_ids
    if unknown_ids:
        raise ValueError(f"unknown candidate IDs: {sorted(unknown_ids)}")

    overlap = (label_sets["zombi"] & label_sets["crow"]) | (label_sets["zombi"] & label_sets["reject"]) | (label_sets["crow"] & label_sets["reject"])
    if overlap:
        raise ValueError(f"candidate IDs assigned to multiple review buckets: {sorted(overlap)}")

    accepted_ids_by_type = {
        "zombi": sorted(label_sets["zombi"]),
        "crow": sorted(label_sets["crow"]),
    }

    for candidate in candidates:
        candidate_id = int(candidate["id"])
        if candidate_id in label_sets["zombi"]:
            candidate["accepted_as"] = "zombi"
        elif candidate_id in label_sets["crow"]:
            candidate["accepted_as"] = "crow"
        elif candidate_id in label_sets["reject"]:
            candidate["accepted_as"] = "reject"
        else:
            candidate["accepted_as"] = None

    return {
        "accepted_ids_by_type": accepted_ids_by_type,
        "rejected_ids": sorted(label_sets["reject"]),
        "accepted_candidates": [
            candidate for candidate in candidates
            if candidate.get("accepted_as") in {"zombi", "crow"}
        ],
    }


def build_candidate_payload(
    run_id: str,
    candidates: list[dict[str, Any]],
    review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "run_id": run_id,
        "calibration_method": "enemy_signature_picker",
        "parameters": {
            "height_band_px": HEIGHT_BAND_PX,
            "aspect_ratio_band": ASPECT_RATIO_BAND,
            "center_y_band_px": CENTER_Y_BAND_PX,
            "min_cluster_frames": MIN_CLUSTER_FRAMES,
            "max_review_frames": MAX_REVIEW_FRAMES,
            "gameplay_frame_margin": GAMEPLAY_FRAME_MARGIN,
            "min_enemy_height_px": MIN_ENEMY_HEIGHT_PX,
            "max_enemy_height_px": MAX_ENEMY_HEIGHT_PX,
            "min_enemy_aspect_ratio": MIN_ENEMY_ASPECT_RATIO,
            "max_enemy_aspect_ratio": MAX_ENEMY_ASPECT_RATIO,
            "min_enemy_center_y_px": MIN_ENEMY_CENTER_Y_PX,
            "max_enemy_center_y_px": MAX_ENEMY_CENTER_Y_PX,
            "merge_frame_gap": MERGE_FRAME_GAP,
            "merge_height_delta_px": MERGE_HEIGHT_DELTA_PX,
            "merge_aspect_ratio_delta": MERGE_ASPECT_RATIO_DELTA,
            "merge_center_y_delta_px": MERGE_CENTER_Y_DELTA_PX,
        },
        "candidates": candidates,
    }
    if review is not None:
        payload.update(review)
    return payload


def render_table(candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return "(no candidates detected)"

    header = (
        f"{'ID':>3}  {'START':>5}  {'END':>5}  {'N':>3}  "
        f"{'H_MED':>6}  {'AR_MED':>6}  {'CY_MED':>6}  {'LABEL':>6}"
    )
    lines = [header, "-" * len(header)]
    for candidate in candidates:
        label = candidate["accepted_as"] or "-"
        lines.append(
            f"{candidate['id']:>3}  "
            f"{candidate['start_frame']:>5}  "
            f"{candidate['end_frame']:>5}  "
            f"{candidate['sample_count']:>3}  "
            f"{candidate['height_median_px']:>6.1f}  "
            f"{candidate['aspect_ratio_median']:>6.2f}  "
            f"{candidate['center_y_median_px']:>6.1f}  "
            f"{label:>6}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect sustained enemy-signature candidates from private frame evidence.",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Run identifier without the run_ prefix (e.g. t10_4_01)",
    )
    parser.add_argument(
        "--accept-zombi",
        default="",
        help="Comma-separated candidate IDs accepted as zombi",
    )
    parser.add_argument(
        "--accept-crow",
        default="",
        help="Comma-separated candidate IDs accepted as crow",
    )
    parser.add_argument(
        "--reject-ids",
        default="",
        help="Comma-separated candidate IDs rejected by review",
    )
    args = parser.parse_args(argv)

    frames_dir = _resolve_frames_dir(args.run_id)
    if not frames_dir.exists():
        print(f"ERROR: frames directory not found for run_id={args.run_id}", file=sys.stderr)
        return 1

    manifest = FrameManifest.from_run(args.run_id, frames_dir=frames_dir)
    differ = FrameDiffer(backend=OpenCVBackend(GNGVisionConfig()))
    diff_stats = differ.diff_manifest(manifest)
    observations = collect_candidate_observations(diff_stats)
    candidates = build_candidate_clusters(observations)

    review: dict[str, Any] | None = None
    try:
        review = apply_review_labels(
            candidates,
            zombi_ids=parse_id_list(args.accept_zombi),
            crow_ids=parse_id_list(args.accept_crow),
            rejected_ids=parse_id_list(args.reject_ids),
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"# {len(candidates)} enemy signature candidates from run_id={args.run_id}")
    print("# Candidate rows contain numeric summaries only")
    print()
    print(render_table(candidates))

    out_dir = ROOT / "evidence" / "private" / f"run_{args.run_id}" / "logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "enemy_signature_candidates.json"
    out_path.write_text(json.dumps(build_candidate_payload(args.run_id, candidates, review), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

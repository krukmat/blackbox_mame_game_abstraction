"""T10.7.E — Projectile trajectory picker for in-flight calibration.

Reads the public trace JSON, links per-frame projectile detections into short
candidate trajectories, and emits a structured candidate table for human
accept/reject review.

Conforms to ADR-019 and ADR-020:
- reads only public artifacts (default specs/traces/gng_trace.json)
- stdout shows frame numbers and numeric metadata only
- writes candidate JSON to evidence/private/run_<id>/logs/
- algorithm parameters are source-visible module constants
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


MAX_FRAME_GAP: int = 2
MIN_TRAJECTORY_POINTS: int = 4
MIN_STEP_NORM: float = 0.002
MAX_STEP_NORM: float = 0.080
MAX_Y_STEP_NORM: float = 0.025
MAX_Y_SPAN_NORM: float = 0.050
MIN_NET_DX_NORM: float = 0.012
MAX_VELOCITY_CV: float = 0.45
MIN_LINEAR_R2: float = 0.80
GAMEPLAY_FRAME_MARGIN: int = 30


def load_trace_entries(trace_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(trace_path.read_text())
    if isinstance(payload, dict):
        if "trace" in payload:
            return list(payload["trace"])
        if "entries" in payload:
            return list(payload["entries"])
    if isinstance(payload, list):
        return payload
    return []


def _projectile_points(entries: list[dict[str, Any]]) -> list[dict[str, float | int]]:
    points: list[dict[str, float | int]] = []
    for index, entry in enumerate(entries):
        if entry.get("entity_type") != "projectile":
            continue
        if "frame" not in entry or "x" not in entry or "y" not in entry:
            continue
        points.append({
            "source_index": index,
            "frame": int(entry["frame"]),
            "x": float(entry["x"]),
            "y": float(entry["y"]),
        })
    return sorted(points, key=lambda p: (int(p["frame"]), float(p["y"]), float(p["x"])))


def _gameplay_frame_range(entries: list[dict[str, Any]]) -> tuple[int, int] | None:
    player_frames = [
        int(entry["frame"])
        for entry in entries
        if entry.get("entity_id") == "player" and "frame" in entry
    ]
    if not player_frames:
        return None
    return (
        min(player_frames) - GAMEPLAY_FRAME_MARGIN,
        max(player_frames) + GAMEPLAY_FRAME_MARGIN,
    )


def _median_step(track: list[dict[str, float | int]]) -> float | None:
    if len(track) < 2:
        return None
    steps: list[float] = []
    for prev, curr in zip(track, track[1:]):
        gap = int(curr["frame"]) - int(prev["frame"])
        if gap <= 0:
            continue
        steps.append((float(curr["x"]) - float(prev["x"])) / gap)
    if not steps:
        return None
    return statistics.median(steps)


def _match_score(
    track: list[dict[str, float | int]],
    point: dict[str, float | int],
) -> float | None:
    last = track[-1]
    gap = int(point["frame"]) - int(last["frame"])
    if gap <= 0 or gap > MAX_FRAME_GAP:
        return None

    dx_per_frame = (float(point["x"]) - float(last["x"])) / gap
    dy_per_frame = abs(float(point["y"]) - float(last["y"])) / gap
    abs_dx = abs(dx_per_frame)
    if not (MIN_STEP_NORM <= abs_dx <= MAX_STEP_NORM):
        return None
    if dy_per_frame > MAX_Y_STEP_NORM:
        return None

    median_step = _median_step(track)
    prediction_error = 0.0
    direction_penalty = 0.0
    if median_step is not None:
        if median_step == 0 or math.copysign(1.0, median_step) != math.copysign(1.0, dx_per_frame):
            return None
        predicted_x = float(last["x"]) + median_step * gap
        prediction_error = abs(float(point["x"]) - predicted_x)
        direction_penalty = abs(dx_per_frame - median_step)

    return (
        (dy_per_frame / MAX_Y_STEP_NORM)
        + (prediction_error / MAX_STEP_NORM)
        + (direction_penalty / MAX_STEP_NORM)
        + (gap * 0.01)
    )


def _linear_r2(frames: list[int], xs: list[float]) -> float:
    if len(frames) < 2:
        return 0.0
    mean_frame = statistics.mean(frames)
    mean_x = statistics.mean(xs)
    ss_frame = sum((frame - mean_frame) ** 2 for frame in frames)
    if ss_frame == 0:
        return 0.0
    slope = sum(
        (frame - mean_frame) * (x - mean_x)
        for frame, x in zip(frames, xs)
    ) / ss_frame
    intercept = mean_x - slope * mean_frame
    ss_total = sum((x - mean_x) ** 2 for x in xs)
    if ss_total == 0:
        return 0.0
    ss_residual = sum(
        (x - (slope * frame + intercept)) ** 2
        for frame, x in zip(frames, xs)
    )
    return max(0.0, 1.0 - (ss_residual / ss_total))


def _build_candidate(
    candidate_id: int,
    track: list[dict[str, float | int]],
) -> dict[str, Any] | None:
    if len(track) < MIN_TRAJECTORY_POINTS:
        return None

    frames = [int(point["frame"]) for point in track]
    xs = [float(point["x"]) for point in track]
    ys = [float(point["y"]) for point in track]
    duration_frames = frames[-1] - frames[0]
    if duration_frames <= 0:
        return None

    velocities: list[float] = []
    frame_gaps: list[int] = []
    for prev, curr in zip(track, track[1:]):
        gap = int(curr["frame"]) - int(prev["frame"])
        if gap <= 0:
            continue
        frame_gaps.append(gap)
        velocities.append((float(curr["x"]) - float(prev["x"])) / gap)
    if not velocities:
        return None

    net_dx = xs[-1] - xs[0]
    if abs(net_dx) < MIN_NET_DX_NORM:
        return None

    abs_velocities = [abs(v) for v in velocities]
    velocity_median = statistics.median(velocities)
    abs_velocity_median = statistics.median(abs_velocities)
    velocity_std = statistics.pstdev(abs_velocities) if len(abs_velocities) > 1 else 0.0
    velocity_cv = velocity_std / abs_velocity_median if abs_velocity_median > 0 else 0.0
    y_span = max(ys) - min(ys)
    linearity_r2 = _linear_r2(frames, xs)

    sustained_ok = len(track) >= MIN_TRAJECTORY_POINTS
    speed_ok = (
        MIN_STEP_NORM <= abs_velocity_median <= MAX_STEP_NORM
        and velocity_cv <= MAX_VELOCITY_CV
    )
    y_stable_ok = y_span <= MAX_Y_SPAN_NORM
    linearity_ok = linearity_r2 >= MIN_LINEAR_R2
    direction = "right" if net_dx > 0 else "left"

    return {
        "id": candidate_id,
        "start_frame": frames[0],
        "end_frame": frames[-1],
        "duration_frames": duration_frames,
        "point_count": len(track),
        "direction": direction,
        "start_x": round(xs[0], 6),
        "end_x": round(xs[-1], 6),
        "net_dx": round(net_dx, 6),
        "median_y": round(statistics.median(ys), 6),
        "y_span": round(y_span, 6),
        "velocity_x_median": round(velocity_median, 6),
        "abs_velocity_x_median": round(abs_velocity_median, 6),
        "velocity_x_std": round(velocity_std, 6),
        "velocity_cv": round(velocity_cv, 6),
        "linearity_r2": round(linearity_r2, 6),
        "mean_frame_gap": round(statistics.mean(frame_gaps), 3),
        "sustained_ok": sustained_ok,
        "speed_ok": speed_ok,
        "y_stable_ok": y_stable_ok,
        "linearity_ok": linearity_ok,
        "valid_for_review": sustained_ok and speed_ok and y_stable_ok and linearity_ok,
        "points": [
            {
                "frame": int(point["frame"]),
                "x": round(float(point["x"]), 6),
                "y": round(float(point["y"]), 6),
            }
            for point in track
        ],
    }


def detect_trajectories(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Link projectile detections into deterministic candidate trajectories.

    Matching is greedy and frame-ordered. A detection may attach to an active
    trajectory only when frame gap, horizontal step, vertical drift, and stable
    direction all pass the module-level thresholds above.
    """
    points = _projectile_points(entries)
    frame_range = _gameplay_frame_range(entries)
    if frame_range is not None:
        start_frame, end_frame = frame_range
        points = [
            point for point in points
            if start_frame <= int(point["frame"]) <= end_frame
        ]
    if not points:
        return []

    points_by_frame: dict[int, list[dict[str, float | int]]] = {}
    for point in points:
        points_by_frame.setdefault(int(point["frame"]), []).append(point)

    active: list[list[dict[str, float | int]]] = []
    finished: list[list[dict[str, float | int]]] = []

    for frame in sorted(points_by_frame):
        still_active: list[list[dict[str, float | int]]] = []
        for track in active:
            if frame - int(track[-1]["frame"]) <= MAX_FRAME_GAP:
                still_active.append(track)
            else:
                finished.append(track)
        active = still_active

        frame_points = points_by_frame[frame]
        matches: list[tuple[float, int, int]] = []
        for track_index, track in enumerate(active):
            for point_index, point in enumerate(frame_points):
                score = _match_score(track, point)
                if score is not None:
                    matches.append((score, track_index, point_index))

        used_tracks: set[int] = set()
        used_points: set[int] = set()
        for _, track_index, point_index in sorted(matches):
            if track_index in used_tracks or point_index in used_points:
                continue
            active[track_index].append(frame_points[point_index])
            used_tracks.add(track_index)
            used_points.add(point_index)

        for point_index, point in enumerate(frame_points):
            if point_index not in used_points:
                active.append([point])

    finished.extend(active)

    candidates: list[dict[str, Any]] = []
    next_id = 1
    for track in sorted(
        finished,
        key=lambda item: (int(item[0]["frame"]), float(item[0]["y"]), float(item[0]["x"])),
    ):
        candidate = _build_candidate(next_id, track)
        if candidate is None:
            continue
        candidates.append(candidate)
        next_id += 1
    return candidates


def parse_id_list(raw: str | None) -> list[int]:
    if raw is None or raw.strip() == "":
        return []
    ids: list[int] = []
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        ids.append(int(token))
    return ids


def build_review_payload(
    candidates: list[dict[str, Any]],
    accepted_ids: list[int],
    rejected_ids: list[int],
) -> dict[str, Any]:
    known_ids = {int(candidate["id"]) for candidate in candidates}
    accepted = set(accepted_ids)
    rejected = set(rejected_ids)
    unknown = (accepted | rejected) - known_ids
    if unknown:
        raise ValueError(f"unknown candidate IDs: {sorted(unknown)}")
    overlap = accepted & rejected
    if overlap:
        raise ValueError(f"candidate IDs both accepted and rejected: {sorted(overlap)}")

    return {
        "accepted_ids": sorted(accepted),
        "rejected_ids": sorted(rejected),
        "accepted_candidates": [
            candidate for candidate in candidates if int(candidate["id"]) in accepted
        ],
    }


def render_table(candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return "(no candidates detected)"

    header = (
        f"{'ID':>3}  {'START':>5}  {'END':>5}  {'PTS':>3}  {'DIR':>5}  "
        f"{'DX':>8}  {'V_MED':>8}  {'V_STD':>8}  {'YSPAN':>8}  "
        f"{'R2':>5}  {'OK':>3}"
    )
    lines = [header, "-" * len(header)]
    for candidate in candidates:
        lines.append(
            f"{candidate['id']:>3}  "
            f"{candidate['start_frame']:>5}  "
            f"{candidate['end_frame']:>5}  "
            f"{candidate['point_count']:>3}  "
            f"{candidate['direction']:>5}  "
            f"{candidate['net_dx']:>8.6f}  "
            f"{candidate['abs_velocity_x_median']:>8.6f}  "
            f"{candidate['velocity_x_std']:>8.6f}  "
            f"{candidate['y_span']:>8.6f}  "
            f"{candidate['linearity_r2']:>5.3f}  "
            f"{'yes' if candidate['valid_for_review'] else 'no':>3}"
        )
    return "\n".join(lines)


def _candidate_payload(
    run_id: str,
    trace_path: Path,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "trace_source": str(trace_path),
        "parameters": {
            "max_frame_gap": MAX_FRAME_GAP,
            "min_trajectory_points": MIN_TRAJECTORY_POINTS,
            "min_step_norm": MIN_STEP_NORM,
            "max_step_norm": MAX_STEP_NORM,
            "max_y_step_norm": MAX_Y_STEP_NORM,
            "max_y_span_norm": MAX_Y_SPAN_NORM,
            "min_net_dx_norm": MIN_NET_DX_NORM,
            "max_velocity_cv": MAX_VELOCITY_CV,
            "min_linear_r2": MIN_LINEAR_R2,
            "gameplay_frame_margin": GAMEPLAY_FRAME_MARGIN,
        },
        "candidates": candidates,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect projectile trajectory candidates from public trace.",
    )
    parser.add_argument("run_id", help="Run identifier (e.g. t10_7_projectiles)")
    parser.add_argument(
        "--trace",
        default="specs/traces/gng_trace.json",
        help="Path to public trace JSON",
    )
    parser.add_argument(
        "--accept-ids",
        default="",
        help="Comma-separated candidate IDs accepted by human review",
    )
    parser.add_argument(
        "--reject-ids",
        default="",
        help="Comma-separated candidate IDs rejected by human review",
    )
    args = parser.parse_args(argv)

    trace_path = Path(args.trace)
    if not trace_path.exists():
        print(f"ERROR: trace not found at {trace_path}", file=sys.stderr)
        return 1

    entries = load_trace_entries(trace_path)
    candidates = detect_trajectories(entries)

    print(f"# {len(candidates)} projectile trajectory candidates detected from public trace")
    print("# Candidate rows contain frame numbers and numeric metadata only")
    print()
    print(render_table(candidates))

    out_dir = Path(f"evidence/private/run_{args.run_id}/logs")
    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = out_dir / "projectile_trajectory_candidates.json"
    candidate_path.write_text(json.dumps(
        _candidate_payload(args.run_id, trace_path, candidates),
        indent=2,
    ))

    accepted_ids = parse_id_list(args.accept_ids)
    rejected_ids = parse_id_list(args.reject_ids)
    if accepted_ids or rejected_ids:
        try:
            review_payload = build_review_payload(candidates, accepted_ids, rejected_ids)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        review_path = out_dir / "projectile_trajectory_review.json"
        review_path.write_text(json.dumps({
            "run_id": args.run_id,
            **review_payload,
        }, indent=2))
        print()
        print(
            f"# Review recorded: "
            f"accepted={len(review_payload['accepted_ids'])}, "
            f"rejected={len(review_payload['rejected_ids'])}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())

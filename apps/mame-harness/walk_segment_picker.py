"""T10.7.C ST.C3 — Walk segment candidate detection picker.

Reads the public trace JSON, finds short stable walking runs for the player,
and emits a structured candidate table for human accept/reject review.

Conforms to ADR-019:
- reads only public artifacts (default specs/traces/gng_trace.json)
- stdout shows frame numbers + numeric metadata only
- writes candidate JSON to evidence/private/run_<id>/logs/walk_candidates.json
- algorithm parameters are source-visible module constants
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

MAX_FRAME_GAP: int = 8
MIN_SEGMENT_FRAMES: int = 5
CONSISTENCY_THRESHOLD: float = 0.30
MIN_STEP_NORM: float = 0.003
MAX_STEP_NORM: float = 0.03
MAX_Y_DRIFT_NORM: float = 0.02


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


def _build_segment(
    segment_id: int,
    direction: str,
    frames: list[int],
    xs: list[float],
    ys: list[float],
) -> dict[str, Any] | None:
    if len(frames) < MIN_SEGMENT_FRAMES:
        return None

    deltas = [
        abs(xs[i] - xs[i - 1]) / max(1, frames[i] - frames[i - 1])
        for i in range(1, len(xs))
    ]
    if not deltas:
        return None

    velocity_x_median = statistics.median(deltas)
    velocity_x_std = statistics.pstdev(deltas) if len(deltas) > 1 else 0.0
    consistency_ok = (
        velocity_x_median > 0
        and (velocity_x_std / velocity_x_median) < CONSISTENCY_THRESHOLD
    )

    return {
        "id": segment_id,
        "direction": direction,
        "start_frame": frames[0],
        "end_frame": frames[-1],
        "frame_count": len(frames),
        "velocity_x_median": round(velocity_x_median, 6),
        "velocity_x_std": round(velocity_x_std, 6),
        "y_span": round(max(ys) - min(ys), 6),
        "consistency_ok": consistency_ok,
    }


def detect_segments(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    player_entries = [
        entry for entry in entries
        if entry.get("entity_id") == "player"
    ]
    if len(player_entries) < 2:
        return []

    segments: list[dict[str, Any]] = []
    current_direction: str | None = None
    current_frames: list[int] = []
    current_xs: list[float] = []
    current_ys: list[float] = []
    previous_frame: int | None = None
    next_id = 1

    for prev_entry, entry in zip(player_entries, player_entries[1:]):
        prev_frame = int(prev_entry["frame"])
        frame = int(entry["frame"])
        prev_x = float(prev_entry["x"])
        x = float(entry["x"])
        prev_y = float(prev_entry["y"])
        y = float(entry["y"])

        frame_gap = frame - prev_frame
        dx = x - prev_x
        step = abs(dx)
        step_per_frame = step / frame_gap if frame_gap > 0 else 0.0
        y_drift = abs(y - prev_y)

        direction: str | None = None
        if (
            frame_gap <= MAX_FRAME_GAP
            and MIN_STEP_NORM <= step_per_frame <= MAX_STEP_NORM
            and y_drift <= MAX_Y_DRIFT_NORM
        ):
            direction = "right" if dx > 0 else "left"

        same_segment = (
            direction is not None
            and current_direction == direction
            and previous_frame is not None
            and frame - previous_frame <= MAX_FRAME_GAP
        )

        if direction is None:
            if current_direction is not None:
                segment = _build_segment(
                    next_id,
                    current_direction,
                    current_frames,
                    current_xs,
                    current_ys,
                )
                if segment is not None:
                    segments.append(segment)
                    next_id += 1
            current_direction = None
            current_frames = []
            current_xs = []
            current_ys = []
            previous_frame = None
            continue

        if not same_segment and current_direction is not None:
            segment = _build_segment(
                next_id,
                current_direction,
                current_frames,
                current_xs,
                current_ys,
            )
            if segment is not None:
                segments.append(segment)
                next_id += 1
            current_frames = []
            current_xs = []
            current_ys = []

        if not same_segment:
            current_direction = direction
            current_frames = [prev_frame]
            current_xs = [prev_x]
            current_ys = [prev_y]

        current_frames.append(frame)
        current_xs.append(x)
        current_ys.append(y)
        previous_frame = frame

    if current_direction is not None:
        segment = _build_segment(
            next_id,
            current_direction,
            current_frames,
            current_xs,
            current_ys,
        )
        if segment is not None:
            segments.append(segment)

    return segments


def render_table(candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return "(no candidates detected)"

    header = (
        f"{'ID':>3}  {'DIR':>5}  {'START':>5}  {'END':>5}  "
        f"{'FRAMES':>6}  {'V_MED':>8}  {'V_STD':>8}  {'YSPAN':>8}  {'OK':>3}"
    )
    lines = [header, "-" * len(header)]
    for candidate in candidates:
        lines.append(
            f"{candidate['id']:>3}  "
            f"{candidate['direction']:>5}  "
            f"{candidate['start_frame']:>5}  "
            f"{candidate['end_frame']:>5}  "
            f"{candidate['frame_count']:>6}  "
            f"{candidate['velocity_x_median']:>8.6f}  "
            f"{candidate['velocity_x_std']:>8.6f}  "
            f"{candidate['y_span']:>8.6f}  "
            f"{'yes' if candidate['consistency_ok'] else 'no':>3}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect walk segment candidates from public trace (ADR-019 picker).",
    )
    parser.add_argument("run_id", help="Run identifier (e.g. t10_7_walk)")
    parser.add_argument(
        "--trace",
        default="specs/traces/gng_trace.json",
        help="Path to public trace JSON",
    )
    args = parser.parse_args(argv)

    trace_path = Path(args.trace)
    if not trace_path.exists():
        print(f"ERROR: trace not found at {trace_path}", file=sys.stderr)
        return 1

    entries = load_trace_entries(trace_path)
    candidates = detect_segments(entries)

    print(f"# {len(candidates)} walk candidates detected from public trace")
    print(
        f"# To inspect any frame, open "
        f"evidence/private/run_{args.run_id}/frames/extracted_png/<NNNN>.png"
    )
    print()
    print(render_table(candidates))

    out_dir = Path(f"evidence/private/run_{args.run_id}/logs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "walk_candidates.json"
    out_path.write_text(json.dumps({
        "run_id": args.run_id,
        "trace_source": str(trace_path),
        "parameters": {
            "max_frame_gap": MAX_FRAME_GAP,
            "min_segment_frames": MIN_SEGMENT_FRAMES,
            "consistency_threshold": CONSISTENCY_THRESHOLD,
            "min_step_norm": MIN_STEP_NORM,
            "max_step_norm": MAX_STEP_NORM,
            "max_y_drift_norm": MAX_Y_DRIFT_NORM,
        },
        "candidates": candidates,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

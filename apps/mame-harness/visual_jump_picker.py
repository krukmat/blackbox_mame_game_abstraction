"""T10.7.A ST.A3a — Jump candidate detection picker.

Reads the public trace JSON, runs a local-minima detector on the player y(t)
signal, and emits a structured candidate table for human accept/reject review.

Conforms to ADR-019 (Human-Validated Calibration Candidates Pattern):
- reads only public artifacts (default specs/traces/gng_trace.json)
- stdout shows frame numbers + numeric metadata only (no private paths)
- writes candidate JSON to evidence/private/run_<id>/logs/jump_candidates.json
- algorithm parameters are source-visible module constants
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Algorithm parameters — source-visible per ADR-019
# ---------------------------------------------------------------------------

MIN_DISTANCE_FRAMES: int = 30          # min gap between accepted peaks
MIN_PROMINENCE_NORM: float = 0.05      # min depth of peak vs surrounding y
ANCHOR_WINDOW: int = 25                # frames searched for jump_start / land
ANCHOR_STABLE_TOL: float = 0.01        # |y - median| tolerance for "stable ground"
ANCHOR_BASELINE_SPAN: int = 5          # frames used to compute the ground baseline
FLAT_GROUND_TOL: float = 0.02          # |y_land - y_ground| limit
SYM_RATIO_MIN: float = 0.7             # gravity_descend / gravity_ascend lower bound
SYM_RATIO_MAX: float = 1.4             # gravity_descend / gravity_ascend upper bound
MIN_HEIGHT_NORM: float = 0.01          # candidates below this height are dropped


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------


def find_valleys(
    y: list[float],
    min_distance: int = MIN_DISTANCE_FRAMES,
    min_prominence: float = MIN_PROMINENCE_NORM,
) -> list[int]:
    """Return indices of local minima in y passing distance + prominence filters."""
    accepted: list[int] = []
    for i in range(1, len(y) - 1):
        if not (y[i] < y[i - 1] and y[i] <= y[i + 1]):
            continue
        if accepted and i - accepted[-1] < min_distance:
            if y[i] < y[accepted[-1]]:
                accepted[-1] = i
            continue
        accepted.append(i)

    pruned: list[int] = []
    for idx in accepted:
        left = max(0, idx - min_distance)
        right = min(len(y), idx + min_distance + 1)
        local_max = max(y[left:right])
        if local_max - y[idx] >= min_prominence:
            pruned.append(idx)
    return pruned


def _stable_baseline(y: list[float], start: int, end: int) -> float | None:
    """Median y over [start, end). Returns None if window empty."""
    window = y[max(0, start):max(0, end)]
    if not window:
        return None
    return statistics.median(window)


def _find_jump_start(
    y: list[float],
    frames: list[int],
    peak_idx: int,
) -> int | None:
    """Last index in [peak-ANCHOR_WINDOW, peak-3] with y stable near pre-peak baseline."""
    baseline = _stable_baseline(
        y,
        peak_idx - ANCHOR_WINDOW - ANCHOR_BASELINE_SPAN,
        peak_idx - ANCHOR_WINDOW,
    )
    if baseline is None:
        return None
    lo = max(0, peak_idx - ANCHOR_WINDOW)
    hi = max(0, peak_idx - 3)
    candidate: int | None = None
    for i in range(lo, hi):
        if abs(y[i] - baseline) <= ANCHOR_STABLE_TOL:
            candidate = i
    return candidate


def _find_land(
    y: list[float],
    frames: list[int],
    peak_idx: int,
) -> int | None:
    """First index in [peak+3, peak+ANCHOR_WINDOW] with y stable near post-peak baseline."""
    baseline = _stable_baseline(
        y,
        peak_idx + ANCHOR_WINDOW,
        peak_idx + ANCHOR_WINDOW + ANCHOR_BASELINE_SPAN,
    )
    if baseline is None:
        return None
    lo = min(len(y), peak_idx + 3)
    hi = min(len(y), peak_idx + ANCHOR_WINDOW + 1)
    for i in range(lo, hi):
        if abs(y[i] - baseline) <= ANCHOR_STABLE_TOL:
            return i
    return None


def detect_candidates(player_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply peak detection + anchor identification + per-candidate validation."""
    if len(player_entries) < 3:
        return []

    frames: list[int] = [int(e["frame"]) for e in player_entries]
    y: list[float] = [float(e["y"]) for e in player_entries]

    peak_indices = find_valleys(y)

    candidates: list[dict[str, Any]] = []
    next_id = 1
    for peak_idx in peak_indices:
        start_idx = _find_jump_start(y, frames, peak_idx)
        land_idx = _find_land(y, frames, peak_idx)
        if start_idx is None or land_idx is None:
            continue

        jump_start_frame = frames[start_idx]
        peak_frame = frames[peak_idx]
        land_frame = frames[land_idx]
        y_ground = y[start_idx]
        y_peak = y[peak_idx]
        y_land = y[land_idx]

        height_ascend = y_ground - y_peak
        height_descend = y_land - y_peak
        if height_ascend < MIN_HEIGHT_NORM or height_descend < MIN_HEIGHT_NORM:
            continue

        t_ascend = peak_frame - jump_start_frame
        t_descend = land_frame - peak_frame
        if t_ascend <= 0 or t_descend <= 0:
            continue

        gravity_ascend = 2.0 * height_ascend / (t_ascend ** 2)
        gravity_descend = 2.0 * height_descend / (t_descend ** 2)

        flat_ok = abs(y_land - y_ground) < FLAT_GROUND_TOL
        ratio = gravity_descend / gravity_ascend if gravity_ascend > 0 else 0.0
        sym_ok = SYM_RATIO_MIN <= ratio <= SYM_RATIO_MAX

        candidates.append({
            "id": next_id,
            "jump_start": jump_start_frame,
            "peak": peak_frame,
            "land": land_frame,
            "y_ground": round(y_ground, 4),
            "y_peak": round(y_peak, 4),
            "y_land": round(y_land, 4),
            "height_ascend": round(height_ascend, 4),
            "height_descend": round(height_descend, 4),
            "t_ascend": t_ascend,
            "t_descend": t_descend,
            "gravity_ascend": round(gravity_ascend, 6),
            "gravity_descend": round(gravity_descend, 6),
            "sym_ratio": round(ratio, 3),
            "flat_ok": flat_ok,
            "sym_ok": sym_ok,
        })
        next_id += 1

    return candidates


# ---------------------------------------------------------------------------
# Output formatting (path-discipline per ADR-019)
# ---------------------------------------------------------------------------


def render_table(candidates: list[dict[str, Any]]) -> str:
    """Format candidates as a stdout table. Frame numbers only — no paths."""
    if not candidates:
        return "(no candidates detected)"

    header = (
        f"{'ID':>3}  {'JS':>5}  {'PEAK':>5}  {'LAND':>5}  "
        f"{'H_asc':>7}  {'T_asc':>5}  {'T_dsc':>5}  "
        f"{'sym':>5}  {'FLAT':>5}  {'SYM':>5}"
    )
    lines = [header, "-" * len(header)]
    for c in candidates:
        lines.append(
            f"{c['id']:>3}  {c['jump_start']:>5}  {c['peak']:>5}  {c['land']:>5}  "
            f"{c['height_ascend']:>7.4f}  {c['t_ascend']:>5}  {c['t_descend']:>5}  "
            f"{c['sym_ratio']:>5.2f}  "
            f"{'yes' if c['flat_ok'] else 'no':>5}  "
            f"{'yes' if c['sym_ok'] else 'no':>5}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect jump candidates from public trace (ADR-019 picker).",
    )
    parser.add_argument("run_id", help="Run identifier (e.g. t10_7_jumps)")
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

    payload = json.loads(trace_path.read_text())
    entries = payload.get("trace", payload)
    player_entries = [e for e in entries if e.get("entity_id") == "player"]

    candidates = detect_candidates(player_entries)

    print(f"# {len(candidates)} jump candidates detected from {len(player_entries)} player entries")
    print(
        f"# To verify any candidate visually, open "
        f"evidence/private/run_{args.run_id}/frames/extracted_png/<NNNN>.png"
    )
    print()
    print(render_table(candidates))

    out_dir = Path(f"evidence/private/run_{args.run_id}/logs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "jump_candidates.json"
    out_path.write_text(json.dumps({
        "run_id": args.run_id,
        "trace_source": str(trace_path),
        "parameters": {
            "min_distance_frames": MIN_DISTANCE_FRAMES,
            "min_prominence_norm": MIN_PROMINENCE_NORM,
            "anchor_window": ANCHOR_WINDOW,
            "anchor_stable_tol": ANCHOR_STABLE_TOL,
            "flat_ground_tol": FLAT_GROUND_TOL,
            "sym_ratio_min": SYM_RATIO_MIN,
            "sym_ratio_max": SYM_RATIO_MAX,
            "min_height_norm": MIN_HEIGHT_NORM,
        },
        "candidates": candidates,
    }, indent=2))

    print(f"\n# Candidates written to: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

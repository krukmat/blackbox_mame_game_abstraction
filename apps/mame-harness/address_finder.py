"""T30.2 / ADR-028 — Scripted player-address finder.

Companion to scripts/address_finder_scripted.lua. The Lua dumps one 64 KB RAM
snapshot per input phase (still1, right, still2, left, still3, jump, apex). This
module intersects per-phase filters to isolate the player horizontal/vertical
position addresses deterministically, with no human picker and no TUI.

Logic (RetroAchievements-style differential isolation):
  player_x : value RISES during `right`, FALLS during `left`, and is STABLE during
             the surrounding `still` phases. A genuine x address satisfies all three.
  player_y : value CHANGES between `still3` and `jump`/`apex` (vertical motion) while
             x-driving phases leave it roughly stable.

Output: a private candidates JSON (evidence/private/, gitignored). Addresses and raw
values never reach stdout in a way that crosses the public boundary (ADR-026).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RAM_SIZE = 0x10000

# Sub-sampled right walk (still1 → right_a → right_b → right) lets us score a
# candidate by how smoothly/monotonically it advances — a true position address
# climbs steadily; copies and scroll artifacts jump or plateau.
RIGHT_WALK = ["still1", "right_a", "right_b", "right"]
PHASES = ["still1", "right_a", "right_b", "right", "still2", "left", "still3", "jump", "apex"]


def load_phase(prefix: Path, name: str) -> bytes:
    path = Path(f"{prefix}{name}.bin")
    data = path.read_bytes()
    if len(data) != RAM_SIZE:
        raise ValueError(f"phase '{name}' snapshot is {len(data)} bytes, expected {RAM_SIZE}")
    return data


def _monotonic_increasing(values: list[int], tol: int = 0) -> bool:
    """True if values never decrease (allowing a small wrap tolerance)."""
    return all(values[i + 1] >= values[i] - tol for i in range(len(values) - 1))


def _walk_smoothness(values: list[int]) -> float:
    """Lower is smoother: variance of consecutive deltas. A constant-velocity walk
    has near-equal deltas (low score); a jumpy copy/scroll has high score."""
    deltas = [values[i + 1] - values[i] for i in range(len(values) - 1)]
    if not deltas:
        return float("inf")
    mean = sum(deltas) / len(deltas)
    return sum((d - mean) ** 2 for d in deltas) / len(deltas)


def find_player_x(snaps: dict[str, bytes]) -> list[int]:
    """Player horizontal position.

    A true x address: rises monotonically across the right walk, falls during `left`,
    holds its plateau through the still phases, and is *unaffected by a vertical jump*
    (x holds while y moves). Ranked by horizontal swing magnitude (largest first) so a
    real position beats a near-constant counter that merely passes the monotonic gate.
    """
    s1, r, s2, l, s3 = (snaps[k] for k in ("still1", "right", "still2", "left", "still3"))
    jump, apex = snaps["jump"], snaps["apex"]
    scored: list[tuple[int, int]] = []
    for a in range(RAM_SIZE):
        walk = [snaps[p][a] for p in RIGHT_WALK]
        rose_monotonic = _monotonic_increasing(walk) and walk[-1] > walk[0]
        fell_left = l[a] < s2[a]
        stable_stills = abs(s2[a] - r[a]) <= 2
        x_holds_in_jump = abs(jump[a] - s3[a]) <= 2 and abs(apex[a] - s3[a]) <= 2
        swing = r[a] - s1[a]
        if rose_monotonic and fell_left and stable_stills and x_holds_in_jump and swing >= 20:
            scored.append((-swing, a))  # negative => largest swing first
    scored.sort()
    return [a for _, a in scored]


def find_player_y(snaps: dict[str, bytes], x_addrs: set[int]) -> list[int]:
    """Addresses that change with vertical motion (jump/apex) but are stable across
    the horizontal phases, and are not the x address(es)."""
    s3, jump, apex = snaps["still3"], snaps["jump"], snaps["apex"]
    right, left = snaps["right"], snaps["left"]
    out = []
    for a in range(RAM_SIZE):
        if a in x_addrs:
            continue
        vertical_moved = (jump[a] != s3[a]) or (apex[a] != s3[a])
        horizontal_stable = (right[a] == left[a]) or (abs(right[a] - left[a]) <= 1)
        if vertical_moved and horizontal_stable:
            out.append(a)
    return out


def detect_encoding(addr: int, snaps: dict[str, bytes]) -> str:
    def is_bcd(v: int) -> bool:
        return (v & 0x0F) <= 9 and ((v >> 4) & 0x0F) <= 9

    values = [snaps[p][addr] for p in PHASES]
    return "bcd8" if all(is_bcd(v) for v in values) else "u8"


def build_candidates(prefix: Path) -> dict:
    snaps = {name: load_phase(prefix, name) for name in PHASES}

    x_candidates = find_player_x(snaps)
    y_candidates = find_player_y(snaps, set(x_candidates))

    variables = []
    if x_candidates:
        addr = x_candidates[0]
        variables.append({
            "name": "player_x",
            "address": addr,
            "type": "u8",
            "encoding": detect_encoding(addr, snaps),
        })
    if y_candidates:
        addr = y_candidates[0]
        variables.append({
            "name": "player_y",
            "address": addr,
            "type": "u8",
            "encoding": detect_encoding(addr, snaps),
        })

    return {
        "variables": variables,
        "_diagnostics": {
            "x_candidate_count": len(x_candidates),
            "y_candidate_count": len(y_candidates),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="T30.2 scripted player-address finder.")
    parser.add_argument(
        "--prefix", type=Path, required=True,
        help="Phase snapshot path prefix (e.g. evidence/private/finder/phase_).",
    )
    parser.add_argument(
        "--out", type=Path,
        default=Path("evidence/private/gng_address_candidates.json"),
        help="Output candidates JSON (private; gitignored).",
    )
    args = parser.parse_args()

    result = build_candidates(args.prefix)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    diag = result["_diagnostics"]
    print(f"x candidates: {diag['x_candidate_count']}, y candidates: {diag['y_candidate_count']}")
    print(f"variables found: {[v['name'] for v in result['variables']]}")
    print(f"saved -> {args.out}")


if __name__ == "__main__":
    main()

"""T10.7.A ST.A3a — Regression tests for visual_jump_picker.

Coverage:
- find_valleys: simple valley, clustered valleys, low-prominence rejection
- detect_candidates: emits full metadata for a clean synthetic jump
- render_table: output contains no private paths (ADR-019 path discipline)
"""
from __future__ import annotations

from visual_jump_picker import (
    MIN_PROMINENCE_NORM,
    detect_candidates,
    find_valleys,
    render_table,
)


class TestFindValleys:
    def test_detects_simple_valley(self) -> None:
        # Local minimum at index 2 (value 0.30 between 0.45 and 0.45)
        y = [0.50, 0.45, 0.30, 0.45, 0.50, 0.50, 0.50]
        # Inflate sequence so prominence + distance filters are satisfied trivially
        y_padded = [0.50] * 20 + y + [0.50] * 20
        valleys = find_valleys(y_padded, min_distance=5, min_prominence=0.05)
        # The valley should map back to the padded position of 0.30
        assert 22 in valleys  # index 2 in y + 20 padding

    def test_rejects_clustered_valleys_keeps_deeper(self) -> None:
        # Two minima 3 indices apart (< min_distance=10). Keep the deeper one.
        y = [0.50] * 5 + [0.50, 0.40, 0.50, 0.50, 0.30, 0.50] + [0.50] * 20
        valleys = find_valleys(y, min_distance=10, min_prominence=0.05)
        # Deeper valley (0.30) is at index 5 + 4 = 9; shallow one (0.40) at index 6
        # With min_distance=10 collapsing them, the deeper survives
        assert 9 in valleys
        assert 6 not in valleys

    def test_rejects_below_prominence(self) -> None:
        # Local minimum at index 22 with prominence 0.02 (< MIN_PROMINENCE_NORM=0.05)
        y = [0.50] * 20 + [0.50, 0.49, 0.48, 0.49, 0.50] + [0.50] * 20
        valleys = find_valleys(y, min_distance=5, min_prominence=MIN_PROMINENCE_NORM)
        assert valleys == []

    def test_empty_input_returns_empty(self) -> None:
        assert find_valleys([], min_distance=5, min_prominence=0.05) == []
        assert find_valleys([0.5], min_distance=5, min_prominence=0.05) == []


class TestDetectCandidates:
    def _synthetic_jump(self) -> list[dict[str, object]]:
        """One clean jump: 30 frames idle, 10 frame ascent, 10 frame descent, 30 idle.

        Ground y=0.80; peak y=0.50 (height 0.30 > MIN_HEIGHT_NORM=0.01).
        Symmetric arc → flat_ok + sym_ok should both pass.
        """
        entries: list[dict[str, object]] = []
        # Pre-jump idle at y=0.80
        for f in range(30):
            entries.append({"frame": f, "entity_id": "player", "y": 0.80})
        # Ascent: linear from 0.80 → 0.50 over 10 frames
        for k in range(1, 11):
            entries.append({"frame": 30 + k, "entity_id": "player",
                            "y": round(0.80 - 0.03 * k, 4)})
        # Descent: linear from 0.50 → 0.80 over 10 frames
        for k in range(1, 11):
            entries.append({"frame": 40 + k, "entity_id": "player",
                            "y": round(0.50 + 0.03 * k, 4)})
        # Post-land idle at y=0.80
        for f in range(30):
            entries.append({"frame": 51 + f, "entity_id": "player", "y": 0.80})
        return entries

    def test_emits_full_metadata_for_clean_jump(self) -> None:
        entries = self._synthetic_jump()
        candidates = detect_candidates(entries)
        assert len(candidates) == 1
        c = candidates[0]
        required_fields = {
            "id", "jump_start", "peak", "land",
            "y_ground", "y_peak", "y_land",
            "height_ascend", "height_descend",
            "t_ascend", "t_descend",
            "gravity_ascend", "gravity_descend",
            "sym_ratio", "flat_ok", "sym_ok",
        }
        assert required_fields.issubset(c.keys())
        assert c["flat_ok"] is True
        assert c["sym_ok"] is True
        assert c["height_ascend"] > 0
        assert c["t_ascend"] > 0
        assert c["t_descend"] > 0

    def test_no_candidates_when_no_jumps_present(self) -> None:
        entries = [
            {"frame": f, "entity_id": "player", "y": 0.80}
            for f in range(100)
        ]
        assert detect_candidates(entries) == []


class TestStdoutContract:
    def test_render_table_contains_no_private_paths(self) -> None:
        # Build a candidate set and confirm the rendered table has no leaks.
        candidates = [{
            "id": 1, "jump_start": 1582, "peak": 1592, "land": 1605,
            "y_ground": 0.80, "y_peak": 0.50, "y_land": 0.80,
            "height_ascend": 0.30, "height_descend": 0.30,
            "t_ascend": 10, "t_descend": 13,
            "gravity_ascend": 0.006, "gravity_descend": 0.0036,
            "sym_ratio": 0.60, "flat_ok": True, "sym_ok": False,
        }]
        table = render_table(candidates)
        forbidden = ["evidence/private", "/frames/", ".png", ".avi"]
        for token in forbidden:
            assert token not in table, f"Private token {token!r} leaked in stdout"

    def test_render_table_handles_empty(self) -> None:
        assert render_table([]) == "(no candidates detected)"

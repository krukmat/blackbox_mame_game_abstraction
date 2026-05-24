"""T10.7.C ST.C3 — Regression tests for walk_segment_picker."""
from __future__ import annotations

from walk_segment_picker import detect_segments, render_table


class TestDetectSegments:
    def test_segment_detection_groups_consecutive_walking_frames(self) -> None:
        entries = [
            {"frame": 10, "entity_id": "player", "state": "walking_left", "x": 0.50, "y": 0.80},
            {"frame": 11, "entity_id": "player", "state": "idle", "x": 0.49, "y": 0.80},
            {"frame": 13, "entity_id": "player", "state": "walking_left", "x": 0.48, "y": 0.80},
            {"frame": 16, "entity_id": "player", "state": "idle", "x": 0.47, "y": 0.79},
            {"frame": 19, "entity_id": "player", "state": "walking_left", "x": 0.46, "y": 0.79},
        ]
        segments = detect_segments(entries)
        assert len(segments) == 1
        assert segments[0]["start_frame"] == 10
        assert segments[0]["end_frame"] == 19
        assert segments[0]["frame_count"] == 5
        assert segments[0]["direction"] == "left"

    def test_segment_too_short_is_dropped(self) -> None:
        entries = [
            {"frame": 20, "entity_id": "player", "state": "walking_right", "x": 0.10, "y": 0.80},
            {"frame": 21, "entity_id": "player", "state": "walking_right", "x": 0.11, "y": 0.80},
            {"frame": 22, "entity_id": "player", "state": "walking_right", "x": 0.12, "y": 0.80},
            {"frame": 23, "entity_id": "player", "state": "walking_right", "x": 0.13, "y": 0.80},
        ]
        assert detect_segments(entries) == []

    def test_consistency_gate_passes(self) -> None:
        entries = [
            {"frame": 30, "entity_id": "player", "state": "walking_right", "x": 0.10, "y": 0.80},
            {"frame": 31, "entity_id": "player", "state": "idle", "x": 0.12, "y": 0.80},
            {"frame": 32, "entity_id": "player", "state": "walking_right", "x": 0.14, "y": 0.80},
            {"frame": 33, "entity_id": "player", "state": "idle", "x": 0.16, "y": 0.80},
            {"frame": 34, "entity_id": "player", "state": "walking_right", "x": 0.18, "y": 0.80},
        ]
        segments = detect_segments(entries)
        assert len(segments) == 1
        assert segments[0]["consistency_ok"] is True

    def test_consistency_gate_fails(self) -> None:
        entries = [
            {"frame": 40, "entity_id": "player", "state": "walking_right", "x": 0.10, "y": 0.80},
            {"frame": 41, "entity_id": "player", "state": "walking_right", "x": 0.105, "y": 0.80},
            {"frame": 42, "entity_id": "player", "state": "walking_right", "x": 0.125, "y": 0.80},
            {"frame": 43, "entity_id": "player", "state": "walking_right", "x": 0.129, "y": 0.80},
            {"frame": 44, "entity_id": "player", "state": "walking_right", "x": 0.149, "y": 0.80},
        ]
        segments = detect_segments(entries)
        assert len(segments) == 1
        assert segments[0]["consistency_ok"] is False

    def test_teleport_step_breaks_segment(self) -> None:
        entries = [
            {"frame": 50, "entity_id": "player", "state": "walking_left", "x": 0.90, "y": 0.82},
            {"frame": 51, "entity_id": "player", "state": "idle", "x": 0.89, "y": 0.82},
            {"frame": 52, "entity_id": "player", "state": "walking_left", "x": 0.20, "y": 0.82},
            {"frame": 53, "entity_id": "player", "state": "walking_left", "x": 0.19, "y": 0.82},
            {"frame": 54, "entity_id": "player", "state": "walking_left", "x": 0.18, "y": 0.82},
            {"frame": 55, "entity_id": "player", "state": "walking_left", "x": 0.17, "y": 0.82},
        ]
        segments = detect_segments(entries)
        assert segments == []

    def test_step_is_normalized_by_frame_gap(self) -> None:
        entries = [
            {"frame": 60, "entity_id": "player", "state": "idle", "x": 0.10, "y": 0.80},
            {"frame": 66, "entity_id": "player", "state": "walking_right", "x": 0.13, "y": 0.80},
            {"frame": 72, "entity_id": "player", "state": "walking_right", "x": 0.16, "y": 0.80},
            {"frame": 78, "entity_id": "player", "state": "walking_right", "x": 0.19, "y": 0.80},
            {"frame": 84, "entity_id": "player", "state": "walking_right", "x": 0.22, "y": 0.80},
        ]
        segments = detect_segments(entries)
        assert len(segments) == 1
        assert segments[0]["consistency_ok"] is True


class TestStdoutContract:
    def test_output_contains_no_private_paths(self) -> None:
        table = render_table([{
            "id": 1,
            "direction": "left",
            "start_frame": 1582,
            "end_frame": 1588,
            "frame_count": 7,
            "velocity_x_median": 0.012345,
            "velocity_x_std": 0.000321,
            "y_span": 0.0042,
            "consistency_ok": True,
        }])
        forbidden = ["evidence/private", "/frames/", ".png", ".avi"]
        for token in forbidden:
            assert token not in table

    def test_render_table_handles_empty(self) -> None:
        assert render_table([]) == "(no candidates detected)"

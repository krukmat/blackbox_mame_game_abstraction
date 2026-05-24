"""T10.7.E — Regression tests for projectile_trajectory_picker."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from projectile_trajectory_picker import (
    build_review_payload,
    detect_trajectories,
    main,
    render_table,
)


def _projectile(frame: int, x: float, y: float = 0.72) -> dict:
    return {
        "frame": frame,
        "entity_id": f"projectile_{frame}",
        "entity_type": "projectile",
        "x": x,
        "y": y,
        "velocity_x": 0.0,
        "velocity_y": 0.0,
        "state": "despawned",
        "events": [],
        "score_delta": 0,
    }


class TestDetectTrajectories:
    def test_links_consecutive_projectile_motion(self) -> None:
        entries = [
            _projectile(10, 0.20),
            _projectile(11, 0.23),
            _projectile(12, 0.26),
            _projectile(13, 0.29),
            _projectile(14, 0.32),
        ]
        candidates = detect_trajectories(entries)
        assert len(candidates) == 1
        candidate = candidates[0]
        assert candidate["start_frame"] == 10
        assert candidate["end_frame"] == 14
        assert candidate["point_count"] == 5
        assert candidate["direction"] == "right"
        assert candidate["valid_for_review"] is True
        assert candidate["abs_velocity_x_median"] == pytest.approx(0.03)

    def test_rejects_vertical_drift_beyond_projectile_band(self) -> None:
        entries = [
            _projectile(20, 0.20, 0.70),
            _projectile(21, 0.23, 0.76),
            _projectile(22, 0.26, 0.82),
            _projectile(23, 0.29, 0.88),
            _projectile(24, 0.32, 0.94),
        ]
        assert detect_trajectories(entries) == []

    def test_rejects_direction_reversal(self) -> None:
        entries = [
            _projectile(30, 0.30),
            _projectile(31, 0.33),
            _projectile(32, 0.36),
            _projectile(33, 0.33),
            _projectile(34, 0.30),
        ]
        assert detect_trajectories(entries) == []

    def test_filters_to_public_player_gameplay_window_when_available(self) -> None:
        entries = [
            {"frame": 100, "entity_id": "player", "entity_type": "player", "x": 0.1, "y": 0.7},
            {"frame": 120, "entity_id": "player", "entity_type": "player", "x": 0.2, "y": 0.7},
            _projectile(10, 0.20),
            _projectile(11, 0.23),
            _projectile(12, 0.26),
            _projectile(13, 0.29),
            _projectile(100, 0.20),
            _projectile(101, 0.23),
            _projectile(102, 0.26),
            _projectile(103, 0.29),
        ]
        candidates = detect_trajectories(entries)
        assert len(candidates) == 1
        assert candidates[0]["start_frame"] == 100


class TestReviewPayload:
    def test_build_review_payload_records_accepted_ids(self) -> None:
        candidates = detect_trajectories([
            _projectile(40, 0.20),
            _projectile(41, 0.23),
            _projectile(42, 0.26),
            _projectile(43, 0.29),
        ])
        payload = build_review_payload(candidates, accepted_ids=[1], rejected_ids=[])
        assert payload["accepted_ids"] == [1]
        assert payload["rejected_ids"] == []
        assert payload["accepted_candidates"][0]["id"] == 1

    def test_build_review_payload_rejects_unknown_ids(self) -> None:
        candidates = detect_trajectories([
            _projectile(50, 0.20),
            _projectile(51, 0.23),
            _projectile(52, 0.26),
            _projectile(53, 0.29),
        ])
        with pytest.raises(ValueError, match="unknown candidate IDs"):
            build_review_payload(candidates, accepted_ids=[99], rejected_ids=[])


class TestStdoutContract:
    def test_render_table_contains_no_private_paths(self) -> None:
        candidates = detect_trajectories([
            _projectile(60, 0.20),
            _projectile(61, 0.23),
            _projectile(62, 0.26),
            _projectile(63, 0.29),
        ])
        table = render_table(candidates)
        forbidden = ["evidence/private", "/frames/", ".png", ".avi"]
        for token in forbidden:
            assert token not in table

    def test_main_writes_candidate_file_without_printing_private_path(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        trace_path = tmp_path / "trace.json"
        trace_path.write_text(json.dumps({
            "trace": [
                _projectile(70, 0.20),
                _projectile(71, 0.23),
                _projectile(72, 0.26),
                _projectile(73, 0.29),
            ],
        }))
        monkeypatch.chdir(tmp_path)

        assert main(["unit_projectiles", "--trace", str(trace_path)]) == 0
        stdout = capsys.readouterr().out
        forbidden = ["evidence/private", "/frames/", ".png", ".avi"]
        for token in forbidden:
            assert token not in stdout

        out = (
            tmp_path
            / "evidence/private/run_unit_projectiles/logs/projectile_trajectory_candidates.json"
        )
        assert out.exists()
        payload = json.loads(out.read_text())
        assert payload["candidates"][0]["start_frame"] == 70

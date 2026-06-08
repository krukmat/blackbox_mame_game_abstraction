"""Regression tests for enemy_signature_calibrator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from enemy_signature_calibrator import (
    calibrate_candidate_files,
    write_signature_yaml,
)
from guardrails import ensure_no_private_paths


def _candidate(
    candidate_id: int,
    accepted_as: str,
    start_frame: int,
    heights: list[int],
    aspect_ratios: list[float],
    center_ys: list[float],
) -> dict:
    points = []
    for index, (height, aspect_ratio, center_y) in enumerate(zip(heights, aspect_ratios, center_ys)):
        points.append(
            {
                "frame": start_frame + index,
                "x": 10,
                "y": 20,
                "width": round(height * aspect_ratio),
                "height": height,
                "center_x": 100.0 + index,
                "center_y": center_y,
                "aspect_ratio": aspect_ratio,
                "area": round(height * max(1, round(height * aspect_ratio))),
            }
        )
    return {
        "id": candidate_id,
        "sample_count": len(points),
        "accepted_as": accepted_as,
        "points": points,
    }


def _write_candidate_file(tmp_path: Path, run_id: str, candidates: list[dict]) -> Path:
    path = tmp_path / f"{run_id}_enemy_signature_candidates.json"
    path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "candidates": candidates,
            }
        )
    )
    return path


def test_calibrator_writes_yaml_with_zombi_and_crow_sections(tmp_path: Path) -> None:
    candidate_path = _write_candidate_file(
        tmp_path,
        "t10_4_01",
        [
            _candidate(1, "zombi", 100, [28, 29, 30, 29], [0.62, 0.64, 0.63, 0.61], [175, 176, 177, 176]),
            _candidate(2, "crow", 200, [16, 17, 16, 17], [1.18, 1.20, 1.16, 1.19], [108, 110, 109, 111]),
        ],
    )

    calibrations = calibrate_candidate_files([candidate_path])
    out_path = tmp_path / "specs" / "calibration" / "gng_enemy_signatures.yaml"
    write_signature_yaml(calibrations, out_path)

    payload = yaml.safe_load(out_path.read_text())
    assert payload["signatures"]["zombi"]["entity_type"] == "enemy_a"
    assert payload["signatures"]["crow"]["entity_type"] == "enemy_b"
    assert payload["signatures"]["zombi"]["calibration_method"] == "enemy_signature_picker"
    assert payload["signatures"]["crow"]["calibration_source"] == "t10_4_01"
    ensure_no_private_paths(payload)


def test_calibrator_rejects_clusters_with_sample_count_below_four(tmp_path: Path) -> None:
    candidate_path = _write_candidate_file(
        tmp_path,
        "t10_4_01",
        [
            _candidate(1, "zombi", 100, [28, 29, 30], [0.62, 0.64, 0.63], [175, 176, 177]),
            _candidate(2, "crow", 200, [16, 17, 16, 17], [1.18, 1.20, 1.16, 1.19], [108, 110, 109, 111]),
        ],
    )

    with pytest.raises(ValueError, match="sample_count=3"):
        calibrate_candidate_files([candidate_path])

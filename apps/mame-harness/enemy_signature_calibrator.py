"""T10.8.1 — Enemy signature calibration from accepted picker candidates."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from guardrails import ensure_no_private_paths, ensure_public_output_path


HEIGHT_MARGIN_PX: int = 2
ASPECT_RATIO_MARGIN: float = 0.05
CENTER_Y_MARGIN_PX: int = 4
GAP_TOLERANCE_FRAMES: int = 3
MIN_CLUSTER_SAMPLE_COUNT: int = 4
PERCENTILE_95: float = 0.95
SAFETY_MARGIN_SCALE: float = 1.50

ENTITY_TYPE_BY_LABEL = {
    "zombi": "enemy_a",
    "crow": "enemy_b",
}


@dataclass(slots=True)
class SignatureCalibration:
    label: str
    entity_type: str
    sample_count: int
    cluster_count: int
    height_min_px: int
    height_max_px: int
    aspect_ratio_min: float
    aspect_ratio_max: float
    center_y_min_px: int
    center_y_max_px: int
    max_frame_jump_px: float
    gap_tolerance_frames: int
    calibration_source: list[str]
    accepted_candidate_ids: list[int]
    calibration_method: str = "enemy_signature_picker"

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "sample_count": self.sample_count,
            "cluster_count": self.cluster_count,
            "height_min_px": self.height_min_px,
            "height_max_px": self.height_max_px,
            "aspect_ratio_min": round(self.aspect_ratio_min, 4),
            "aspect_ratio_max": round(self.aspect_ratio_max, 4),
            "center_y_min_px": self.center_y_min_px,
            "center_y_max_px": self.center_y_max_px,
            "max_frame_jump_px": round(self.max_frame_jump_px, 3),
            "gap_tolerance_frames": self.gap_tolerance_frames,
            "calibration_source": self.calibration_source[0]
            if len(self.calibration_source) == 1
            else self.calibration_source,
            "calibration_method": self.calibration_method,
            "accepted_candidate_ids": self.accepted_candidate_ids,
        }


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    index = (len(ordered) - 1) * percentile
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    fraction = index - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * fraction)


def _load_candidate_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _iter_accepted_candidates(payloads: list[dict[str, Any]]) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    accepted: dict[str, list[tuple[str, dict[str, Any]]]] = {"zombi": [], "crow": []}

    for payload in payloads:
        run_id = str(payload["run_id"])
        for candidate in payload.get("candidates", []):
            label = candidate.get("accepted_as")
            if label in accepted:
                accepted[label].append((run_id, candidate))
    return accepted


def _validate_candidate(candidate: dict[str, Any], label: str) -> None:
    sample_count = int(candidate.get("sample_count", 0))
    if sample_count < MIN_CLUSTER_SAMPLE_COUNT:
        raise ValueError(
            f"{label}: candidate {candidate.get('id')} sample_count={sample_count} "
            f"< required minimum {MIN_CLUSTER_SAMPLE_COUNT}"
        )
    if len(candidate.get("points", [])) < MIN_CLUSTER_SAMPLE_COUNT:
        raise ValueError(
            f"{label}: candidate {candidate.get('id')} has fewer than "
            f"{MIN_CLUSTER_SAMPLE_COUNT} points"
        )


def calibrate_candidate_files(candidate_paths: list[Path]) -> dict[str, SignatureCalibration]:
    payloads = [_load_candidate_file(path) for path in candidate_paths]
    accepted_by_type = _iter_accepted_candidates(payloads)

    calibrations: dict[str, SignatureCalibration] = {}
    for label, entity_type in ENTITY_TYPE_BY_LABEL.items():
        accepted = accepted_by_type[label]
        if not accepted:
            raise ValueError(f"{label}: no accepted candidates found")

        heights: list[int] = []
        aspects: list[float] = []
        center_ys: list[float] = []
        jump_distances: list[float] = []
        sources: set[str] = set()
        candidate_ids: list[int] = []
        sample_count = 0

        for run_id, candidate in accepted:
            _validate_candidate(candidate, label)
            sources.add(run_id)
            candidate_ids.append(int(candidate["id"]))
            points = list(candidate["points"])
            sample_count += len(points)

            for point in points:
                heights.append(int(point["height"]))
                aspects.append(float(point["aspect_ratio"]))
                center_ys.append(float(point["center_y"]))

            for prev, curr in zip(points, points[1:]):
                dx = float(curr["center_x"]) - float(prev["center_x"])
                dy = float(curr["center_y"]) - float(prev["center_y"])
                jump_distances.append(math.hypot(dx, dy))

        p95_jump = _percentile(jump_distances, PERCENTILE_95)
        calibrations[label] = SignatureCalibration(
            label=label,
            entity_type=entity_type,
            sample_count=sample_count,
            cluster_count=len(accepted),
            height_min_px=max(0, min(heights) - HEIGHT_MARGIN_PX),
            height_max_px=max(heights) + HEIGHT_MARGIN_PX,
            aspect_ratio_min=max(0.0, min(aspects) - ASPECT_RATIO_MARGIN),
            aspect_ratio_max=max(aspects) + ASPECT_RATIO_MARGIN,
            center_y_min_px=max(0, int(math.floor(min(center_ys) - CENTER_Y_MARGIN_PX))),
            center_y_max_px=int(math.ceil(max(center_ys) + CENTER_Y_MARGIN_PX)),
            max_frame_jump_px=max(1.0, p95_jump * SAFETY_MARGIN_SCALE),
            gap_tolerance_frames=GAP_TOLERANCE_FRAMES,
            calibration_source=sorted(sources),
            accepted_candidate_ids=sorted(candidate_ids),
        )

    return calibrations


def write_signature_yaml(
    calibrations: dict[str, SignatureCalibration],
    output_path: Path,
) -> None:
    ensure_public_output_path(output_path)

    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_by": "enemy_signature_calibrator.py",
        "signatures": {
            label: calibration.to_dict()
            for label, calibration in calibrations.items()
        },
    }

    ensure_no_private_paths(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.dump(payload, default_flow_style=False, sort_keys=False))


def _default_candidate_path(run_id: str) -> Path:
    return Path(f"evidence/private/run_{run_id}/logs/enemy_signature_candidates.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Calibrate enemy signatures from human-accepted picker candidates.",
    )
    parser.add_argument(
        "--run-id",
        default="t10_4_01",
        help="Primary run identifier used when --candidate-json is omitted",
    )
    parser.add_argument(
        "--candidate-json",
        action="append",
        default=[],
        help="Path to enemy_signature_candidates.json; may be repeated",
    )
    parser.add_argument(
        "--output",
        default="specs/calibration/gng_enemy_signatures.yaml",
        help="Public YAML output path",
    )
    args = parser.parse_args(argv)

    candidate_paths = [Path(raw) for raw in args.candidate_json] or [_default_candidate_path(args.run_id)]
    calibrations = calibrate_candidate_files(candidate_paths)
    output_path = Path(args.output)
    write_signature_yaml(calibrations, output_path)

    print("# Enemy signatures calibrated")
    for label, calibration in calibrations.items():
        print(
            f"{label}: entity_type={calibration.entity_type} "
            f"sample_count={calibration.sample_count} "
            f"cluster_count={calibration.cluster_count} "
            f"max_frame_jump_px={calibration.max_frame_jump_px:.3f}"
        )
    print(f"# YAML written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

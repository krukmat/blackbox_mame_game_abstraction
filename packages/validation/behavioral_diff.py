from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json

from guardrails import ensure_no_private_paths, ensure_public_output_path


@dataclass(slots=True)
class TraceEntry:
    frame: int
    entity_id: str
    entity_type: str
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    state: str
    events: list[str]
    score_delta: int = 0


@dataclass(slots=True)
class BehavioralDiffResult:
    passed: bool
    confidence: float
    mismatches: list[str]
    recommended_tuning: list[str]


class BehavioralDiff:
    def compare(
        self,
        observed: list[TraceEntry],
        simulated: list[TraceEntry],
        movement_tolerance: float = 2.0,  # T10.3: GNG native res 256x224 px; 1 unit = 1 px; 2.0 covers sub-pixel rounding
    ) -> BehavioralDiffResult:
        mismatches: list[str] = []
        observed_map = {(entry.frame, entry.entity_id): entry for entry in observed}
        simulated_map = {(entry.frame, entry.entity_id): entry for entry in simulated}
        all_keys = sorted(set(observed_map) | set(simulated_map))

        for key in all_keys:
            observed_entry = observed_map.get(key)
            simulated_entry = simulated_map.get(key)
            if observed_entry is None or simulated_entry is None:
                mismatches.append(f"missing entry for frame={key[0]} entity={key[1]}")
                continue
            if abs(observed_entry.x - simulated_entry.x) > movement_tolerance:
                mismatches.append(f"x mismatch frame={key[0]} entity={key[1]}")
            if abs(observed_entry.y - simulated_entry.y) > movement_tolerance:
                mismatches.append(f"y mismatch frame={key[0]} entity={key[1]}")
            if observed_entry.state != simulated_entry.state:
                mismatches.append(f"state mismatch frame={key[0]} entity={key[1]}")
            if observed_entry.events != simulated_entry.events:
                mismatches.append(f"event mismatch frame={key[0]} entity={key[1]}")
            if observed_entry.score_delta != simulated_entry.score_delta:
                mismatches.append(f"score mismatch frame={key[0]} entity={key[1]}")

        confidence = 1.0 if not all_keys else max(0.0, 1.0 - (len(mismatches) / len(all_keys)))
        passed = not mismatches
        recommended_tuning = [] if passed else ["Adjust movement tuning and event sequencing."]
        return BehavioralDiffResult(
            passed=passed,
            confidence=round(confidence, 3),
            mismatches=mismatches,
            recommended_tuning=recommended_tuning,
        )


def write_validation_reports(
    result: BehavioralDiffResult,
    json_output: Path,
    markdown_output: Path,
) -> dict[str, object]:
    payload = {
        "summary": {
            "pass": result.passed,
            "confidence": result.confidence,
        },
        "mismatched_frames_events": result.mismatches,
        "recommended_tuning": result.recommended_tuning,
    }
    ensure_public_output_path(json_output)
    ensure_public_output_path(markdown_output)
    ensure_no_private_paths(payload)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    markdown_lines = [
        "# Behavioral Validation Report",
        "",
        f"- Pass: {result.passed}",
        f"- Confidence: {result.confidence}",
        "",
        "## Mismatches",
        "",
    ]
    if result.mismatches:
        markdown_lines.extend([f"- {mismatch}" for mismatch in result.mismatches])
    else:
        markdown_lines.append("- None")
    markdown_lines.extend(["", "## Recommended Tuning", ""])
    if result.recommended_tuning:
        markdown_lines.extend([f"- {item}" for item in result.recommended_tuning])
    else:
        markdown_lines.append("- No tuning required")
    markdown_output.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")
    return payload


def write_trace_output(entries: list[TraceEntry], output_path: Path) -> Path:
    payload = {"trace": [asdict(entry) for entry in entries]}
    ensure_public_output_path(output_path)
    ensure_no_private_paths(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def load_trace_entries(path: Path) -> list[TraceEntry]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [TraceEntry(**entry) for entry in payload.get("trace", [])]

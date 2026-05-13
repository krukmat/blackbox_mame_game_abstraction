from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from uuid import uuid4

from capture_manager import create_capture_session
from input_planner import load_input_plan
from mame_runner import MameRunRequest, run_mame
from metadata_writer import write_public_metadata
from preflight import MAME_MINIMUM_VERSION, PreflightIssue
from source_profiles import GNG_SOURCE_PROFILE
from state_manager import RunState
from vision_pipeline import analyze_run_frames
from asset_recipe_generator import generate_asset_recipes
from behavioral_validation import validate_behavior

REPO_SAFE_COMMAND_PATHS = {
    "scripts/mame_autoboot.lua",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Black-box MAME harness scaffold")
    subcommands = parser.add_subparsers(dest="command", required=True)

    init_parser = subcommands.add_parser("init", help="Prepare scaffold directories")
    init_parser.add_argument("--root", type=Path, default=Path("."))

    run_parser = subcommands.add_parser("run", help="Build or execute a MAME run")
    run_parser.add_argument("--rom", required=True)
    run_parser.add_argument("--input-plan", type=Path, default=Path("plans/basic_controls.yaml"))
    run_parser.add_argument("--mame-binary", default="mame")
    run_parser.add_argument("--rom-path", type=Path)
    run_parser.add_argument("--working-dir", type=Path, default=Path("."))
    run_parser.add_argument("--seconds-to-run", type=int)
    run_parser.add_argument("--frames-to-run", type=int)
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--print-json", action="store_true")

    analyze_parser = subcommands.add_parser("analyze-placeholder", help="Analyze private frames into redacted metadata")
    analyze_parser.add_argument("--run-id", required=True)
    analyze_parser.add_argument(
        "--output",
        type=Path,
        default=Path("specs/entities/entity_candidates.generated.json"),
    )

    subcommands.add_parser("infer-placeholder", help="Inference remains intentionally placeholder")

    asset_parser = subcommands.add_parser(
        "generate-asset-recipes-placeholder",
        help="Generate abstract asset recipes from redacted entity candidates",
    )
    asset_parser.add_argument(
        "--entity-candidates",
        type=Path,
        default=Path("specs/entities/entity_candidates.generated.json"),
    )
    asset_parser.add_argument(
        "--output",
        type=Path,
        default=Path("specs/assets/asset_recipes.generated.yaml"),
    )

    validate_parser = subcommands.add_parser(
        "validate-placeholder",
        help="Run clean-room behavioral validation",
    )
    validate_parser.add_argument("--observed-trace", type=Path, required=False)
    validate_parser.add_argument("--simulated-trace", type=Path, required=False)
    validate_parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("specs/validation/reports/behavioral_validation.generated.json"),
    )
    validate_parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("specs/validation/reports/behavioral_validation.generated.md"),
    )

    return parser


def handle_init(root: Path) -> dict[str, str]:
    created = []
    for directory in ("apps/mame-harness", "apps/rn-prototype", "docs", "specs", "evidence/private"):
        target = root / directory
        target.mkdir(parents=True, exist_ok=True)
        created.append(directory)
    return {"status": "initialized", "directories": ",".join(created)}


def handle_run(args: argparse.Namespace) -> dict[str, object]:
    plan = load_input_plan(args.input_plan)
    run_id = uuid4().hex[:12]
    state = RunState(run_id=run_id)
    capture = create_capture_session(run_id)
    source_profile = GNG_SOURCE_PROFILE if args.rom == GNG_SOURCE_PROFILE.profile_id else None
    request = MameRunRequest(
        game_shortname=args.rom,
        mame_binary=args.mame_binary,
        working_dir=args.working_dir,
        source_profile=source_profile,
        rom_path=args.rom_path,
        input_dir=capture.logs_dir,
        state_dir=capture.root / "states",
        snapshot_dir=capture.frames_dir,
        aviwrite_path=capture.video_dir / "capture.avi",
        autoboot_script=Path("scripts/mame_autoboot.lua"),
        frames_to_run=args.frames_to_run,
        seconds_to_run=args.seconds_to_run,
        dry_run=args.dry_run,
    )
    run_result = run_mame(request)
    state_note = {
        "dry_run": "dry-run command generated",
        "preflight_failure": "preflight validation failed",
        "execution_failure": "command execution failed",
        "success": "command executed",
    }[run_result.status]
    state.transition(run_result.status, note=state_note)

    metadata = {
        "run_id": run_id,
        "game_shortname": args.rom,
        "input_plan": plan.plan_name,
        "frame_plan_length": len(plan.expand_to_frames()),
        "dry_run": args.dry_run,
        "private_evidence_ref": f"private://{capture.run_id}",
        "state": state.phase,
        "notes": state.notes,
        "runner_status": run_result.status,
        "command": _redact_command_paths(run_result.command, run_id=run_id),
    }
    if run_result.preflight is not None:
        metadata["preflight"] = {
            "ok": run_result.preflight.ok,
            "profile_id": run_result.preflight.profile_id,
            "driver": run_result.preflight.driver,
            "detected_version": run_result.preflight.detected_version,
            "issues": [
                {"code": issue.code, "field": issue.field, "message": _sanitize_preflight_issue_message(issue)}
                for issue in run_result.preflight.issues
            ],
        }
    if run_result.execution is not None:
        metadata["execution"] = {
            "returncode": run_result.execution.returncode,
            "stdout": _sanitize_execution_output(run_result.execution.stdout),  # T05.3.3
            "stderr": _sanitize_execution_output(run_result.execution.stderr),  # T05.3.3
        }
    write_public_metadata(Path("specs/run_metadata.json"), metadata)
    return metadata


def _redact_command_paths(command: list[str], run_id: str) -> list[str]:
    redacted: list[str] = []
    for part in command:
        normalized = part.replace("\\", "/")
        if "evidence/private/" in normalized:
            suffix = normalized.split(f"run_{run_id}/", maxsplit=1)[-1]
            redacted.append(f"private://{run_id}/{suffix}")
        elif _is_repo_safe_command_reference(normalized):
            redacted.append(normalized)
        elif _looks_like_path(normalized):
            redacted.append("<redacted:path>")
        else:
            redacted.append(part)
    return redacted


def _is_repo_safe_command_reference(value: str) -> bool:
    return value in REPO_SAFE_COMMAND_PATHS


def _sanitize_preflight_issue_message(issue: PreflightIssue) -> str:
    templates = {
        "driver_contract_mismatch": issue.message,
        "mame_binary_missing": "MAME binary was not found. Provide an installed executable or configured binary.",
        "mame_version_probe_failed": "Failed to run the MAME version probe. Confirm the configured MAME binary is executable.",
        "mame_version_unparseable": "Could not parse the MAME version output. Expected '0.<NNN>'.",
        "mame_version_too_old": (
            f"Configured MAME version is below the minimum supported version 0.{MAME_MINIMUM_VERSION}."
        ),
        "rom_path_missing": "ROM input is required. Provide the directory containing the expected ROM zip or the zip itself.",
        "rom_zip_name_mismatch": "ROM input must resolve to the expected ROM zip name for the selected source profile.",
        "rom_zip_missing": "Expected ROM zip was not found at the provided ROM input location.",
    }
    message = templates.get(issue.code, issue.message)
    return _strip_path_like_segments(message)


def _looks_like_path(value: str) -> bool:
    if value.startswith("private://"):
        return False
    if value.startswith("/"):
        return True
    if len(value) >= 3 and value[1] == ":" and value[2] in ("\\", "/"):
        return True
    if "/" in value or "\\" in value:
        return True
    if value.startswith(".") and len(value) > 1:
        return True
    return False


def _strip_path_like_segments(message: str) -> str:
    sanitized = re.sub(r"[A-Za-z]:[\\/][^\s,;:]+", "<redacted:path>", message)
    sanitized = re.sub(r"(?:\.\./|\./|/)[^\s,;:]+", "<redacted:path>", sanitized)
    return sanitized


def _sanitize_execution_output(text: str | None) -> str | None:
    """T05.3.3 — sanitize free-form process output; remove all path-bearing segments."""
    if text is None:
        return None
    # Windows absolute paths: C:\... or C:/...
    sanitized = re.sub(r"[A-Za-z]:[\\/][^\s\]\)>\"']+", "<redacted:path>", text)
    # Unix absolute paths and relative evidence/frame/crop paths
    sanitized = re.sub(r"(?:evidence/private|/frames/|/crops/|(?<!\w)/)[^\s\]\)>\"']+", "<redacted:path>", sanitized)
    return sanitized


def handle_analyze(args: argparse.Namespace) -> dict[str, object]:
    output_path = analyze_run_frames(run_id=args.run_id, output_path=args.output)
    return {"status": "analyzed", "output": str(output_path)}


def handle_asset_recipes(args: argparse.Namespace) -> dict[str, object]:
    output_path = generate_asset_recipes(args.entity_candidates, args.output)
    return {"status": "generated", "output": str(output_path)}


def handle_validation(args: argparse.Namespace) -> dict[str, object]:
    report = validate_behavior(
        observed_trace_path=args.observed_trace,
        simulated_trace_path=args.simulated_trace,
        json_output=args.json_output,
        markdown_output=args.markdown_output,
    )
    return {"status": "validated", "report": report["summary"]}


def handle_placeholder(name: str) -> dict[str, str]:
    return {
        "status": "placeholder",
        "command": name,
        "detail": "Implementation intentionally deferred to a later phase.",
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init":
        result = handle_init(args.root)
    elif args.command == "run":
        result = handle_run(args)
    elif args.command == "analyze-placeholder":
        result = handle_analyze(args)
    elif args.command == "generate-asset-recipes-placeholder":
        result = handle_asset_recipes(args)
    elif args.command == "validate-placeholder":
        result = handle_validation(args)
    else:
        result = handle_placeholder(args.command)

    if getattr(args, "print_json", False) or args.command != "run":
        print(json.dumps(result, indent=2))
    else:
        print(f"run_id={result['run_id']} state={result['state']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

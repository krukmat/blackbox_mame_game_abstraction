from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from uuid import uuid4

HARNESS_DIR = Path(__file__).resolve().parent
ROOT = HARNESS_DIR.parents[1]
VISION_DIR = ROOT / "packages" / "vision"
ASSET_FACTORY_DIR = ROOT / "packages" / "asset-factory"
VALIDATION_DIR = ROOT / "packages" / "validation"

for candidate in (ROOT, HARNESS_DIR, VISION_DIR, ASSET_FACTORY_DIR, VALIDATION_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from capture_manager import create_capture_session
from guardrails import PRIVATE_EVIDENCE_ROOT, ensure_private_evidence_path, ensure_public_output_path
from input_planner import load_input_plan
from map_init_wizard import run_map_init_wizard
from mame_runner import MameRunRequest, run_mame
from memory_map import export_memory_map_json  # T20.5 / ADR-026
from mapping_compiler import compile_mapping_files
from mapping_profiles import load_mapping_profile
from metadata_writer import write_public_metadata
from preflight import MAME_MINIMUM_VERSION, PreflightIssue, parse_mame_version, run_preflight
from retroarch_mapping_importer import import_retroarch_autoconfig_file
from sdl_gamecontrollerdb_importer import import_sdl_gamecontrollerdb_file
from source_profiles import get_source_profile
from state_manager import RunState
from vision_pipeline import analyze_run_frames, extract_run_trace
from asset_recipe_generator import generate_asset_recipes
from behavioral_validation import validate_behavior
import yaml

REPO_SAFE_COMMAND_PATHS = {
    "scripts/mame_autoboot.lua",
}
MAME_INPUT_PLAN_ENV_VAR = "BLACKBOX_INPUT_PLAN_PATH"
MAME_INPUT_TIMELINE_ENV_VAR = "BLACKBOX_INPUT_TIMELINE_PATH"  # T20.1 (ADR-023)
MAME_MEMORY_MAP_ENV_VAR = "BLACKBOX_MEMORY_MAP_PATH"  # T20.5 (ADR-026) — private JSON for Lua
MAME_STATE_TIMELINE_ENV_VAR = "BLACKBOX_STATE_TIMELINE_PATH"  # T20.5 (ADR-026)
# Operator-facing local YAML address map (gitignored); converted to the private JSON above.
MEMORY_MAP_YAML_ENV_VAR = "BLACKBOX_MEMORY_MAP_YAML"
DEFAULT_MEMORY_MAP_YAML = Path("blackbox.local.memory_map.yaml")
DEFAULT_BOOTSTRAP_CONFIG_PATH = Path("blackbox.local.yaml")
DEFAULT_ENV_FILE_PATH = Path(".env")
DEFAULT_TRACE_OUTPUT_PATH = Path("specs/traces/gng_trace.json")
DEFAULT_FFMPEG_BINARY = "ffmpeg"
BOOTSTRAP_ENV_TO_FIELD = {
    "BLACKBOX_MAME_BINARY": "mame_binary",
    "BLACKBOX_FFMPEG_BINARY": "ffmpeg_binary",
    "BLACKBOX_ROM_PATH": "rom_path",
    "BLACKBOX_EVIDENCE_ROOT": "evidence_root",
    "BLACKBOX_SOURCE_PROFILE": "source_profile",
    "BLACKBOX_MAME_DRIVER": "mame_driver",
    "BLACKBOX_BOOT_PLAN": "boot_plan",
    "BLACKBOX_TRACE_INPUT_PLAN": "trace_input_plan",
    "BLACKBOX_TRACE_OUTPUT": "trace_output",
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
    run_parser.add_argument("--source-profile", default=None)
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--print-json", action="store_true")

    analyze_parser = subcommands.add_parser("analyze-placeholder", help="Analyze private frames into redacted metadata")
    analyze_parser.add_argument("--run-id", required=True)
    analyze_parser.add_argument(
        "--output",
        type=Path,
        default=Path("specs/entities/entity_candidates.generated.json"),
    )

    trace_parser = subcommands.add_parser(
        "extract-trace",
        help="Extract a public abstract trace from private gameplay frames",
    )
    trace_parser.add_argument("--run-id", required=True)
    trace_parser.add_argument("--input-plan", type=Path, required=True)
    trace_parser.add_argument(
        "--output",
        type=Path,
        default=Path("specs/traces/gng_trace.generated.json"),
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

    map_parser = subcommands.add_parser("map", help="Validate and compile layered input mapping artifacts")
    map_subcommands = map_parser.add_subparsers(dest="map_command", required=True)

    map_init_parser = map_subcommands.add_parser("init", help="Interactively create a device profile")
    map_init_parser.add_argument("--out", type=Path)
    map_init_parser.add_argument("--controller-preset")
    map_init_parser.add_argument("--device-preset")

    map_validate_parser = map_subcommands.add_parser("validate", help="Validate a layered mapping profile or sequence")
    map_validate_parser.add_argument("--profile", type=Path, required=True)

    map_compile_parser = map_subcommands.add_parser("compile", help="Compile layered mapping files to an input plan")
    map_compile_parser.add_argument("--device", type=Path, required=True)
    map_compile_parser.add_argument("--controller", type=Path, required=True)
    map_compile_parser.add_argument("--game", type=Path, required=True)
    map_compile_parser.add_argument("--sequence", type=Path, required=True)
    map_compile_parser.add_argument("--out", type=Path, required=True)

    map_import_sdl_parser = map_subcommands.add_parser(
        "import-sdl",
        help="Import an SDL GameControllerDB entry into a device profile",
    )
    map_import_sdl_parser.add_argument("--db", type=Path, required=True)
    map_import_sdl_parser.add_argument("--out", type=Path, required=True)
    map_import_sdl_parser.add_argument("--guid")
    map_import_sdl_parser.add_argument("--name")
    map_import_sdl_parser.add_argument("--profile-id")

    map_import_retroarch_parser = map_subcommands.add_parser(
        "import-retroarch",
        help="Import a RetroArch autoconfig file into a device profile",
    )
    map_import_retroarch_parser.add_argument("--config", type=Path, required=True)
    map_import_retroarch_parser.add_argument("--out", type=Path, required=True)
    map_import_retroarch_parser.add_argument("--profile-id")

    # T20.4b — one-command isolation-experiment battery (capture→extract→calibrate→verdict).
    battery_parser = subcommands.add_parser(
        "calibrate-battery",
        help="Run the isolation-experiment battery end to end with one verdict table",
    )
    battery_parser.add_argument("--rom", default="gng")
    battery_parser.add_argument("--rom-path", type=Path)
    battery_parser.add_argument("--mame-binary", default="mame")
    battery_parser.add_argument("--memory-map-yaml", type=Path, default=None)
    battery_parser.add_argument(
        "--output", type=Path, default=Path("specs/calibration/gng_experiment_calibration.yaml")
    )
    battery_parser.add_argument(
        "--run-id", action="append", default=[],
        help="stem=run_id to reuse an existing capture instead of launching MAME (repeatable)",
    )
    battery_parser.add_argument("--ffmpeg-binary", default="ffmpeg")
    battery_parser.add_argument("--print-json", action="store_true")

    doctor_parser = subcommands.add_parser("doctor", help="Check local MAME/bootstrap prerequisites")
    doctor_parser.add_argument("--config", type=Path, default=DEFAULT_BOOTSTRAP_CONFIG_PATH)
    doctor_parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE_PATH)
    doctor_parser.add_argument("--source-profile")
    doctor_parser.add_argument("--mame-driver")
    doctor_parser.add_argument("--mame-binary")
    doctor_parser.add_argument("--ffmpeg-binary")
    doctor_parser.add_argument("--rom-path", type=Path)
    doctor_parser.add_argument("--evidence-root", type=Path)
    doctor_parser.add_argument("--trace-output", type=Path)

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
    input_plan_json_path = plan.export_to_json(capture.logs_dir / "input_plan.json")
    # T20.1 (ADR-023): the Lua bridge writes the ground-truth input timeline here.
    input_timeline_json_path = capture.logs_dir / "input_timeline.json"
    source_profile = get_source_profile(args.source_profile) if args.source_profile else None

    # T20.5 / ADR-026: optional RAM memory tap. If a local YAML address map is configured
    # (env var or default file), convert it to a private JSON the Lua reads and enable the
    # private state timeline. Absent config = no tap (graceful; vision fallback).
    mame_environment = {
        MAME_INPUT_PLAN_ENV_VAR: str(input_plan_json_path.resolve()),
        MAME_INPUT_TIMELINE_ENV_VAR: str(input_timeline_json_path.resolve()),
    }
    memory_map_yaml_env = os.environ.get(MEMORY_MAP_YAML_ENV_VAR)
    memory_map_yaml_path = (
        Path(memory_map_yaml_env)
        if memory_map_yaml_env
        else (DEFAULT_MEMORY_MAP_YAML if DEFAULT_MEMORY_MAP_YAML.exists() else None)
    )
    if memory_map_yaml_path is not None and memory_map_yaml_path.exists():
        memory_map_json_path = export_memory_map_json(
            memory_map_yaml_path, capture.logs_dir / "memory_map.json"
        )
        mame_environment[MAME_MEMORY_MAP_ENV_VAR] = str(memory_map_json_path.resolve())
        mame_environment[MAME_STATE_TIMELINE_ENV_VAR] = str(
            (capture.logs_dir / "state_timeline.json").resolve()
        )

    request = MameRunRequest(
        game_shortname=args.rom,
        mame_binary=args.mame_binary,
        working_dir=args.working_dir,
        source_profile=source_profile,
        rom_path=args.rom_path,
        input_dir=capture.logs_dir,
        state_dir=capture.states_dir,  # T08.2.5
        snapshot_dir=capture.frames_dir,
        aviwrite_path=capture.video_dir / "capture.avi",
        autoboot_script=Path("scripts/mame_autoboot.lua"),
        environment=mame_environment,
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


def handle_extract_trace(args: argparse.Namespace) -> dict[str, object]:
    output_path = extract_run_trace(
        run_id=args.run_id,
        input_plan_path=args.input_plan,
        output_path=args.output,
    )
    return {"status": "trace_extracted", "output": str(output_path)}


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


def handle_map_validate(args: argparse.Namespace) -> dict[str, object]:
    profile = load_mapping_profile(args.profile)
    return {
        "status": "validated",
        "profile_type": profile.profile_type,
        "id": profile.id,
        "path": str(args.profile),
    }


def handle_map_init(args: argparse.Namespace) -> dict[str, object]:
    result = run_map_init_wizard(
        input_stream=sys.stdin,
        output_stream=sys.stdout,
        output_path=args.out,
        controller_preset=args.controller_preset,
        device_preset=args.device_preset,
    )
    return {
        "status": "initialized",
        "output": str(result.output_path),
        "profile_type": result.profile.profile_type,
        "id": result.profile.id,
        "bindings": len(result.profile.raw_to_canonical),
        "next_validate_command": result.next_validate_command,
        "next_compile_command": result.next_compile_command,
    }


def handle_map_compile(args: argparse.Namespace) -> dict[str, object]:
    output_path = compile_mapping_files(
        device_profile_path=args.device,
        controller_profile_path=args.controller,
        game_action_profile_path=args.game,
        input_sequence_path=args.sequence,
        output_path=args.out,
    )
    compiled_plan = load_input_plan(output_path)
    return {
        "status": "compiled",
        "output": str(output_path),
        "plan_name": compiled_plan.plan_name,
        "game_id": compiled_plan.game_id,
        "steps": len(compiled_plan.steps),
    }


def handle_map_import_sdl(args: argparse.Namespace) -> dict[str, object]:
    imported = import_sdl_gamecontrollerdb_file(
        db_path=args.db,
        output_path=args.out,
        name=args.name,
        guid=args.guid,
        profile_id=args.profile_id,
    )
    return {
        "status": "imported",
        "output": str(imported.output_path),
        "profile_type": imported.profile.profile_type,
        "id": imported.profile.id,
        "device_name": imported.profile.device.name,
        "guid": imported.profile.device.guid,
        "bindings": len(imported.profile.raw_to_canonical),
        "warnings": list(imported.warnings),
    }


def handle_map_import_retroarch(args: argparse.Namespace) -> dict[str, object]:
    imported = import_retroarch_autoconfig_file(
        config_path=args.config,
        output_path=args.out,
        profile_id=args.profile_id,
    )
    return {
        "status": "imported",
        "output": str(imported.output_path),
        "profile_type": imported.profile.profile_type,
        "id": imported.profile.id,
        "device_name": imported.profile.device.name,
        "guid": imported.profile.device.guid,
        "bindings": len(imported.profile.raw_to_canonical),
        "warnings": list(imported.warnings),
    }


def handle_calibrate_battery(args: argparse.Namespace) -> dict[str, object]:
    # T20.4b — orchestrate the battery; print the verdict table; return a JSON summary.
    from battery_calibrator import calibrate_battery, format_verdict_table

    run_ids: dict[str, str] = {}
    for item in args.run_id:
        if "=" in item:
            stem, rid = item.split("=", 1)
            run_ids[stem.strip()] = rid.strip()

    # Fall back to the local bootstrap (.env) so the battery is truly one-command.
    rom_path = args.rom_path or (
        Path(os.environ["BLACKBOX_ROM_PATH"]) if os.environ.get("BLACKBOX_ROM_PATH") else None
    )
    mame_binary = os.environ.get("BLACKBOX_MAME_BINARY") or args.mame_binary
    ffmpeg_binary = os.environ.get("BLACKBOX_FFMPEG_BINARY") or args.ffmpeg_binary

    verdicts = calibrate_battery(
        rom=args.rom,
        rom_path=rom_path,
        mame_binary=mame_binary,
        memory_map_yaml=args.memory_map_yaml,
        run_ids=run_ids,
        output_path=args.output,
        ffmpeg_binary=ffmpeg_binary,
    )
    print(format_verdict_table(verdicts))
    return {
        "verdicts": [
            {"experiment_id": v.experiment_id, "status": v.status, "reason": v.reason}
            for v in verdicts
        ],
        "rerun": [v.experiment_id for v in verdicts if v.status == "RERUN"],
    }


def handle_doctor(args: argparse.Namespace) -> dict[str, object]:
    settings, config_sources, config_issues = _load_bootstrap_settings(
        config_path=args.config,
        env_file=args.env_file,
    )
    resolved = _resolve_doctor_settings(args, settings)

    checks: list[dict[str, object]] = []
    issues: list[dict[str, str]] = list(config_issues)

    profile = None
    if resolved["source_profile"] is None:
        issues.append(
            {
                "code": "source_profile_missing",
                "message": "No source profile is configured. Set BLACKBOX_SOURCE_PROFILE or pass --source-profile.",
            }
        )
    else:
        try:
            profile = get_source_profile(resolved["source_profile"])
        except ValueError:
            issues.append(
                {
                    "code": "source_profile_unknown",
                    "message": "Configured source profile is not registered in source_profiles.py.",
                }
            )
        else:
            checks.append(
                {
                    "name": "source_profile",
                    "ok": True,
                    "detail": (
                        f"source profile '{profile.profile_id}' resolves to MAME driver "
                        f"'{profile.mame_driver}'."
                    ),
                }
            )

    if profile is not None:
        configured_driver = resolved["mame_driver"]
        if configured_driver is not None and configured_driver != profile.mame_driver:
            issues.append(
                {
                    "code": "mame_driver_mismatch",
                    "message": "Configured MAME driver does not match the selected source profile.",
                }
            )
        else:
            checks.append(
                {
                    "name": "mame_driver",
                    "ok": True,
                    "detail": f"driver '{profile.mame_driver}' is aligned with the selected source profile.",
                }
            )

    mame_check = _check_mame_binary(resolved["mame_binary"])
    if mame_check["ok"]:
        checks.append(mame_check)
    else:
        issues.append(
            {
                "code": str(mame_check["code"]),
                "message": str(mame_check["detail"]),
            }
        )

    if profile is not None:
        preflight = run_preflight(
            profile=profile,
            mame_binary=resolved["mame_binary"],
            rom_path=resolved["rom_path"],
        )
        filtered_preflight_issues = [
            issue
            for issue in preflight.issues
            if issue.code not in {
                "mame_binary_missing",
                "mame_version_probe_failed",
                "mame_version_unparseable",
                "mame_version_too_old",
            }
        ]
        if preflight.ok:
            checks.append(
                {
                    "name": "source_profile_preflight",
                    "ok": True,
                    "detail": "source-profile driver contract and ROM input passed preflight.",
                }
            )
        elif filtered_preflight_issues:
            for issue in filtered_preflight_issues:
                issues.append(
                    {
                        "code": issue.code,
                        "message": _sanitize_preflight_issue_message(issue),
                    }
                )

    ffmpeg_check = _check_support_binary(
        binary_name=resolved["ffmpeg_binary"],
        check_name="ffmpeg_binary",
        missing_code="ffmpeg_binary_missing",
        missing_detail="ffmpeg executable was not found. Configure BLACKBOX_FFMPEG_BINARY or put ffmpeg on PATH.",
    )
    if ffmpeg_check["ok"]:
        checks.append(ffmpeg_check)
    else:
        issues.append(
            {
                "code": str(ffmpeg_check["code"]),
                "message": str(ffmpeg_check["detail"]),
            }
        )

    evidence_root_issue = _check_private_evidence_root(resolved["evidence_root"])
    if evidence_root_issue is None:
        checks.append(
            {
                "name": "private_evidence_root",
                "ok": True,
                "detail": "private evidence root stays under evidence/private and is writable.",
            }
        )
    else:
        issues.append(evidence_root_issue)

    trace_output_issue = _check_public_trace_output(resolved["trace_output"])
    if trace_output_issue is None:
        checks.append(
            {
                "name": "trace_output",
                "ok": True,
                "detail": "public trace output path is repo-relative and allowed by the public-output guardrails.",
            }
        )
    else:
        issues.append(trace_output_issue)

    return {
        "status": "ok" if not issues else "issues_found",
        "config_sources": config_sources,
        "checks": checks,
        "issues": issues,
    }


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
    elif args.command == "extract-trace":
        result = handle_extract_trace(args)
    elif args.command == "generate-asset-recipes-placeholder":
        result = handle_asset_recipes(args)
    elif args.command == "validate-placeholder":
        result = handle_validation(args)
    elif args.command == "map":
        if args.map_command == "init":
            result = handle_map_init(args)
        elif args.map_command == "validate":
            result = handle_map_validate(args)
        elif args.map_command == "compile":
            result = handle_map_compile(args)
        elif args.map_command == "import-sdl":
            result = handle_map_import_sdl(args)
        elif args.map_command == "import-retroarch":
            result = handle_map_import_retroarch(args)
        else:
            result = handle_placeholder(f"map {args.map_command}")
    elif args.command == "calibrate-battery":
        result = handle_calibrate_battery(args)
    elif args.command == "doctor":
        result = handle_doctor(args)
    else:
        result = handle_placeholder(args.command)

    if getattr(args, "print_json", False) or args.command != "run":
        print(json.dumps(result, indent=2))
    else:
        print(f"run_id={result['run_id']} state={result['state']}")
    return 0

def _load_bootstrap_settings(
    config_path: Path,
    env_file: Path,
) -> tuple[dict[str, str], dict[str, object], list[dict[str, str]]]:
    settings: dict[str, str] = {}
    issues: list[dict[str, str]] = []

    if config_path.exists():
        try:
            settings.update(_load_yaml_bootstrap_file(config_path))
        except ValueError as exc:
            issues.append(
                {
                    "code": "config_file_invalid",
                    "message": str(exc),
                }
            )

    if env_file.exists():
        try:
            settings.update(_load_env_file(env_file))
        except ValueError as exc:
            issues.append(
                {
                    "code": "env_file_invalid",
                    "message": str(exc),
                }
            )

    env_overrides: list[str] = []
    for env_key, field_name in BOOTSTRAP_ENV_TO_FIELD.items():
        value = os.getenv(env_key)
        if value is not None and value != "":
            settings[field_name] = value
            env_overrides.append(env_key)

    config_sources = {
        "config_file": config_path.name if config_path.exists() else None,
        "env_file": env_file.name if env_file.exists() else None,
        "env_overrides": sorted(env_overrides),
    }
    return settings, config_sources, issues


def _load_yaml_bootstrap_file(path: Path) -> dict[str, str]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError("bootstrap config file must contain a YAML object.")

    settings: dict[str, str] = {}
    for field_name in BOOTSTRAP_ENV_TO_FIELD.values():
        value = loaded.get(field_name)
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValueError(f"bootstrap config field '{field_name}' must be a string.")
        settings[field_name] = value
    return settings


def _load_env_file(path: Path) -> dict[str, str]:
    settings: dict[str, str] = {}
    for index, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "=" not in line:
            raise ValueError(f".env file line {index} must use KEY=VALUE syntax.")
        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        field_name = BOOTSTRAP_ENV_TO_FIELD.get(key)
        if field_name is not None:
            settings[field_name] = value
    return settings


def _resolve_doctor_settings(args: argparse.Namespace, settings: dict[str, str]) -> dict[str, object]:
    return {
        "source_profile": args.source_profile or settings.get("source_profile"),
        "mame_driver": args.mame_driver or settings.get("mame_driver"),
        "mame_binary": args.mame_binary or settings.get("mame_binary") or "mame",
        "ffmpeg_binary": args.ffmpeg_binary or settings.get("ffmpeg_binary") or DEFAULT_FFMPEG_BINARY,
        "rom_path": args.rom_path or _optional_path(settings.get("rom_path")),
        "evidence_root": args.evidence_root or _optional_path(settings.get("evidence_root")) or PRIVATE_EVIDENCE_ROOT,
        "trace_output": args.trace_output or _optional_path(settings.get("trace_output")) or DEFAULT_TRACE_OUTPUT_PATH,
    }


def _optional_path(value: str | None) -> Path | None:
    if value is None or value == "":
        return None
    return Path(value)


def _check_mame_binary(mame_binary: str) -> dict[str, object]:
    availability_check = _check_support_binary(
        binary_name=mame_binary,
        check_name="mame_binary",
        missing_code="mame_binary_missing",
        missing_detail="MAME binary was not found. Configure BLACKBOX_MAME_BINARY or put mame on PATH.",
    )
    if not availability_check["ok"]:
        return availability_check

    try:
        completed = subprocess.run(
            [mame_binary, "-version"],
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return {
            "name": "mame_binary",
            "ok": False,
            "code": "mame_version_probe_failed",
            "detail": "Failed to run the MAME version probe. Confirm the configured MAME binary is executable.",
        }

    version = parse_mame_version(completed.stdout)
    if version is None:
        return {
            "name": "mame_binary",
            "ok": False,
            "code": "mame_version_unparseable",
            "detail": "Could not parse the MAME version output. Expected '0.<NNN>'.",
        }
    if version < MAME_MINIMUM_VERSION:
        return {
            "name": "mame_binary",
            "ok": False,
            "code": "mame_version_too_old",
            "detail": f"Configured MAME version is below the minimum supported version 0.{MAME_MINIMUM_VERSION}.",
        }
    return {
        "name": "mame_binary",
        "ok": True,
        "detail": f"configured MAME binary is executable and reports version 0.{version}.",
    }


def _check_support_binary(
    *,
    binary_name: str,
    check_name: str,
    missing_code: str,
    missing_detail: str,
) -> dict[str, object]:
    resolved = shutil.which(binary_name)
    if resolved is None:
        return {
            "name": check_name,
            "ok": False,
            "code": missing_code,
            "detail": missing_detail,
        }
    return {
        "name": check_name,
        "ok": True,
        "detail": f"configured {check_name.replace('_', ' ')} is available.",
    }


def _check_private_evidence_root(path: Path) -> dict[str, str] | None:
    try:
        checked = ensure_private_evidence_path(path)
    except ValueError:
        return {
            "code": "private_evidence_root_invalid",
            "message": "Configured private evidence root must stay under evidence/private.",
        }

    try:
        checked.mkdir(parents=True, exist_ok=True)
        probe_dir = checked / ".doctor_probe"
        probe_dir.mkdir(parents=True, exist_ok=True)
        probe_file = probe_dir / ".write_test"
        probe_file.write_text("ok", encoding="utf-8")
        probe_file.unlink()
        probe_dir.rmdir()
    except OSError:
        return {
            "code": "private_evidence_root_unwritable",
            "message": "Configured private evidence root is not writable.",
        }
    return None


def _check_public_trace_output(path: Path) -> dict[str, str] | None:
    if path.is_absolute():
        return {
            "code": "trace_output_absolute_path",
            "message": "Configured public trace output must be repo-relative, not an absolute machine path.",
        }
    try:
        ensure_public_output_path(path)
    except ValueError:
        return {
            "code": "trace_output_invalid",
            "message": "Configured public trace output is blocked by the clean-room guardrails.",
        }
    return None


if __name__ == "__main__":
    raise SystemExit(main())

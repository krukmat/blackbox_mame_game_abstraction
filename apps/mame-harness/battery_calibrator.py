"""T20.4b — battery orchestrator.

One command runs the whole isolation-experiment battery end to end and returns a single
verdict table, so operator participation is minimal and retries are targeted, never blind.

Per experiment: capture (auto-launched scripted run OR an existing run_id) → extract frames
→ extract trace → fail-fast validation → auto-detect the stable sub-window → calibrate.

Each experiment yields a verdict: PASS | REVIEW | RERUN(<reason>). RERUN names the experiment
and the failed check with a concrete fix; the orchestrator does not silently retry captures.

Clean-room: consumes only the public trace + public plan and writes numbers-only calibration.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from capture_manager import create_capture_session
from experiment_calibrator import (
    ExperimentConstant,
    calibrate_experiment,
    write_experiment_calibration_yaml,
)
from guardrails import PRIVATE_EVIDENCE_ROOT
from input_planner import InputPlan, load_input_plan
from mame_runner import MameRunRequest, run_mame
from memory_map import export_memory_map_json
from source_profiles import SourceProfile, get_source_profile
from vision_pipeline import extract_run_trace

# Lua env vars (mirror scripts/mame_autoboot.lua and cli.py).
INPUT_PLAN_ENV = "BLACKBOX_INPUT_PLAN_PATH"
INPUT_TIMELINE_ENV = "BLACKBOX_INPUT_TIMELINE_PATH"
MEMORY_MAP_ENV = "BLACKBOX_MEMORY_MAP_PATH"
STATE_TIMELINE_ENV = "BLACKBOX_STATE_TIMELINE_PATH"

CAPTURE_MARGIN_FRAMES = 60          # extra frames beyond the plan so the window is fully covered
WINDOW_SEARCH_MARGIN = 30           # tolerance around the declared window when auto-detecting
SPEED_ARGS = ("-nothrottle", "-sound", "none")  # faster-than-realtime headless-ish capture

_WALK_STATES = {"walking_left", "walking_right"}
_AIRBORNE_STATES = {"ascending", "descending"}

# The GNG isolation battery (T20.3 / ADR-024).
DEFAULT_BATTERY = (
    Path("plans/sequences/gng_exp_idle_baseline.yaml"),
    Path("plans/sequences/gng_exp_walk_right.yaml"),
    Path("plans/sequences/gng_exp_walk_left.yaml"),
    Path("plans/sequences/gng_exp_jump_in_place.yaml"),
    Path("plans/sequences/gng_exp_fire_stationary.yaml"),
)


@dataclass(slots=True)
class ExperimentVerdict:
    experiment_id: str
    status: str                       # PASS | REVIEW | RERUN
    reason: str = ""
    constants: dict[str, ExperimentConstant] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Capture
# ─────────────────────────────────────────────────────────────────────────────


def _capture_experiment(
    plan: InputPlan,
    plan_path: Path,
    profile: SourceProfile,
    rom_path: Path | None,
    mame_binary: str,
    memory_map_yaml: Path | None,
) -> tuple[str, str, str]:
    """Auto-launch a scripted capture for one experiment. Returns (run_id, status, detail).

    Uses the source profile's MAME driver as the machine name (e.g. gng → gngb,
    ADR-005), not the profile id. ``detail`` carries an actionable reason on failure.
    """
    run_id = uuid4().hex[:12]
    capture = create_capture_session(run_id)
    input_plan_json = plan.export_to_json(capture.logs_dir / "input_plan.json")

    environment = {
        INPUT_PLAN_ENV: str(input_plan_json.resolve()),
        INPUT_TIMELINE_ENV: str((capture.logs_dir / "input_timeline.json").resolve()),
    }
    if memory_map_yaml is not None and memory_map_yaml.exists():
        memory_json = export_memory_map_json(memory_map_yaml, capture.logs_dir / "memory_map.json")
        environment[MEMORY_MAP_ENV] = str(memory_json.resolve())
        environment[STATE_TIMELINE_ENV] = str((capture.logs_dir / "state_timeline.json").resolve())

    frames_to_run = len(plan.expand_to_frames()) + CAPTURE_MARGIN_FRAMES
    request = MameRunRequest(
        game_shortname=profile.mame_driver,
        mame_binary=mame_binary,
        source_profile=profile,
        rom_path=rom_path,
        input_dir=capture.logs_dir,
        state_dir=capture.states_dir,
        snapshot_dir=capture.frames_dir,
        aviwrite_path=capture.video_dir / "capture.avi",
        autoboot_script=Path("scripts/mame_autoboot.lua"),
        environment=environment,
        frames_to_run=frames_to_run,
        extra_args=list(SPEED_ARGS),
        dry_run=False,  # MameRunRequest defaults to dry_run=True; the battery really captures.
    )
    result = run_mame(request)
    detail = ""
    if result.status == "preflight_failure" and result.preflight is not None:
        detail = "; ".join(issue.message for issue in result.preflight.issues)
    elif result.status == "execution_failure" and result.execution is not None:
        stderr = (result.execution.stderr or "").strip().splitlines()
        detail = stderr[-1] if stderr else f"returncode={result.execution.returncode}"
    return run_id, result.status, detail


def _extract_frames(run_id: str, ffmpeg_binary: str = "ffmpeg") -> int:
    """Extract PNG frames from the capture AVI (mirrors scripts/extract_frames.sh)."""
    run_root = PRIVATE_EVIDENCE_ROOT / f"run_{run_id}"
    avi = run_root / "video" / "capture.avi"
    out_dir = run_root / "frames" / "extracted_png"
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [ffmpeg_binary, "-i", str(avi), str(out_dir / "%04d.png"), "-y", "-loglevel", "error"],
        check=True,
    )
    return len(list(out_dir.glob("*.png")))


# ─────────────────────────────────────────────────────────────────────────────
# Trace + window
# ─────────────────────────────────────────────────────────────────────────────


def _load_trace_entries(run_id: str, plan_path: Path) -> list[dict]:
    # extract_run_trace enforces a PUBLIC output path (not under evidence/); the per-experiment
    # trace is intermediate, so write it to a temp file and read it back.
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "trace.json"
        extract_run_trace(run_id, plan_path, out)
        return json.loads(out.read_text(encoding="utf-8"))["trace"]


def detect_window(isolated_variable: str, entries: list[dict], declared: tuple[int, int]) -> tuple[int, int]:
    """Auto-detect the stable sub-window of the isolated activity (robust to timing jitter).

    Searches the declared window widened by WINDOW_SEARCH_MARGIN and returns the actual span
    of the relevant activity; falls back to the declared window if too little is found.
    """
    lo = max(0, declared[0] - WINDOW_SEARCH_MARGIN)
    hi = declared[1] + WINDOW_SEARCH_MARGIN

    if isolated_variable == "locomotion_velocity_x":
        frames = [e["frame"] for e in entries
                  if e["entity_type"] == "player" and e["state"] in _WALK_STATES and lo <= e["frame"] <= hi]
    elif isolated_variable == "jump_arc":
        frames = [e["frame"] for e in entries
                  if e["entity_type"] == "player" and e["state"] in _AIRBORNE_STATES and lo <= e["frame"] <= hi]
    elif isolated_variable == "projectile":
        frames = [e["frame"] for e in entries
                  if e["entity_type"] == "projectile" and lo <= e["frame"] <= hi]
    else:
        return declared

    if len(frames) < 2:
        return declared
    return (min(frames), max(frames))


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────


def _validate(plan: InputPlan, entries: list[dict], declared: tuple[int, int]) -> str | None:
    """Fail-fast, specific validation. Returns a concrete reason string, or None if OK."""
    exp = plan.experiment
    assert exp is not None

    players = [e for e in entries if e["entity_type"] == "player"]
    if not players:
        return "player never detected — boot may not have reached gameplay; re-run the capture"
    if max(e["frame"] for e in players) < declared[0]:
        return f"capture ended before the measurement window (max player frame < {declared[0]})"

    if exp.isolated_variable == "projectile":
        if not any(e["entity_type"] == "projectile" for e in entries):
            return "no projectile detected — fire not registered or projectile missed; re-run fire_stationary"
    elif exp.isolated_variable == "jump_arc":
        if not any(e["state"] in _AIRBORNE_STATES for e in players):
            return "no airborne frames — jump not detected; re-run jump_in_place"
    elif exp.isolated_variable == "locomotion_velocity_x":
        if not any(e["state"] in _WALK_STATES for e in players):
            return "no walking frames — movement not detected; re-run walk_right"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────────────


def calibrate_one(plan_path: Path, run_id: str) -> ExperimentVerdict:
    """Validate + calibrate a single already-captured experiment by run_id."""
    plan = load_input_plan(plan_path)
    if plan.experiment is None:
        return ExperimentVerdict(plan.plan_name, "RERUN", "plan has no experiment block")
    exp = plan.experiment
    declared = (exp.measurement_window.start_frame, exp.measurement_window.end_frame)

    try:
        entries = _load_trace_entries(run_id, plan_path)
    except Exception as exc:  # noqa: BLE001 — surface any extraction failure as actionable
        return ExperimentVerdict(exp.experiment_id, "RERUN", f"trace extraction failed: {exc}")

    reason = _validate(plan, entries, declared)
    if reason is not None:
        return ExperimentVerdict(exp.experiment_id, "RERUN", reason)

    window = detect_window(exp.isolated_variable, entries, declared)
    try:
        constants = calibrate_experiment(plan, entries, window_override=window)
    except ValueError as exc:
        return ExperimentVerdict(exp.experiment_id, "RERUN", f"calibration failed: {exc}")

    needs_review = any(c.needs_human_review for c in constants.values())
    status = "REVIEW" if needs_review else "PASS"
    reason = "low fit / consistency — inspect flagged constant" if needs_review else ""
    return ExperimentVerdict(exp.experiment_id, status, reason, constants)


def calibrate_battery(
    battery: tuple[Path, ...] = DEFAULT_BATTERY,
    *,
    rom: str = "gng",
    rom_path: Path | None = None,
    mame_binary: str = "mame",
    memory_map_yaml: Path | None = None,
    run_ids: dict[str, str] | None = None,
    output_path: Path = Path("specs/calibration/gng_experiment_calibration.yaml"),
    ffmpeg_binary: str = "ffmpeg",
) -> list[ExperimentVerdict]:
    """Run the battery and return per-experiment verdicts.

    If ``run_ids`` maps a plan filename stem to an existing run_id, that capture is reused
    (no MAME launch); otherwise the experiment is auto-captured.
    """
    run_ids = run_ids or {}
    profile = get_source_profile(rom)  # rom is the source-profile id (e.g. "gng" → driver "gngb")
    verdicts: list[ExperimentVerdict] = []
    all_constants: dict[str, ExperimentConstant] = {}

    for plan_path in battery:
        plan = load_input_plan(plan_path)
        stem = plan_path.stem
        run_id = run_ids.get(stem)

        if run_id is None:
            run_id, status, detail = _capture_experiment(
                plan, plan_path, profile, rom_path, mame_binary, memory_map_yaml
            )
            if status != "success":
                reason = f"capture failed (status={status})"
                if detail:
                    reason += f": {detail}"
                verdicts.append(ExperimentVerdict(
                    plan.experiment.experiment_id if plan.experiment else stem, "RERUN", reason))
                continue
            try:
                _extract_frames(run_id, ffmpeg_binary)
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                verdicts.append(ExperimentVerdict(
                    plan.experiment.experiment_id if plan.experiment else stem,
                    "RERUN", f"frame extraction failed: {exc}"))
                continue

        verdict = calibrate_one(plan_path, run_id)
        verdicts.append(verdict)
        all_constants.update(verdict.constants)

    if all_constants:
        write_experiment_calibration_yaml(all_constants, output_path)

    return verdicts


def format_verdict_table(verdicts: list[ExperimentVerdict]) -> str:
    lines = ["", "Calibration battery verdict", "=" * 60]
    for v in verdicts:
        lines.append(f"[{v.status:^6}] {v.experiment_id}")
        for name, c in v.constants.items():
            q = f" r2={c.fit_quality:.4f}" if c.fit_quality is not None else ""
            flag = " (needs_human_review)" if c.needs_human_review else ""
            lines.append(f"         {name} = {c.value_per_frame:.6f}/frame{q}{flag}")
        if v.reason:
            lines.append(f"         → {v.reason}")
    rerun = [v.experiment_id for v in verdicts if v.status == "RERUN"]
    review = [v.experiment_id for v in verdicts if v.status == "REVIEW"]
    lines.append("-" * 60)
    lines.append(f"PASS={sum(v.status=='PASS' for v in verdicts)} "
                 f"REVIEW={len(review)} RERUN={len(rerun)}")
    if rerun:
        lines.append(f"Re-run only: {', '.join(rerun)}")
    return "\n".join(lines)

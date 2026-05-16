# Boot Calibration Spike

## Status

Completed as MAP-11 on 2026-05-16.

## Goal

Reduce fragile hand-authored boot timing in the MAME harness without weakening the clean-room boundary.

The spike defines:

- what private evidence may be inspected during calibration
- what public calibration outputs are allowed
- what outputs are forbidden
- how a future calibration flow fits the existing deterministic execution path
- whether follow-up implementation requires an ADR

## Current Timing Problem

The current boot flow depends on fixed frame counts copied into multiple public places:

- [plans/gng_boot_only.yaml](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/plans/gng_boot_only.yaml)
- [plans/gng_gameplay.yaml](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/plans/gng_gameplay.yaml)
- [scripts/launch_manual_capture_autoboot.sh](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/scripts/launch_manual_capture_autoboot.sh)
- [docs/bootstrap.md](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/docs/bootstrap.md)
- [CLAUDE.md](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/CLAUDE.md)

Today those timings are:

- `noop` for about 950 frames before `insert_coin`
- `insert_coin` for 10 frames
- `noop` for 60 frames before `press_start`
- `press_start` for 5 frames
- `noop` for 480 frames before Arthur becomes controllable

This is brittle for four reasons:

1. The timing is game-specific and driver-specific, but it is duplicated across plans, scripts, and docs.
2. A small drift in attract-mode length, intro timing, or emulator setup can invalidate the authored waits.
3. The current workflow has no first-class calibration artifact; timing is embedded inside executable plans.
4. Any attempt to "improve" this naively can slip into public screenshots, frame references, or pixel-matching heuristics.

## Existing Files Involved

- [apps/mame-harness/cli.py](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/apps/mame-harness/cli.py)
- [apps/mame-harness/input_planner.py](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/apps/mame-harness/input_planner.py)
- [apps/mame-harness/guardrails.py](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/apps/mame-harness/guardrails.py)
- [scripts/launch_manual_capture_autoboot.sh](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/scripts/launch_manual_capture_autoboot.sh)
- [scripts/mame_autoboot.lua](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/scripts/mame_autoboot.lua)
- [plans/gng_boot_only.yaml](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/plans/gng_boot_only.yaml)
- [plans/gng_gameplay.yaml](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/plans/gng_gameplay.yaml)
- [docs/bootstrap.md](/Users/matiasleandrokruk/Documents/blackbox_mame_game_abstraction/docs/bootstrap.md)

The existing execution boundary must stay intact:

```text
public boot timing artifact
  -> generated public input plan YAML
  -> input_planner.py
  -> private per-frame JSON
  -> scripts/mame_autoboot.lua
  -> MAME
```

## Private Evidence Surfaces

The calibration flow may inspect these locally and privately only:

- `evidence/private/run_<id>/video/capture.avi`
- `evidence/private/run_<id>/frames/...`
- `evidence/private/run_<id>/logs/input_plan.json`
- private numeric observations derived from those frames during local calibration
- terminal-only operator confirmations gathered during a calibration session

These must remain private:

- screenshots
- extracted frames
- crop images
- video clips
- OCR text tied to frame captures
- raw per-frame visual metrics
- absolute paths into `evidence/private/`
- any public path or payload containing frame or crop locations

## Allowed Public Calibration Outputs

A future implementation may emit one public boot calibration artifact, plus optional generated plans derived from it.

Recommended public artifact location:

```text
profiles/games/<driver>/boot_calibration.yaml
```

Recommended public fields:

- `profile_type: boot_calibration`
- `profile_id`
- `source_profile`
- `game_id` or `driver`
- `method`
- `calibrated_at`
- optional `private_evidence_ref: private://<run_id>`
- `boot_phases`
- `recommended_plan_steps`
- `tolerances`
- `status`
- `notes`

Allowed public values are abstract only:

- semantic phase names such as `boot_idle`, `coin_ready`, `start_ready`, `intro_running`, `player_controllable`
- frame counts
- durations in milliseconds derived from frame counts
- bounded frame windows or tolerances
- confidence or review status enums
- opaque private references using `private://...`

Example shape:

```yaml
profile_type: boot_calibration
profile_id: gngb_default_boot
source_profile: gng
driver: gngb
method: hybrid_manual_private_signal
calibrated_at: 2026-05-16
private_evidence_ref: private://manual_boot_cal_01
boot_phases:
  coin_ready:
    first_safe_frame: 950
    tolerance_frames: 20
  start_ready:
    first_safe_frame: 1020
    tolerance_frames: 20
  player_controllable:
    first_safe_frame: 1505
    tolerance_frames: 30
recommended_plan_steps:
  - action: noop
    frames: 950
  - action: insert_coin
    frames: 10
  - action: noop
    frames: 60
  - action: press_start
    frames: 5
  - action: noop
    frames: 480
status: human_review_required
notes:
  - calibrated from private boot session
```

## Forbidden Public Outputs

A follow-up implementation must reject any attempt to publish:

- screenshots or screenshot paths
- videos or video paths
- frame paths
- crop paths
- per-frame image hashes
- OCR dumps from title or credit screens
- raw visual feature vectors
- binary evidence files
- public traces that enumerate private frame-by-frame observations
- any pixel comparison report

The public artifact must stay at the same abstraction level as existing plans and specs: timing, semantic state names, and opaque provenance only.

## Candidate Strategies

### 1. Fixed Delay Baseline

Description:
- keep hand-authored waits only

Assessment:
- acceptable as a fallback
- does not solve duplication or recalibration workflow

Decision:
- not sufficient as the target design

### 2. Visual Diff Stabilization

Description:
- compare frame regions to detect that boot or intro has "settled"

Assessment:
- drifts toward pixel comparison
- encourages game-specific image heuristics
- creates pressure to expose raw visual diagnostics publicly

Decision:
- rejected for the first implementation

### 3. Credit / Start Prompt Detection

Description:
- detect the coin prompt or 1P start prompt from private visual evidence

Assessment:
- possible in principle if kept private
- still requires game-specific visual classification or OCR-like logic
- too much surface area for a first calibration feature

Decision:
- defer

### 4. Controllability Probe

Description:
- after `press_start`, inject a short low-risk probe action and detect whether the player state now responds

Assessment:
- compatible with clean-room rules if detection stays private and emits only timing markers publicly
- can build on existing numeric trace machinery rather than pixel comparison
- still requires careful handling to avoid false positives during auto-animation or scripted intro motion

Decision:
- keep as a future private-only automation option

### 5. Hybrid Manual Confirmation

Description:
- run a private calibration session
- prompt the operator to confirm semantic checkpoints
- emit only abstract timing markers publicly

Assessment:
- lowest-risk first implementation
- no screenshots or pixel matching required
- fits the current runtime without rewriting the runner, Lua injector, or input planner

Decision:
- recommended MVP

## Recommended First Implementation

Use a hybrid manual-confirmation workflow with a public calibration profile and no new public visual outputs.

Recommended command shape:

```text
apps/mame-harness/.venv/bin/python apps/mame-harness/cli.py calibrate-boot \
  --source-profile gng \
  --driver gngb \
  --out profiles/games/gngb/boot_calibration.yaml
```

Recommended stages:

1. Run existing preflight checks and verify local bootstrap config.
2. Launch a private calibration run using the existing MAME runner and Lua injection path.
3. Ask the operator to confirm semantic milestones only:
   - coin prompt ready
   - start prompt ready
   - player controllable
4. Store all raw evidence and any detailed observation logs under `evidence/private/run_<id>/`.
5. Write one public `boot_calibration.yaml` artifact containing only abstract timing windows and recommended plan steps.
6. Optionally generate a public boot plan from that artifact and validate it through `input_planner.load_input_plan()`.

This preserves ADR-009 determinism because the executable artifact remains a normal public input plan. Calibration only changes how that plan is derived.

## Guardrails And Validation Strategy

Public calibration outputs must pass all existing public-writer constraints:

- `ensure_public_output_path`
- `ensure_no_private_paths`
- no blocked directory names such as `frames`, `video`, or `crops`
- no blocked evidence extensions such as `.png`, `.avi`, or `.sav`

Follow-up implementation tests should cover:

- no public calibration artifact can contain `evidence/private/`
- no public calibration artifact can contain `/frames/` or `/crops/`
- no calibration output path can use blocked media extensions
- generated plan YAML stays parseable by `input_planner.load_input_plan()`
- calibration payload schema rejects per-frame visual arrays and path-bearing fields
- any optional provenance field uses `private://<run_id>` only

## Risks And False Positives

- Manual confirmation still depends on user discipline; operator prompts must be precise and limited.
- A controllability probe can misfire if intro animation resembles player-controlled motion.
- Game-specific boot flows may need different semantic checkpoints, so the profile contract must allow phase names to stay semantic rather than hardcoded to GNG strings.
- If calibration writes verbose debugging data publicly, it will become a new leakage surface immediately.

## ADR Decision

Yes. Follow-up implementation needs a new ADR because it introduces a new reusable public artifact contract and a new private-to-public calibration workflow that future games can replicate.

That ADR is [ADR-018](./adr/ADR-018-boot-calibration-public-contract.md).

## Recommended MVP Summary

The MVP should be a top-level `calibrate-boot` CLI command that performs a private run, captures semantic checkpoint confirmations, writes a public `boot_calibration.yaml`, and leaves the existing plan expansion and Lua execution path unchanged.

# AGENTS.md

## Objective

Build a clean-room black-box game abstraction framework.

The system observes games through MAME, captures private evidence, infers abstract mechanics, creates new asset recipes, and supports a React Native reimplementation.

## Agent Workflow Guide (authoritative for process)

`docs/playbooks/AGENT_WORKFLOW_GUIDE.md` is the authoritative source for agent-facing
**process** — workflow, task presentation, planning discipline, reasoning/effort grading,
model selection (Codex + Claude Code), ADR propagation, testing/commit rules, handoff format,
and language policy. It overrides this file on those process topics; this file applies for any
topic it does not cover. The clean-room guardrails (see Forbidden / Allowed below) are
inviolable and are never overridden.

## Forbidden

Do not:

- add ROMs
- add screenshots
- add videos
- add original sprites
- add audio captures
- add save states
- implement sprite ripping as a public output
- implement image-to-image transformation of original sprites
- create a clone-specific implementation

## Allowed

You may implement:

- MAME command runner
- dry-run command builder
- metadata capture
- frame manifest loading
- private evidence path management
- computer vision interfaces
- behavior inference interfaces
- abstract mechanics specs
- asset recipe generator
- originality guard placeholders
- React Native game engine scaffold

## Output Rule

All public output must be abstract.

Use this transformation:

```text
MAME observation
→ redacted metadata
→ abstract mechanics
→ new theme
→ new original assets
→ independent mobile game
```

## Test Requirements

Add tests for:

- private evidence isolation
- no generated asset uses original image paths
- no public spec includes frame paths or crop paths
- no output directory accepts ROM/video/screenshot extensions
- asset recipes include prohibited similarity rules

## Implementation Style

- Small commits
- Simple typed modules
- No unnecessary ML dependencies in early phases
- Prefer interfaces and placeholders over speculative complexity
- Do not use TDD by default in this project. Implement the change first, then add focused regression tests for the completed behavior when the task requires test coverage.

## Python Environment

- Always use the project virtualenv.
- Never invoke bare `python`, `python3`, or `pytest` for repo work.
- Use `apps/mame-harness/.venv/bin/python` and `apps/mame-harness/.venv/bin/pytest`, or activate `apps/mame-harness/.venv/` first.
- The project runtime is Python 3.11 from the harness virtualenv. System interpreters may be a different version and are not valid for execution or test verification.

## Architecture Decision Records

Read the ADRs in `docs/adr/` before analyzing or implementing any feature that touches the boundaries they describe. The ADRs are the authoritative record of why the system is structured as it is.

### ADR Index

| ADR | Decision | Relevant surface |
|-----|----------|-----------------|
| ADR-001 | Four-layer clean-room architecture with programmatic enforcement | Any new module or package |
| ADR-002 | `private://` URI scheme for evidence session references | Any code that writes run metadata |
| ADR-003 | Three-layer public output blocklist (extension + directory + path marker) | Any public file writer |
| ADR-004 | Structured result objects in the MAME runner — no exceptions for operational outcomes | `mame_runner.py`, CLI |
| ADR-005 | Source profile pattern; `gng.zip` must use MAME driver `gngb` | Any game profile or preflight work |
| ADR-006 | Vision layer emits numeric output only — never frame or crop paths | `packages/vision/`, entity candidates |
| ADR-007 | Every asset recipe must embed five prohibited similarity rules and `human_review_required: true` | `packages/asset-factory/` |
| ADR-008 | Behavioral validation uses abstract traces — never pixel or screenshot comparison | `packages/validation/` |
| ADR-009 | Input plans are deterministic YAML sequences — same plan produces same per-frame output | `input_planner.py`, `plans/` |
| ADR-010 | Public original game definition layer between abstract mechanics and RN product work | T12 game definition artifacts, RN product direction |
| ADR-011 | Mechanics-to-scenario transformation and originality validation | T12 encounter grammar, scene recipes, validation gates |
| ADR-012 | Entity signature-based player identification; multi-region FrameDiffer; ArthurTracker | `packages/vision/frame_differ.py`, `packages/vision/arthur_tracker.py`, `packages/vision/trace_extractor.py` |
| ADR-013 | OpenCV as replaceable vision backend; MOG2 background subtraction; HUD masking; player gap tolerance | `packages/vision/frame_differ.py`, `packages/vision/gng_vision_config.py`, `packages/vision/trace_extractor.py` |
| ADR-014 | Layered input mapping compatibility layer compiled to the existing input-plan pipeline | `input_planner.py`, mapping profiles/compiler, future `map` CLI commands |
| ADR-015 | SDL GameControllerDB importer to `device_profile` YAML with explicit unsupported-control warnings | SDL mapping importer, `map import-sdl`, device profile generation |
| ADR-016 | RetroArch autoconfig importer to `device_profile` YAML with fixed A/B convention and explicit unsupported-field warnings | RetroArch mapping importer, `map import-retroarch`, device profile generation |
| ADR-017 | Prompt-based `map init` wizard to create `device_profile` YAML with required-control enforcement | `map init`, wizard prompts, device profile generation |
| ADR-018 | Boot calibration emits abstract timing markers only | boot calibration artifact, calibration CLI, generated boot plans |
| ADR-019 | Human-validated calibration candidates pattern (picker → accept/reject → calculator) | `apps/mame-harness/visual_jump_picker.py`, future calibration pickers, `<picker>_candidates.json` private artifacts |
| ADR-020 | Cross-frame projectile continuity for in-flight velocity calibration | projectile tracking, projectile picker, projectile calibration output |
| ADR-021 | Generalized `EntityTracker` with per-type `EntitySignature`; persistent enemy IDs across frames; `ArthurTracker` becomes a wrapper | `packages/vision/entity_tracker.py`, `packages/vision/arthur_tracker.py`, `packages/vision/trace_extractor.py`, `specs/calibration/gng_enemy_signatures.yaml` |
| ADR-022 | Scroll-aware vision pipeline: `ScrollDetector` + MOG2 reset on scroll end with warmup window; resolves ADR-013 MOG2 scroll-reset Known Gap | `packages/vision/scroll_detector.py`, `packages/vision/frame_differ.py`, `packages/vision/gng_vision_config.py`, `packages/vision/trace_extractor.py` |
| ADR-023 | Ground-truth input timeline: MAME Lua records effective per-frame input (injected plan OR human) to a private `input_timeline.json`; authoritative source for input-driven events, CV inference demoted to fallback | `scripts/mame_autoboot.lua`, `apps/mame-harness/input_timeline.py`, `packages/schemas/input_timeline.schema.json` |
| ADR-024 | Designed isolation-experiment calibration: each experiment plan isolates one mechanic (embedded `experiment` block, structurally-enforced isolation) so constants are measured with no human picker; default method, ADR-019 demoted to fallback | `packages/schemas/experiment_plan.schema.json`, `apps/mame-harness/input_planner.py`, `plans/sequences/gng_exp_*.yaml` |
| ADR-026 | Internal-state (RAM) observation clean-room boundary (**Accepted**, constrained): MAME RAM may be read via Lua using community cheat-DB addresses as a private measurement/verification accelerator only; memory is not the published source of truth (clause 4); public output stays numbers-only | `scripts/mame_autoboot.lua`, `apps/mame-harness/guardrails.py`, memory-tap calibration (T20.5/T20.6) |
| ADR-028 | Memory-mapping-first game integration: the MAME Lua memory tap (ADR-026) becomes the **default** entity position/state source; CV (ADR-012/013/021/022) and pickers (ADR-019/020) demoted to fallback; declarative per-game integration bundle (typed variables + scenario events + rom.sha + savestate anchor) + guided address-search; calibration via ADR-024 over the RAM state timeline; deprecates unauthored ADR-025/027 and tasks T20.7–T20.10 | memory tap + bundle (T30.2–T30.5), `apps/mame-harness/guardrails.py`, `docs/plans/memory_mapping_first_rearchitecture_plan.md` |

> **ADR-028 (2026-06-18):** ADR-012, ADR-013, ADR-019, ADR-020, ADR-021, ADR-022 are demoted to *fallback* by ADR-028 (memory-mapping-first). The memory tap (ADR-026) is the default position/state source.

### Known Gaps (verify before implementing)

These are documented open limitations. If your task touches one of these areas, read the referenced ADR and treat the gap as a risk to be assessed before marking the task complete.

- **ADR-002 / redaction**: `_redact_command_paths` catches `evidence/private/` as a literal substring only. Symlink-resolved or `~`-expanded absolute paths are not caught.
- **ADR-003 / blocklist**: `BLOCKED_PUBLIC_SUFFIXES` is static. New evidence types require manual additions to `guardrails.py`.
- **ADR-004 / stdout-stderr**: `MameExecution.stdout` and `stderr` are written verbatim to public metadata. Subprocess output may contain local machine paths — redaction is not yet implemented.
- **ADR-004 / status type**: `MameRunResult.status` is a plain `str`. Typos are not caught at definition time.
- **ADR-005 / driver contract**: Preflight has a hardcoded `if profile.profile_id == "gng"` branch. Adding a second game requires a new branch, not a generic contract.
- **ADR-006 / PGM format**: Only P2 ASCII PGM is supported. P5 binary PGM is not. MAME snapshot compatibility needs verification.
- **ADR-012 / player signature**: `ArthurSignature` defaults are calibrated for GNG at 256×224. T10.7 added `max_frame_jump_px` to reject implausible player teleports, but crouch/death animations can still create short `find_arthur` gaps.
- **ADR-013 / MOG2 scroll reset**: Background model becomes invalid on horizontal camera scroll (stage 2+). Stage 1 runs unaffected. Tracked as Known Gap until T12 scope is defined.
- **ADR-013 / enemy tracking**: Cross-frame enemy identity continuity is not implemented. Enemy entities remain ephemeral per-frame IDs (`enemy_a_{frame}`).
- **ADR-007 / theme variants**: `suggested_new_theme_variants` are the same three strings for every entity. Should be varied or mechanics-derived.
- **ADR-008 / movement tolerance**: Default tolerance (1.0 unit) is a placeholder. Correct value requires real captured evidence to calibrate.
- **ADR-008 / state vocabulary**: State and event strings must match exactly. No canonical vocabulary is enforced — naming drift causes false mismatches.

## Documentation Vault

`docs/obsidian/` is an Obsidian vault with module notes, ADR summaries, and the GNG integration plan. Use these notes to load architectural context quickly before reading source code:

- `00 - Project Overview.md` — pipeline, repo layout, current phase
- Module notes: `Guardrails`, `MAME Runner`, `Vision Layer`, `Asset Factory`, `Behavioral Validation`, `Source Profile`, `Preflight`, `Input Plan`, `React Native Prototype`, `Public Original Game Definition Layer`
- `GNG Integration Plan.md` — T01–T11 status table and exit criteria

## Analysis Protocol

Before proposing or starting any implementation:

1. Identify which ADR(s) govern the module or boundary being touched (see ADR Index above).
2. Read those ADRs in full — context, decision, consequences, and known limitations.
3. Check the Known Gaps list for open risks in the target area.
4. Read the corresponding module note in `docs/obsidian/` if one exists.
5. If the work crosses the private/public boundary, touches asset recipe originality, or changes the validation method, raise the reasoning grade to `High` regardless of implementation size.

## New Feature Documentation Requirements

Every new feature that introduces an architectural decision must be documented before implementation begins.

A decision qualifies as architectural if it:
- introduces a new module, package, or layer
- changes how the private/public boundary is enforced or traversed
- changes how public outputs are written, redacted, or validated
- changes the asset recipe originality contract
- changes the behavioral validation method
- introduces a new external dependency or integration point
- establishes a new pattern that future tasks will replicate

When a feature qualifies:

1. Create a new ADR in `docs/adr/` following the existing format (Status, Date, Context, Decision, Consequences, Alternatives Considered, Related).
2. Create a corresponding summary note in `docs/obsidian/` with the same wikilink conventions as existing ADR notes.
3. Add the new ADR to the ADR Index table in both `CLAUDE.md` and `AGENTS.md`.
4. Add the new Obsidian note to the vault index in `docs/obsidian/README.md` and to the ADR index table in `docs/obsidian/00 - Project Overview.md`.
5. If the feature resolves a Known Gap, remove or update the gap entry in both `CLAUDE.md` and `AGENTS.md`.

ADR numbering: use the next available integer after the highest existing ADR number. Do not reuse numbers.

This documentation must be produced as part of the planning phase, before any implementation task begins.

## Documentation Update Requirement

Documentation must always be updated as part of the same change when task execution alters the documented workflow, operating instructions, assumptions, constraints, or accepted procedure.

- Do not leave task docs, handoff docs, or other operator-facing instructions stale after changing the effective process in implementation or in agent/user instructions.
- If a live execution decision changes how a task should be performed, update the corresponding task file before presenting the adjusted procedure as settled.
- When a change affects both task execution and handoff continuity, update both the task doc and the active handoff doc in the same workstream.

## Planning Requirements

When a user asks for a plan, the plan must define tasks explicitly and in dependency order.

Every plan must include:

- tasks ordered by execution dependency
- an explicit dependency statement for each task
- the required reasoning grade for each task
- the expected effort level for each task
- the recommended model for each task

Use the following minimum planning fields per task:

- Task ID and title
- Objective
- Scope
- Out of scope
- Dependencies
- Reasoning grade: `Low | Medium | High`
- Effort grade: `Low | Medium | High`
- Recommended model
- Acceptance criteria

Planning rules:

- Do not present tasks as an unordered backlog when execution order matters.
- Do not omit dependency order when one task blocks another.
- Do not omit reasoning grade or effort grade.
- Recommended model must reflect real task difficulty and risk.
- If a task crosses a clean-room or public-output boundary, bias reasoning grade upward.
- Once a task or subtask has been assigned a reasoning grade or effort grade, do not change that cataloging implicitly later.
- A previously assigned reasoning grade or effort grade may only be changed if the scope, dependency structure, or risk profile has materially changed.
- Any such recataloging must be stated explicitly and must include a short justification describing exactly what changed and why the new grade is warranted.
- Any plan presentation or task handoff must include a `Reference documents` section.
- `Reference documents` must include, at minimum: the current task file, the parent plan file, `README.md`, `AGENTS.md`, and `CLAUDE.md`.
- `Reference documents` must also include every ADR that governs the task's boundary (see ADR Index above).
- `Reference documents` must include the relevant `docs/obsidian/` module note if one exists.
- Add any domain-specific docs needed to understand the task safely before execution.

## Codex Task Presentation Requirement

When presenting a task to the user, any `Recommended model` guidance must be expressed using models actually available in Codex for the current session.

- Do not present inherited model labels from other agent ecosystems (for example `Haiku` or `Sonnet`) as the operative recommendation.
- If a task file contains legacy or external model labels, treat them as historical context only and translate or flag them as outdated when presenting the task.
- Reasoning presentation must also be framed in Codex terms for the current session rather than external agent naming conventions.

## Task Presentation Rule

Do not present a task as ready for execution, and do not present a handoff prompt for a task, until a separate task file exists for that task and is sufficiently defined for another agent to continue without ambiguity.

Minimum required contents for that separate task file:

- Objective
- Scope
- Out of scope
- Dependencies
- Reasoning grade
- Effort grade
- Recommended model
- Acceptance criteria
- Reference documents

If the task file does not exist yet, create or complete it first. Only after that may the task or handoff prompt be presented.

# AGENTS.md

## Objective

Build a clean-room black-box game abstraction framework.

The system observes games through MAME, captures private evidence, infers abstract mechanics, creates new asset recipes, and supports a React Native reimplementation.

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

### Known Gaps (verify before implementing)

These are documented open limitations. If your task touches one of these areas, read the referenced ADR and treat the gap as a risk to be assessed before marking the task complete.

- **ADR-002 / redaction**: `_redact_command_paths` catches `evidence/private/` as a literal substring only. Symlink-resolved or `~`-expanded absolute paths are not caught.
- **ADR-003 / blocklist**: `BLOCKED_PUBLIC_SUFFIXES` is static. New evidence types require manual additions to `guardrails.py`.
- **ADR-004 / stdout-stderr**: `MameExecution.stdout` and `stderr` are written verbatim to public metadata. Subprocess output may contain local machine paths — redaction is not yet implemented.
- **ADR-004 / status type**: `MameRunResult.status` is a plain `str`. Typos are not caught at definition time.
- **ADR-005 / driver contract**: Preflight has a hardcoded `if profile.profile_id == "gng"` branch. Adding a second game requires a new branch, not a generic contract.
- **ADR-006 / vision stub**: The vision pipeline is a placeholder. Entity candidates are synthetic. Real pixel analysis is deferred to a later phase.
- **ADR-012 / multi-region + ArthurTracker**: Multi-region FrameDiffer and ArthurTracker are not yet implemented (T10.5 in progress). Until T10.5-E is complete, `extract_trace` produces one `TraceEntry` per frame aggregate, not one per entity. T10.5-C.3/C.4 (per-entity state isolation and spawn/die rewrite) are the highest-risk steps — reason carefully before touching `prev_state_by_entity` or `prev_seen_by_id`.
- **ADR-006 / PGM format**: Only P2 ASCII PGM is supported. P5 binary PGM is not. MAME snapshot compatibility needs verification.
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

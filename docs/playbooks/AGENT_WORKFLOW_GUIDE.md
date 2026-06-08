# Agent Workflow Guide

> **Status:** Authoritative for agent-facing *process* in this repository — workflow,
> task presentation structure, planning discipline, reasoning/effort grading, model
> selection, ADR propagation, testing and commit rules, handoff format, and language
> policy. It applies equally to **Codex** and **Claude Code** agents.
>
> **Authority order.** This guide overrides `CLAUDE.md` (project and global) and
> `AGENTS.md` on the *process* topics it covers. `CLAUDE.md` / `AGENTS.md` apply for
> any topic not covered here. The one exception that this guide can **never** override
> is the clean-room boundary: the Critical Guardrails in `CLAUDE.md` and the governing
> ADRs are inviolable. On any legal / private-vs-public / originality question, the
> guardrails win.

## 0. Project context (read before anything)

This is a **clean-room black-box game abstraction framework**. It observes a game
running in MAME, keeps the raw evidence private, and emits only abstract, numeric,
clean-room-safe artifacts that can drive an independent implementation with original
art and identity.

```text
observe -> capture (private) -> abstract spec (public) -> new assets -> independent implementation
```

Every decision an agent makes is downstream of one rule: **only abstract data crosses
the private→public boundary.** If a change could move expressive content (sprites,
audio, screenshots, ROM bytes, crops, frame paths) across that boundary, stop and
escalate before proceeding.

## 1. Non-negotiable clean-room guardrails

Never commit or emit as public output: ROM files, original sprites, original audio,
screenshots, gameplay video, save states, copyrighted visual crops, or
image-to-image derivatives of original sprites.

Allowed public outputs: abstract mechanics specs, entity archetypes, motion/timing
metadata, approximate collision metadata, asset recipes for *new* original assets,
behavioral validation cases, and the React Native implementation that uses new assets.

Enforcement is structural, not advisory:
- `apps/mame-harness/guardrails.py` checks every public write (extension blocklist,
  directory blocklist, recursive payload scan for private path markers).
- Keep `evidence/private/` gitignored. Public artifacts live under `specs/` and must
  pass `ensure_no_private_paths` at write time.
- Any module that writes files **must** have a test proving it does not write private
  visual evidence into tracked directories.

When in doubt, read the ADR that governs the boundary (see §9) before touching code.

## 2. Python environment (hard requirement)

Always use the project virtualenv. Never invoke bare `python`, `python3`, or `pytest`
— the system interpreter may be 3.9 or 3.14 and breaks `dataclass(slots=True)`.

- Venv: `apps/mame-harness/.venv/` (Python 3.11).
- Activate: `source apps/mame-harness/.venv/bin/activate`, or prefix directly:
  `apps/mame-harness/.venv/bin/pytest`, `apps/mame-harness/.venv/bin/python`.

## 3. Mandatory workflow before implementing

1. **Analyze** — read context, dependencies, affected files, governing ADRs, and the
   relevant `docs/obsidian/` module note (see §4).
2. **Plan** — create `docs/plans/<plan-name>.md` with: objective, affected files,
   design decisions, module dependencies, and the ordered task list (see §8).
3. **Tasks** — create one task file per task under `docs/tasks/<group>/` with the
   fields required in §5. The task list must be **topologically ordered** by execution
   dependency.
4. **Present and wait** — show the plan and the task list and wait for **explicit
   approval** before starting implementation. This is required **even if a plan was
   approved in a prior session.** Never auto-start on prior approval. The only
   exception is the user explicitly saying "proceed without asking" or equivalent.
5. **Implement** — one task at a time, in the defined order. Work on the approved task
   only.
6. **Mark progress** — update the task/plan document after each completed task. The
   plan doc is the crash-safe progress ledger; treat it as your durable TODO list so
   work can resume after a crash.
7. **Sync status artifacts before reporting completion** — before telling the user a
   task is done, update every materially affected status document in the same pass
   (task file, plan file, dependent tasks, ADR status/index entries). Completion is
   not valid until those documents are consistent.
8. **Summarize before switching** — show a summary of the completed task before moving
   to the next, and request approval for the next task.

## 4. Analysis requirements (before proposing changes to any module)

1. Read the ADR(s) that govern the module's boundary (ADR Index in `CLAUDE.md` /
   `AGENTS.md`).
2. Check the **Known Gaps** list in `CLAUDE.md` / `AGENTS.md` for open risks in that
   area; treat a relevant gap as a risk that may need to be resolved before the task
   can be marked complete.
3. Read the corresponding `docs/obsidian/` module note if one exists.
4. If the change touches a clean-room boundary (private/public separation, asset
   recipe originality, validation method), **bias the reasoning grade upward.**

## 5. Task definition requirements

A task is not ready to present (and no handoff prompt may be produced for it) until a
separate task file exists that another agent could execute without ambiguity. The file
must include at least:

- Task ID and title
- Objective
- Scope
- Out of scope
- Dependencies (explicit)
- Reasoning grade: `Low | Medium | High`
- Effort grade: `Low | Medium | High`
- Recommended model (see §7)
- Acceptance criteria
- Reference documents (see below)
- A short agent handoff prompt (see §11)

**Reference documents** must include, at minimum: the task file itself, the parent
plan file, `README.md`, `AGENTS.md`, `CLAUDE.md`, this guide, any ADR that governs the
task's boundary, and the relevant `docs/obsidian/` module note if one exists.

**Behavioral examples for development tasks.** When a task writes or modifies code, the
task file must include concrete, testable examples written in behavioral terms (not
implementation terms), each with a stable ID:
- at least one **happy path** (`HP-1`, `HP-2`, …) — a success flow the task must
  implement or preserve;
- at least one **edge case** (`EC-1`, `EC-2`, …) — a boundary, invalid-input, or
  clean-room-violation flow the task must handle or reject.

Example (clean-room flavored):
- `HP-1: scripted run + valid input timeline -> trace events match the injected plan exactly`
- `EC-1: public writer receives a dict containing an "evidence/private/..." value -> ValueError before the file is opened`

Skip the example requirement for docs-only, config-only, or pure-planning tasks, and
for **exploratory / calibration** tasks where this project deliberately implements
first and adds regression tests afterward (see §10).

## 6. Per-task discipline

**Pre-task presentation for development tasks** must include:
- **Happy paths considered** — the success flows the agent will implement and verify
  (derived from the `HP-#` cases).
- **Edge cases considered** — the boundary/failure/clean-room conditions to handle
  (derived from the `EC-#` cases).
- **Diagram** — a compact Mermaid diagram showing the flow, boundary, dependency
  direction, or state transition the task relies on. Use the smallest diagram that
  makes the implementation shape obvious. Required for development tasks even when the
  architecture is unchanged.

Skip these for docs-only, config, or planning tasks unless the user asks.

**Post-task summary for development tasks** must include:
- **Happy paths covered** and **Edge cases covered**, each with **code evidence** —
  the concrete files, functions, and tests that prove the claimed coverage, with a
  one-line explanation of what each reference demonstrates.
- The exact test command(s) run on the venv and their result.

Treat status-document synchronization as part of the task, not follow-up cleanup. Do
not report a task complete while any governing status document still shows stale state.

## 7. Reasoning, effort, and model selection

This project grades two axes per task and resolves a recommended model from them. It
does **not** use a separate elapsed-time estimate; effort reflects implementation +
validation cost, reasoning reflects ambiguity, cross-module impact, and clean-room risk.

### Reasoning grade

| Grade | Meaning |
|-------|---------|
| Low | Bounded local change, limited ambiguity, mostly mechanical. |
| Medium | Cross-module reasoning, contract alignment, moderate ambiguity, test design. |
| High | Architectural or boundary-sensitive work, evidence interpretation, abstraction design, or legal/clean-room risk. |

Clean-room boundary work always biases the reasoning grade upward.

### Effort grade

`Low | Medium | High`. The descriptive S/M/L/XL scale below is an aid for articulating
effort; map it onto the `Low | Medium | High` grade used in task files.

| Level | Description | Example |
|-------|-------------|---------|
| S | Mechanical — transcription, copy, merge. No inference. | Config from an explicit spec. |
| M | Moderate — understand contracts, design logic, anticipate edge cases. | Boundary/guardrail tests. |
| L | High — multiple subsystems, architecture decisions. | Deterministic calibrator with regression tests. |
| XL | Very high — unpredictable external tooling, iterative diagnosis. | New vision backend / tracking pipeline. |

Once a grade is assigned to a task, do not change it implicitly. A grade may change
only if scope, dependency structure, or risk profile materially changed — state the
change explicitly with a short justification.

### Capability tier → concrete model

Separate the **capability decision** from the **concrete model resolution**. Capability
is derived from reasoning + effort; the concrete model is the best current vendor model
for that tier in the active agent environment.

| Capability tier | Use for | Claude Code | Codex (OpenAI) |
|-----------------|---------|-------------|----------------|
| Economy | Low reasoning, mechanical (S) | Haiku (`claude-haiku-4-5`) | current OpenAI economy/mini reasoning model |
| Balanced | Medium reasoning, standard implementation (M) | Sonnet (`claude-sonnet-4-6`) | current OpenAI balanced model |
| Premium | High reasoning, architecture, clean-room boundary, synthesis (L/XL) | Opus (`claude-opus-4-8`) | current OpenAI flagship reasoning model |

Resolution rules:
- Every task presentation gives **both** a Codex and a Claude Code recommendation,
  derived from the same reasoning/effort grades. Do not present only one vendor unless
  the task is scoped to a single agent environment.
- The Claude model IDs above are current as of this guide's date; if asked for the
  "latest/best" model, verify against official Anthropic docs first.
- For Codex/OpenAI, resolve the tier to the current vendor model — verify against
  official OpenAI docs rather than relying on a possibly-stale ID. Prefer naming the
  capability tier plus the resolved ID over a stale pinned guess.
- If a task file pins a model, that is a task-local override; present it as such and do
  not silently swap it.

### Thinking / extended-reasoning mode

Activate extended reasoning for the premium/balanced model only when the task requires
multi-step reasoning that cannot be validated incrementally — architecture trade-offs
with more than two interacting constraints, novel algorithm design, evidence
interpretation across frames, or diagnosis of non-deterministic failures. Do **not**
activate for: writing tests for already-specified logic, config edits, doc updates, or
any task whose strategy is fully pre-defined.

### State it in the task presentation

```
| Reasoning grade  | <Low|Medium|High> + one-line rationale            |
| Effort grade     | <Low|Medium|High>                                 |
| Claude Code      | <resolved model> — thinking <On/Off>              |
| Codex            | <resolved model / tier — verify current ID>       |
```

## 8. Planning requirements

When asked for a plan, define the work as ordered tasks, not a loose idea list. The
task list must be topologically ordered: a task that blocks later work appears before
its dependents. Each planned task carries dependency order, explicit dependencies,
reasoning grade, effort grade, recommended model, and acceptance criteria.

The plan file (`docs/plans/<name>.md`) records: objective, scope / out of scope,
dependency rationale, affected modules, deliverables, exit criteria, a Progress Log
used as the crash-safe ledger, and a Reference documents section (same minimum set as
§5).

## 9. ADR creation and change propagation

A decision is **architectural** (and needs an ADR authored during the planning phase,
before implementation) if it: introduces a new module/package/layer; changes how the
private/public boundary is enforced or traversed; changes how public outputs are
written, redacted, or validated; changes the asset-recipe originality contract; changes
the behavioral-validation method; introduces a new external dependency/integration; or
establishes a pattern future tasks will replicate.

**ADR numbering:** next integer after the highest existing ADR. Never reuse numbers.

This repository's ADR record is mirrored across several canonical docs. When you
create or change an ADR, propagate in the **same** change:

| ADR change | Update in the same change |
|---|---|
| **New ADR** | the ADR file in `docs/adr/`; a summary note in `docs/obsidian/`; the ADR Index table in **both** `CLAUDE.md` and `AGENTS.md`; the vault index in `docs/obsidian/README.md`; the ADR index table in `docs/obsidian/00 - Project Overview.md`; remove/update any **Known Gap** the ADR resolves (in both `CLAUDE.md` and `AGENTS.md`); the affected plan/task files |
| **Status change** (`Proposed`→`Accepted`→`Superseded`/`Deprecated`) | the ADR file `Status`; the Obsidian note status line; the ADR Index rows in `CLAUDE.md`, `AGENTS.md`, `docs/obsidian/README.md`, `docs/obsidian/00 - Project Overview.md`; every plan/task doc that cites the ADR as authority |
| **Scope or decision change** | every canonical doc whose prose describes that decision (semantic — human review owns whether the prose is still accurate); the index annotations; `README.md` if outward-facing |
| **Supersession** | both ADRs' `Status`; the index rows for each; every doc citing the superseded ADR |

**Deletion rule.** An `Accepted` ADR is part of the auditable record and must **not** be
deleted — mark it `Superseded by ADR-NNN` or `Deprecated`. A `Proposed` ADR that was
never adopted may be deleted only after every reference is removed in the same change.
Renumbering is delete + create and must update all references atomically. Per repo
policy, **ask for confirmation before deleting anything.**

**Definition of done for any ADR change:**
- [ ] ADR file `Status` updated; Context/Decision/Consequences/Alternatives/Related present.
- [ ] Obsidian note added/updated.
- [ ] ADR Index rows consistent across `CLAUDE.md`, `AGENTS.md`, `docs/obsidian/README.md`,
      `docs/obsidian/00 - Project Overview.md`.
- [ ] Any resolved Known Gap removed/updated in `CLAUDE.md` and `AGENTS.md`.
- [ ] No plan/task doc cites a missing or contradicted ADR.

## 10. Testing and commit rules

- **Do not use TDD by default in this project.** Implement first, verify behavior, then
  add focused regression tests for the finished behavior when tests are required. (This
  is a deliberate project-level override of the global TDD preference, and applies in
  particular to exploratory and calibration work.)
- **Guardrail tests are mandatory:** every module that writes files must have a test
  proving it writes no private visual evidence into tracked directories, and every
  asset recipe must embed its originality constraints.
- Prefer real backends over mocks; the pipeline should run on real private evidence and
  real public artifacts, not mocked connectivity.
- Run tests on the venv: `apps/mame-harness/.venv/bin/pytest -q`.
- **Never commit if any test is broken.** Run the full suite before commit and push.
  (`NO SE DEBE HACER COMMIT SI HAY TESTS ROTOS`.)
- **Ask for confirmation before deleting anything**, and before overwriting a tracked
  artifact you did not create — inspect it first.
- End git commit messages with the required co-author trailer; branch first if on the
  default branch; commit/push only when the user asks.

## 11. Handoff prompt format

Keep handoff prompts minimal — the task was already presented and approved; do not
re-explain it. A handoff prompt contains only:

1. Task ID + one-line goal.
2. Governing docs (task file + plan file, paths only).
3. The one file (and line range, if known) holding the logic to change.
4. Exact acceptance criteria (bullets only).
5. Stop condition: what the agent must do last and must **not** start next.

## 12. Token-budget discipline

While implementing, watch remaining budget. If what remains will not cover the next
task, document exactly where work will pause (in the task/plan doc) before running out,
so another session can resume cleanly.

## 13. Language policy

- All **user-facing** communication: Spanish.
- All **agent-facing** artifacts — plans, task documents, prompts, handoff
  instructions, ADRs, code, and comments: precise, unambiguous technical English.
- When a change is made, note the related task ID in the line/module comment.

## Related

- `CLAUDE.md` (project) — mission, critical guardrails, ADR index, coding standards.
- `CLAUDE.md` (global user) — cross-project preferences.
- `AGENTS.md` — agent-facing ADR index and analysis requirements.
- `README.md` — pipeline overview and quick start.
- `docs/adr/` — full ADRs; `docs/obsidian/` — module notes and ADR summaries.
- `docs/plans/`, `docs/tasks/` — active plans and task ledgers.

# ADR-014 — Layered Input Mapping Before Deterministic Input Plans

## Status
Accepted

## Date
2026-05-16

## Context

The repository already has a working deterministic execution boundary for MAME observation:

```text
YAML input plan
  -> input_planner.load_input_plan()
  -> private per-frame JSON
  -> scripts/mame_autoboot.lua
  -> MAME
```

That path is functional and covered by baseline tests, but the bootstrap experience is fragile. A contributor currently has to understand too many concerns too early:

- physical keyboard or controller inputs
- the repository's fixed arcade-style button vocabulary
- game-specific semantic actions such as `insert_coin`, `press_start`, `jump`, and `fire`
- hand-authored frame sequences and boot timing
- source-profile details such as the `gng` -> `gngb` driver contract

This couples physical device mapping directly to semantic gameplay intent. It makes first-use setup brittle and increases the chance of silent misconfiguration before the user has a valid controller model.

MAP-00 repository orientation confirmed three constraints that the new mapping work must preserve:

1. The current generated target format is the existing YAML input plan contract:
   - top-level `plan_name`, `game_id`, `steps`
   - each step has `action`, `frames`, optional `notes`
2. Compatibility is not defined by schema alone. `input_planner.py` performs runtime validation against `VALID_ACTIONS`, and `load_input_plan()` remains the authoritative parser.
3. The execution boundary is narrower than `VALID_ACTIONS` alone. `pause` exists in `input_planner.VALID_ACTIONS`, but `scripts/mame_autoboot.lua` does not currently inject a `pause` field. The first layered-mapping implementation must not assume every planner action is executable through the current Lua path.

The repository needs a reusable mapping model that reduces first-run friction without rewriting the existing MAME harness or weakening clean-room safeguards.

## Decision

Introduce a layered input mapping model ahead of the existing deterministic input-plan pipeline.

```text
physical device profile
        ↓
canonical controller profile
        ↓
game action profile
        ↓
compiled input plan
        ↓
existing frame-level JSON / Lua / MAME execution
```

### Layer 1 — Device Profile

Represents a physical keyboard or controller and maps raw device inputs to a canonical controller vocabulary.

Responsibilities:

- capture device identity
- store raw physical input identifiers
- normalize raw inputs to canonical control names
- remain clean-room safe public configuration

Expected location:

```text
profiles/devices/<device_id>.yaml
```

### Layer 2 — Controller Profile

Represents the repository's stable canonical control vocabulary, independent of any specific game or hardware.

Responsibilities:

- define the reusable control surface for loaders, importers, and validation
- keep game semantics decoupled from physical hardware
- define required vs optional controls for a controller shape

Expected location:

```text
profiles/controllers/<controller_id>.yaml
```

### Layer 3 — Game Action Profile

Maps canonical controls to semantic game actions for a specific source profile and driver.

Responsibilities:

- keep game semantics separate from hardware and controller shape
- allow multiple games to reuse the same controller profile
- constrain semantic outputs to the currently supported execution surface

Expected location:

```text
profiles/games/<driver>/<profile>.yaml
```

### Compiled Input Plan

The first implementation phase must compile layered profiles into the existing YAML input plan format rather than replacing `input_planner.py`, the private JSON export, the Lua injector, or the MAME runner.

The compiler output remains:

```yaml
plan_name: ...
game_id: ...
steps:
  - action: ...
    frames: ...
    notes: ...
```

The compiler must validate compatibility by loading the generated YAML through `input_planner.load_input_plan()`.

### First-PR Compatibility Rules

The first implementation PR must preserve the current execution path:

```text
layered public profiles
  -> generated public input plan YAML
  -> apps/mame-harness/input_planner.py
  -> private per-frame JSON
  -> scripts/mame_autoboot.lua
  -> MAME
```

The first PR must also enforce the following:

- no runner rewrite
- no Lua rewrite
- no change to the private/public clean-room boundary
- no silent fallback from unknown controls or missing mappings to `noop`
- generated public artifacts must use existing guardrail conventions or an equivalent guardrail-aware writer
- compiled actions must be restricted to the safe currently executable contract; actions not fully supported by the present Lua injection layer must fail explicitly or remain out of scope for the first PR

## Consequences

**Positive**

- Bootstrap mapping becomes layered, deterministic, and easier to explain.
- Physical device mapping becomes reusable across games.
- The existing MAME harness remains the execution boundary, reducing regression risk.
- Later SDL GameControllerDB and RetroArch importers can target a stable internal model.
- Each layer can be validated independently with focused tests.
- Public mapping artifacts remain abstract and compatible with current clean-room guardrails.

**Negative**

- More public files and concepts are introduced.
- Schema and loader design can be overbuilt if the first PR exceeds the minimum contract.
- Importers and mapping wizards introduce deferred complexity that must not leak into the first PR.
- The current action surface is constrained by both planner validation and Lua injection support, not by schema declarations alone.

## Known Risks And Constraints

- `input_plan.schema.json` does not encode the semantic action vocabulary. Runtime validation in `input_planner.py` remains authoritative.
- `pause` is accepted by the planner but not mapped in `scripts/mame_autoboot.lua`. The first layered-mapping implementation must treat this as an unsupported compatibility edge unless the execution boundary is intentionally expanded in a later task.
- Public YAML generation needs a guardrail-aware writer equivalent to the existing JSON metadata writer; otherwise a new public artifact path can bypass current enforcement patterns.
- `gngb` is the first supported sample, but the architecture must not hardcode `gngb` as the only mapping model.

## Alternatives Considered

**Keep semantic YAML plans only**

Rejected because it preserves the current bootstrap friction and continues to force contributors to author game-semantic plans before establishing a stable physical input model.

**Replace the current MAME harness**

Rejected because the current execution path is already deterministic, tested, and aligned with the clean-room boundary. The immediate need is a compatibility layer, not a new runtime.

**Build a GUI or wizard first**

Rejected because a guided UX without a stable underlying domain model would hide the problem instead of solving it. Interactive setup is deferred until the data model is stable.

## Related

- [ADR-001](./ADR-001-clean-room-layered-architecture.md)
- [ADR-002](./ADR-002-private-evidence-uri-scheme.md)
- [ADR-003](./ADR-003-public-output-blocklist.md)
- [ADR-005](./ADR-005-source-profile-pattern.md)
- [ADR-009](./ADR-009-input-plan-determinism.md)
- [docs/plans/layered_input_mapping_plan.md](../plans/layered_input_mapping_plan.md)
- [docs/new reqs/blackbox_mame_mapping_handoff_updated/docs/ADR-0001-layered-input-mapping.md](../new%20reqs/blackbox_mame_mapping_handoff_updated/docs/ADR-0001-layered-input-mapping.md)
- `apps/mame-harness/input_planner.py`
- `apps/mame-harness/cli.py`
- `apps/mame-harness/guardrails.py`
- `apps/mame-harness/source_profiles.py`
- `scripts/mame_autoboot.lua`

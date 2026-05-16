# ADR-014 — Layered Input Mapping

tags: #adr #input #mapping #mame #clean-room

Source: `docs/adr/ADR-014-layered-input-mapping.md`
Plan: `docs/plans/layered_input_mapping_plan.md`

## Decision

Add a layered mapping model before the current deterministic input-plan pipeline:

```text
device profile
  -> controller profile
  -> game action profile
  -> compiled input plan
  -> existing JSON / Lua / MAME execution
```

## Why

The current bootstrap path couples physical input too directly to semantic game actions. Contributors need to understand hardware mapping, source-profile details, and frame-authored plans too early.

MAP-00 confirmed that the existing runtime path is already stable:

- YAML input plan -> `input_planner.load_input_plan()`
- private per-frame JSON export
- `BLACKBOX_INPUT_PLAN_PATH`
- `scripts/mame_autoboot.lua`
- MAME

The mapping work should reduce setup friction without rewriting that path.

## Compatibility Constraints

- First PR compiles to the current YAML input plan shape: `plan_name`, `game_id`, `steps`.
- `input_planner.load_input_plan()` remains the compatibility authority.
- Public generated plans must use guardrail-aware writing.
- No silent fallback to `noop` for missing required mappings.
- `pause` exists in planner `VALID_ACTIONS` but is not currently injected by Lua, so it is not part of the safe first-PR execution surface.

## Deferred Work

- SDL GameControllerDB importer
- RetroArch autoconfig importer
- `map init` wizard
- boot calibration
- runner or Lua rewrites

## Related

- [[ADR-001 Clean-Room Layered Architecture]]
- [[ADR-003 Public Output Blocklist]]
- [[ADR-005 Source Profile Pattern]]
- [[ADR-009 Input Plan Determinism]]
- [[Input Plan]]
- [[Guardrails]]
- [[Source Profile]]

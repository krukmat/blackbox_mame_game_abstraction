# ADR-018 — Boot Calibration Public Contract

tags: #adr #boot #calibration #timing #clean-room

Source: `docs/adr/ADR-018-boot-calibration-public-contract.md`
Plan: `docs/plans/layered_input_mapping_plan.md`

## Decision

Boot calibration may inspect private evidence locally, but it emits only an abstract public timing profile.

```text
private calibration session
  -> public boot_calibration.yaml
  -> generated public input plan
  -> existing planner / Lua / MAME execution
```

## Rules

- Public output may contain semantic phase names, frame counts, tolerances, and optional `private://` provenance only.
- Public output may not contain screenshots, videos, frame paths, crop paths, OCR dumps, or per-frame visual data.
- The first implementation uses hybrid manual confirmation rather than pixel comparison or full automatic prompt detection.
- Calibration does not replace `input_planner.py` or `scripts/mame_autoboot.lua`.

## Related

- [[ADR-001 Clean-Room Layered Architecture]]
- [[ADR-002 Private URI Scheme]]
- [[ADR-003 Public Output Blocklist]]
- [[ADR-008 Behavioral Validation No Pixels]]
- [[ADR-009 Input Plan Determinism]]
- [[ADR-014 Layered Input Mapping]]

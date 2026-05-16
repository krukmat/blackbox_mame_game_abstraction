# ADR-017 — `map init` Wizard

tags: #adr #input #mapping #wizard #cli

Source: `docs/adr/ADR-017-map-init-wizard.md`
Plan: `docs/plans/layered_input_mapping_plan.md`

## Decision

Add a prompt-based `map init` wizard that writes a normal `device_profile`.

```text
interactive prompts
  -> required / optional control bindings
  -> device_profile YAML
  -> existing mapping loader / compiler path
```

## Rules

- Output stays a normal `device_profile`.
- Existing public-output guardrails still apply.
- Existing `load_mapping_profile()` remains the validator.
- Required controls from the selected controller profile are enforced.
- Optional controls may be skipped.
- Duplicate raw bindings fail during input.

## First Version

- prompt-based CLI only
- optional `keyboard_default` device preset
- `arcade_2button` controller preset
- no real-time OS input capture
- no GUI or TUI framework

## Related

- [[ADR-003 Public Output Blocklist]]
- [[ADR-014 Layered Input Mapping]]
- [[ADR-015 SDL GameControllerDB Importer]]
- [[ADR-016 RetroArch Autoconfig Importer]]


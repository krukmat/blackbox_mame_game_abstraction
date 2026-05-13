# Exploration Strategy

The initial harness assumes controlled, reproducible black-box exploration:

1. Define an input plan in YAML with deterministic actions and durations.
2. Expand the plan into frame-level intent metadata before any emulator integration.
3. Build a MAME command in dry-run mode before executing a local run.
4. Capture evidence only under `evidence/private/run_<id>/`.
5. Redact private paths before writing public artifacts.
6. Use private frames only for local motion analysis that emits numeric metadata.

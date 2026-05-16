# GNG-MAP-01 - Legacy GNG Plan Decomposition

## Status

✅ Done — 2026-05-17

## Objective

Map the current GNG operational plans onto the layered mapping model and define which public artifact owns each concern.

## Scope

- inventory `plans/gng_boot_only.yaml` and `plans/gng_gameplay.yaml`
- identify which steps are:
  - semantic gameplay actions
  - fixed timing waits
  - source-profile assumptions
  - script/bootstrap assumptions
- define the migration matrix from legacy authored steps to:
  - `profiles/games/gngb/default_actions.yaml`
  - GNG `input_sequence` files
  - generated runtime plans under `plans/generated/`
  - later `boot_calibration` ownership under ADR-018
- document any semantic gaps between legacy plans and the current layered compiler contract

## Out Of Scope

- editing runtime scripts
- changing local bootstrap config
- compiling or replacing active GNG plans
- implementing boot calibration

## Dependencies

- parent plan: [GNG Layered Mapping Adoption Plan](../../plans/gng_layered_mapping_adoption_plan.md)
- architectural prerequisites already accepted:
  - [ADR-014](../../adr/ADR-014-layered-input-mapping.md)
  - [ADR-018](../../adr/ADR-018-boot-calibration-public-contract.md)
- timing context from [T10.3 - Timing Calibration](../gng_source_integration/T10.3-timing-calibration.md)

## Reasoning Grade

`High`

## Effort Grade

`Low`

## Recommended Model

`GPT-5.5`

## Acceptance Criteria

- every step in `gng_boot_only` and `gng_gameplay` is assigned to a layered artifact owner
- the plan explicitly distinguishes temporary fixed timing carried forward from future calibration-owned timing
- the task documents whether any legacy plan behavior cannot be represented through the current layered contract
- another agent can continue into artifact authoring without ambiguity

## Legacy Artifact Inventory

### Authored semantic runtime plans

- `plans/gng_boot_only.yaml`
  - boot-only operational plan for manual capture
  - mixes calibrated boot waits, semantic actions, and a long `noop` takeover tail
- `plans/gng_gameplay.yaml`
  - full automated capture plan
  - reuses the same boot sequence, then encodes locomotion, jump, fire, and observation windows

### Layered public artifacts already available

- `profiles/games/gngb/default_actions.yaml`
  - already encodes the semantic action layer for `gng -> gngb`
  - canonical control mappings needed by GNG already exist:
    - `select -> insert_coin`
    - `start -> press_start`
    - `dpad_right -> move_right`
    - `south -> jump`
    - `east -> fire`
    - `noop -> noop`
- `profiles/controllers/arcade_2button.yaml`
  - current canonical control surface is sufficient for the GNG plans
- `profiles/devices/keyboard_default.yaml`
  - compile-time validator only for the current compiler contract
- `plans/sequences/gng_smoke_sequence.yaml`
  - proves the layered compiler path works, but is not the GNG runtime source of truth

### Operational consumers still pointing at legacy plans

- `.env.example`
  - `BLACKBOX_BOOT_PLAN=plans/gng_boot_only.yaml`
  - `BLACKBOX_TRACE_INPUT_PLAN=plans/gng_gameplay.yaml`
- `blackbox.local.example.yaml`
  - `boot_plan: plans/gng_boot_only.yaml`
  - `trace_input_plan: plans/gng_gameplay.yaml`
- `scripts/launch_manual_capture_autoboot.sh`
  - defaults `BLACKBOX_BOOT_PLAN` to `plans/gng_boot_only.yaml`
- `scripts/extract_frames.sh`
  - defaults `BLACKBOX_TRACE_INPUT_PLAN` to `plans/gng_gameplay.yaml`
- `apps/mame-harness/source_profiles.py`
  - `GNG_SOURCE_PROFILE.base_input_plan` still points at `plans/basic_controls.yaml`

## Decomposition Findings

### Semantic compatibility with the layered contract

- The current GNG legacy plans are fully representable through the existing layered model.
- No legacy step requires `pause` or any other action outside `input_planner.VALID_ACTIONS`.
- All gameplay semantics used by the legacy plans are already expressible through the existing GNG action profile:
  - `insert_coin`
  - `press_start`
  - `move_right`
  - `jump`
  - `fire`
  - `noop`
- The long `noop` windows are valid under the current compiler and planner contracts because `noop` is a declared canonical control and semantic action.

### Source-profile and runtime boundary findings

- The authoritative source profile remains `gng`, and the executable driver remains `gngb`.
- Compiled runtime plans must therefore keep `game_id: gngb`, derived from `profiles/games/gngb/default_actions.yaml`.
- The legacy plans are not device-specific in practice. They encode semantic runtime intent, not physical input bindings.
- The current compiler still requires a concrete `device_profile`, so runtime GNG compilation is not yet truly device-agnostic even though the resulting generated plan is.

### Timing ownership finding

- Three boot waits are calibration-derived and should be treated as temporary sequence-owned values that later move under ADR-018 timing ownership:
  - pre-coin boot wait: `noop x 950`
  - pre-start prompt wait: `noop x 60`
  - title/intro wait: `noop x 480`
- Two press widths are operational execution details and remain sequence-owned:
  - `insert_coin x 10`
  - `press_start x 5`
- The manual-capture tail `noop x 9999` is not a calibration artifact. It is an operational handoff seam that keeps Lua injection inactive while the human takes over.

## Legacy Step Ownership Matrix

| Legacy plan step | Current meaning | Layered owner now | Future owner under ADR-018 | Notes |
|---|---|---|---|---|
| `noop x 950` | RAM/ROM check + attract-mode lead-in before coin prompt | `input_sequence` step in boot and gameplay sequences | `boot_calibration` should become the source of the frame count/window | Keep carried forward unchanged in GNG-MAP-02 |
| `insert_coin x 10` | coin insertion pulse | `game_action_profile` owns `select -> insert_coin`; `input_sequence` owns duration and placement | none | sequence control should be `select` |
| `noop x 60` | wait for start prompt | `input_sequence` step in boot and gameplay sequences | `boot_calibration` should become the source of the frame count/window | Keep carried forward unchanged in GNG-MAP-02 |
| `press_start x 5` | start pulse | `game_action_profile` owns `start -> press_start`; `input_sequence` owns duration and placement | none | sequence control should be `start` |
| `noop x 480` | title transition + intro until Arthur is controllable | `input_sequence` step in boot and gameplay sequences | `boot_calibration` should become the source of the frame count/window | Keep carried forward unchanged in GNG-MAP-02 |
| `noop x 9999` in `gng_boot_only` | stop injecting inputs so manual play can begin | `input_sequence` step in boot-only sequence | none | operational takeover seam, not a timing calibration artifact |
| `move_right x 60` | locomotion evidence | `game_action_profile` owns `dpad_right -> move_right`; `input_sequence` owns duration/order | none | gameplay sequence only |
| `jump x 30` | jump-arc evidence | `game_action_profile` owns `south -> jump`; `input_sequence` owns duration/order | none | gameplay sequence only |
| `move_right x 40/60` | locomotion continuation | `game_action_profile` owns `dpad_right -> move_right`; `input_sequence` owns duration/order | none | gameplay sequence only |
| `fire x 20` | projectile evidence | `game_action_profile` owns `east -> fire`; `input_sequence` owns duration/order | none | gameplay sequence only |
| gameplay `noop x 30/40` | observation windows for projectile travel and settling | `input_sequence` owns duration/order | none | not calibration-owned; these are capture-design choices |

## Migration Decisions For GNG-MAP-02

### Source-of-truth files to author

- `plans/sequences/gng_boot_only.yaml`
  - `id: gng_boot_only`
  - canonical controls only
- `plans/sequences/gng_gameplay.yaml`
  - `id: gng_gameplay`
  - canonical controls only

### Generated runtime targets to produce

- `plans/generated/gng_boot_only.yaml`
- `plans/generated/gng_gameplay.yaml`

These names preserve the current public runtime identifiers while isolating the new generated artifacts under `plans/generated/`.

### Control translation to apply

| Legacy semantic action | Canonical sequence control |
|---|---|
| `insert_coin` | `select` |
| `press_start` | `start` |
| `move_right` | `dpad_right` |
| `jump` | `south` |
| `fire` | `east` |
| `noop` | `noop` |

## Unresolved Constraints And Explicit Gaps

### Compile-time device dependency

- `mapping_compiler.build_compiled_input_plan()` requires a `device_profile` and rejects unbound non-`noop` controls.
- That means GNG runtime generation currently still needs a concrete validator profile such as `profiles/devices/keyboard_default.yaml`, even though the generated runtime plan does not materially depend on that keyboard layout.
- Because changing the compiler contract is out of scope for `GNG-MAP-02`, the next task should treat the device profile as a compile-time validation dependency, not as the GNG runtime source of truth.

### Operational surfaces remain stale by design

- `.env.example`, `blackbox.local.example.yaml`, helper scripts, README/bootstrap references, and `SourceProfile.base_input_plan` are intentionally unchanged in this task.
- Repointing those surfaces belongs to `GNG-MAP-04`, after generated-plan parity is proven in `GNG-MAP-03`.

## Handoff To GNG-MAP-02

Another agent can proceed without ambiguity using these decisions:

- author two canonical `input_sequence` files under `plans/sequences/`
- preserve the exact carried-forward boot timings `950 / 10 / 60 / 5 / 480`
- preserve the manual takeover tail `noop x 9999` in the boot-only sequence
- map gameplay semantics through the existing GNG action profile instead of changing `default_actions.yaml` unless a gap is discovered during authoring
- compile to `plans/generated/gng_boot_only.yaml` and `plans/generated/gng_gameplay.yaml`
- use the existing controller/action stack:
  - `profiles/controllers/arcade_2button.yaml`
  - `profiles/games/gngb/default_actions.yaml`
- use a concrete `device_profile` only as a temporary compiler requirement, not as the authoritative representation of GNG runtime behavior

## Reference Documents

- [This Task File](./GNG-MAP-01-legacy-gng-plan-decomposition.md)
- [Parent Plan](../../plans/gng_layered_mapping_adoption_plan.md)
- [Layered Input Mapping Plan](../../plans/layered_input_mapping_plan.md)
- [GNG Source Integration Plan](../../plans/gng_source_integration_plan.md)
- [README.md](../../../README.md)
- [AGENTS.md](../../../AGENTS.md)
- [CLAUDE.md](../../../CLAUDE.md)
- [ADR-005](../../adr/ADR-005-source-profile-pattern.md)
- [ADR-009](../../adr/ADR-009-input-plan-determinism.md)
- [ADR-014](../../adr/ADR-014-layered-input-mapping.md)
- [ADR-018](../../adr/ADR-018-boot-calibration-public-contract.md)
- [Input Plan](../../obsidian/Input%20Plan.md)
- [Source Profile](../../obsidian/Source%20Profile.md)
- [GNG Integration Plan](../../obsidian/GNG%20Integration%20Plan.md)
- [Bootstrap Setup](../../bootstrap.md)
- [Layered Input Mapping](../../mapping.md)
- [T10.3 - Timing Calibration](../gng_source_integration/T10.3-timing-calibration.md)

# ADR-016 — RetroArch Autoconfig Importer to Device Profiles

## Status
Accepted

## Date
2026-05-16

## Context

ADR-014 established `device_profile` as the public hardware-facing layer in the mapping model. ADR-015 then added SDL GameControllerDB import as one normalized path into that layer.

A second common controller-config source is RetroArch autoconfig `.cfg` files. These files already describe physical controller bindings, but their naming conventions do not match the repository's canonical controller vocabulary directly. In particular, RetroArch's `input_a_btn` and `input_b_btn` names can be interpreted differently if a caller projects Xbox-style mental models onto Nintendo-style labels.

The importer therefore needs a deterministic policy that:

- produces the same `device_profile` contract as hand-authored profiles and the SDL importer
- does not guess button semantics from vendor or platform heuristics
- keeps unsupported or extra RetroArch fields from leaking into public output
- stays inside the existing clean-room guardrails and loader validation path

## Decision

Add a RetroArch autoconfig importer that converts a `.cfg` file into a standard `device_profile`.

### Input Surface

The importer reads a RetroArch autoconfig file with simple `key = "value"` assignments and supports a CLI flow:

```text
map import-retroarch --config <file> --out <yaml> [--profile-id <id>]
```

### Output Surface

The importer writes a standard `device_profile`:

- `profile_type: device_profile`
- `source: retroarch_autoconfig`
- `device.kind: gamecontroller`
- `device.name` from `input_device` when available
- `device.guid` is `vendor:<vendor_id>:product:<product_id>` when both IDs are present; otherwise `null`
- `raw_to_canonical` built from the supported RetroArch mapping fields only
- `metadata.clean_room_safe: true`

The YAML must pass the existing `load_mapping_profile()` validation path after it is written.

### Canonical Mapping Policy

The first importer supports this RetroArch field subset:

- `input_up_btn`, `input_up_axis` -> `dpad_up`
- `input_down_btn`, `input_down_axis` -> `dpad_down`
- `input_left_btn`, `input_left_axis` -> `dpad_left`
- `input_right_btn`, `input_right_axis` -> `dpad_right`
- `input_b_btn` -> `south`
- `input_a_btn` -> `east`
- `input_y_btn` -> `north`
- `input_x_btn` -> `west`
- `input_select_btn` -> `select`
- `input_start_btn` -> `start`
- `input_l_btn` -> `l1`
- `input_r_btn` -> `r1`

For `A/B`, the importer uses one explicit convention:

- `input_b_btn` is treated as the bottom face button (`south`)
- `input_a_btn` is treated as the right face button (`east`)

This matches the typical RetroPad/Nintendo-style label orientation and avoids platform-specific guessing.

### Validation Policy

The importer fails explicitly when:

- the config file is malformed
- no supported bindings are present
- two supported RetroArch fields map to the same canonical control
- two supported RetroArch fields reuse the same raw physical binding
- the output path is not allowed for public artifacts
- the generated YAML fails the existing `device_profile` validation path

Unsupported RetroArch fields are ignored with explicit warnings returned by the importer and CLI result.

## Consequences

**Positive**

- Contributors can bootstrap `device_profile` YAML from another common controller-config source.
- RetroArch import remains aligned with the same normalized device-profile contract as SDL import.
- A/B behavior is deterministic and documented instead of heuristic.
- Clean-room path and payload rules remain enforced by the existing writer/loader boundary.

**Negative**

- The first importer supports only a small subset of RetroArch mapping fields.
- Analog, trigger, stick-click, hotkey, and platform-specific fields may be ignored and reported as warnings.
- Some RetroArch configs provide both button and axis variants for the same direction; the importer treats that as a conflict instead of picking one silently.

## Alternatives Considered

**Infer A/B meaning per vendor or platform**

Rejected because it introduces hidden heuristics and makes imports less predictable.

**Adopt RetroArch as an execution backend**

Rejected because the repository execution boundary remains MAME plus the existing input-plan pipeline.

**Store the whole RetroArch config inside the output profile**

Rejected because the normalized `device_profile` is already the stable public abstraction and keeping raw config baggage would add unnecessary duplication.

## Related

- [ADR-003](./ADR-003-public-output-blocklist.md)
- [ADR-014](./ADR-014-layered-input-mapping.md)
- [ADR-015](./ADR-015-sdl-gamecontrollerdb-importer.md)
- [docs/plans/layered_input_mapping_plan.md](../plans/layered_input_mapping_plan.md)
- `apps/mame-harness/retroarch_mapping_importer.py`
- `apps/mame-harness/cli.py`


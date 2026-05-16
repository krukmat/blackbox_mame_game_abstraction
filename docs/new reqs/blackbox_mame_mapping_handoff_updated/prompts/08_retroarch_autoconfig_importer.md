# Prompt 08 - RetroArch Autoconfig Importer

```text
Implement RetroArch autoconfig importer after SDL importer is stable.

Scope:

Add:

- apps/mame-harness/retroarch_mapping_importer.py

CLI command:

```bash
blackbox map import-retroarch \
  --config path/to/controller.cfg \
  --out profiles/devices/imported_retroarch_controller.yaml
```

Behavior:

- Parse a RetroArch autoconfig `.cfg` file.
- Extract device name/vendor/product fields when available.
- Map common RetroArch inputs to canonical controls:
  - input_a_btn -> east or south depending on convention detected/documented;
  - input_b_btn -> south or east depending on convention detected/documented;
  - input_x_btn -> west;
  - input_y_btn -> north;
  - input_start_btn -> start;
  - input_select_btn -> select;
  - input_up_btn/input_up_axis -> dpad_up;
  - input_down_btn/input_down_axis -> dpad_down;
  - input_left_btn/input_left_axis -> dpad_left;
  - input_right_btn/input_right_axis -> dpad_right;
  - input_l_btn -> l1;
  - input_r_btn -> r1.

Important:

RetroArch A/B physical naming can differ from SDL/Nintendo/Xbox mental models. Document the convention in code comments and tests. Prefer deterministic behavior over guessing.

Constraints:

- Do not modify SDL importer.
- Do not implement wizard here.
- Generated output must pass `device_profile` validation.

Tests:

- minimal RetroArch config imports successfully;
- missing optional fields are tolerated;
- malformed config fails clearly;
- generated profile validates;
- A/B convention is documented in a test name or assertion.
```

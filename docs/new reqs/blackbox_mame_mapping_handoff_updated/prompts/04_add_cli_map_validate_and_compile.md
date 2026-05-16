# Prompt 04 - Add CLI Commands `map validate` and `map compile`

```text
Add CLI support for layered input mapping.

Scope:

Extend the existing CLI in:

- apps/mame-harness/cli.py

Add a `map` command group or equivalent structure consistent with the current CLI style.

Required commands:

1. Validate one profile:

```bash
blackbox map validate --profile profiles/devices/keyboard_default.yaml
```

2. Compile layered profiles to an existing input plan:

```bash
blackbox map compile \
  --device profiles/devices/keyboard_default.yaml \
  --controller profiles/controllers/arcade_2button.yaml \
  --game profiles/games/gngb/default_actions.yaml \
  --sequence plans/sequences/gng_smoke_sequence.yaml \
  --out plans/generated/gng_smoke_compiled.yaml
```

Constraints:

- Do not break existing CLI commands.
- Follow existing argument parsing style.
- Errors must be actionable.
- The compile command must create parent directories for the output path when safe.
- The command must refuse unsafe output paths if the repo already has conventions for public/private boundaries.
- Do not run MAME from this command.
- Do not read ROMs, screenshots, audio or private evidence.

Add tests:

- apps/mame-harness/tests/test_mapping_cli.py

Test cases:

1. `map validate` succeeds for valid sample profiles;
2. `map validate` fails for invalid profile;
3. `map compile` writes a generated plan;
4. generated plan is parseable by the current input planner;
5. existing CLI behavior still works.

After implementation, provide the exact commands to run the test subset.
```

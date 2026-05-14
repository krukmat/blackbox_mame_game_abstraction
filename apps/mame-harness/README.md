# MAME Harness

The harness provides a simple typed CLI and guardrail-aware helpers for:

- input-plan loading
- dry-run MAME command construction
- private evidence path management
- public metadata redaction
- placeholder analysis, inference, asset, and validation commands

## Quick start

Activate the Python 3.11 virtualenv before running any command:

```bash
source apps/mame-harness/.venv/bin/activate
```

### Dry-run with GNG source profile (no ROM required)

```bash
python apps/mame-harness/cli.py run \
  --rom gngb \
  --source-profile gng \
  --dry-run
```

### Real run with GNG source profile

```bash
python apps/mame-harness/cli.py run \
  --rom gngb \
  --source-profile gng \
  --rom-path <path-to-roms> \
  --frames-to-run 300
```

`<path-to-roms>` must be the private local directory containing `gng.zip`. This path is never committed.

Without `--source-profile` the run is generic — no preflight validation and no profile-backed driver contract.

## Source profiles

The canonical source profile definitions live in `apps/mame-harness/source_profiles.py`.

Current profile contract:

- `gng` resolves to MAME driver `gngb`
- `--rom-path` is expected to point to the private local directory that contains `gng.zip`
- the base capture contract uses `plans/basic_controls.yaml`, `scripts/mame_autoboot.lua`, and a bounded default of `300` frames
- the profile is for private observation and redacted metadata generation only; it does not promise faithful game reproduction

## Preflight

The preflight validator lives in `apps/mame-harness/preflight.py`.

Current preflight contract:

- validates MAME binary presence and `-version` execution
- requires MAME `0.240` or newer
- validates that the `gng` profile still resolves to `gngb`
- accepts either a directory containing `gng.zip` or a direct path to `gng.zip`
- returns structured results for runner and CLI consumption

## Runner contract

The hardened runner lives in `apps/mame-harness/mame_runner.py`.

Current runner statuses:

- `dry_run`
- `preflight_failure`
- `execution_failure`
- `success`

Each runner result includes the built MAME command and may also include structured preflight and execution details.

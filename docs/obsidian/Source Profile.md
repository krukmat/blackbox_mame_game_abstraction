# Source Profile

tags: #mame #configuration #gng

`apps/mame-harness/source_profiles.py`

## Purpose

A `SourceProfile` is the canonical, version-controlled configuration for one game observation source. It encodes:
- Which MAME driver to use (may differ from ROM zip name)
- Expected ROM zip filename
- Default capture parameters
- Explicit statement that this is private observation only

## The GNG Profile

The only currently defined profile is `GNG_SOURCE_PROFILE` for Ghosts'n Goblins.

```python
GNG_SOURCE_PROFILE = SourceProfile(
    profile_id="gng",
    display_name="Ghosts'n Goblins local observation source",
    mame_driver="gngb",           # NOTE: driver is gngb, not gng
    expected_rom_zip="gng.zip",
    rom_path_kind="directory_containing_rom_zip",
    base_input_plan=Path("plans/basic_controls.yaml"),
    default_frames_to_run=300,
    autoboot_script=Path("scripts/mame_autoboot.lua"),
    private_usage_only=True,
    public_output_boundary="...",
    notes=(
        "The local gng.zip matches MAME driver gngb, not the parent gng driver.",
        ...
    ),
)
```

## Critical: Driver Disambiguation

`gng.zip` must be launched with MAME driver `gngb` (the bootleg version), **not** `gng`.
This is validated by [[Preflight]] before any real run. If the profile declares a wrong driver, preflight returns `PreflightResult(ok=False, issues=["driver_contract_mismatch"])`.

## CLI Usage

```bash
python3.11 apps/mame-harness/cli.py run --rom gng --rom-path /path/to/roms --dry-run
```

The CLI detects `args.rom == "gng"` and injects `GNG_SOURCE_PROFILE` automatically.

## Known Limitation

The driver validation in `preflight.py` has a hardcoded `if profile.profile_id == "gng"` check. Adding a second game would require adding another branch rather than using a generic contract. See [[ADR-005 Source Profile Pattern]] for the full reasoning.

## Related

- [[MAME Runner]]
- [[Preflight]]
- [[ADR-005 Source Profile Pattern]]
- `apps/mame-harness/source_profiles.py`
- `docs/tasks/gng_source_integration/T02-gng-source-profile-definition.md`

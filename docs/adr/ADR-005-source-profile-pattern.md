# ADR-005 — Source Profile Pattern for Game Observation Inputs

## Status
Accepted

## Date
2026-05-13

## Context

The MAME harness needs to support multiple games over time, each with:
- a specific MAME driver name (which may differ from the ZIP name — e.g., `gng.zip` requires driver `gngb`, not `gng`)
- expected ROM zip filename
- default capture parameters
- an explicit statement that private usage is the only intended use

Without a canonical profile object, this knowledge would scatter across CLI argument defaults, hardcoded constants in the runner, and comments. A new contributor would not know that `gng.zip` must use driver `gngb` unless they happened to read the right file.

The profile also needs to be the authoritative input to the preflight validator — the validator must reject any profile where the driver contract is wrong, before any real MAME invocation.

## Decision

Introduce a `SourceProfile` frozen dataclass in `source_profiles.py`:

```python
@dataclass(frozen=True, slots=True)
class SourceProfile:
    profile_id: str
    display_name: str
    mame_driver: str
    expected_rom_zip: str
    rom_path_kind: str
    rom_path_example: Path
    base_input_plan: Path
    default_frames_to_run: int
    autoboot_script: Path
    private_usage_only: bool
    public_output_boundary: str
    notes: tuple[str, ...]
```

Key fields:
- `mame_driver`: the driver to use with MAME — may differ from the ZIP filename.
- `private_usage_only`: a machine-readable flag signaling that this profile is for observation only.
- `public_output_boundary`: a human-readable string stating what public outputs this profile is allowed to produce.
- `notes`: tuple of operational notes (e.g., driver disambiguation warnings).

`GNG_SOURCE_PROFILE` is the first concrete profile, declared as a module-level constant and registered in `SOURCE_PROFILES: dict[str, SourceProfile]`.

The CLI resolves a profile by name: `get_source_profile("gng")`. If the name is unknown, it raises a `ValueError` with the list of available profiles.

Preflight (`preflight.py::_validate_driver_contract`) treats the profile as the source of truth and validates that the declared `mame_driver` matches the expected contract for that `profile_id`.

## Consequences

**Positive**
- The driver disambiguation for `gng` (use `gngb`, not `gng`) is now encoded once and tested, not scattered.
- Adding a new game requires adding one `SourceProfile` constant and one entry in `SOURCE_PROFILES`. No other files need to change for basic support.
- The `private_usage_only` flag is readable by tooling and documentation generators.

**Negative**
- The driver contract validation in `preflight.py` currently has a hardcoded check: `if profile.profile_id == "gng" and profile.mame_driver != EXPECTED_GNG_DRIVER`. This is not a general contract mechanism — adding a second game would require adding another `if` branch. A better design would embed a `required_driver` field in the profile itself and validate it generically.
- `rom_path_kind` is a string (`"directory_containing_rom_zip"`) rather than an Enum. It conveys intent but is not machine-enforced.

## Related

- [ADR-004](./ADR-004-mame-runner-structured-results.md)
- `apps/mame-harness/source_profiles.py`
- `apps/mame-harness/preflight.py`
- `docs/tasks/gng_source_integration/T02-gng-source-profile-definition.md`
- `docs/tasks/gng_source_integration/T03-mame-and-rom-preflight-validation.md`

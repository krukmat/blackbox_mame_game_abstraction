# Preflight

tags: #mame #validation #runner

`apps/mame-harness/preflight.py`

## Purpose

Validate all prerequisites for a MAME run before any subprocess is started. Produces a `PreflightResult` that the [[MAME Runner]] inspects before execution.

## Validation Chain (in order)

```
1. _validate_driver_contract(profile)
   → checks mame_driver matches the expected contract for this profile_id

2. _validate_mame_binary_presence(mame_binary)
   → shutil.which(mame_binary) — must be resolvable in PATH

3. _probe_mame_version(mame_binary)
   → runs mame -version, parses "0.<NNN>" format
   → must be >= MAME_MINIMUM_VERSION (currently 240)

4. _resolve_rom_zip_path(profile, rom_path)
   → rom_path must be provided
   → if directory: must contain profile.expected_rom_zip
   → zip filename must match exactly
   → zip must exist on disk
```

If any step fails, preflight returns immediately with `ok=False` and a single `PreflightIssue`.

## Issue Codes

| Code | Field | Trigger |
|------|-------|---------|
| `driver_contract_mismatch` | `profile.mame_driver` | Wrong driver declared in profile |
| `mame_binary_missing` | `mame_binary` | Binary not in PATH |
| `mame_version_probe_failed` | `mame_binary` | Subprocess error on `-version` |
| `mame_version_unparseable` | `mame_binary` | Output doesn't match `0.<NNN>` |
| `mame_version_too_old` | `mame_binary` | Version < 240 |
| `rom_path_missing` | `rom_path` | No ROM path provided for profile run |
| `rom_zip_name_mismatch` | `rom_path` | ZIP filename doesn't match `expected_rom_zip` |
| `rom_zip_missing` | `rom_path` | ZIP not found on disk |

## Preflight is Optional

If `MameRunRequest.source_profile is None`, preflight is skipped and `MameRunResult.preflight` is `None`. Generic runs without a profile bypass all checks.

## Version Parsing

MAME reports versions as `0.268 (mame0268)`. `parse_mame_version` extracts the integer `268`.
The minimum version `240` covers MAME 0.240+, which is when the `gngb` driver stabilized.

## Related

- [[MAME Runner]]
- [[Source Profile]]
- [[ADR-005 Source Profile Pattern]]
- `apps/mame-harness/preflight.py`
- `docs/tasks/gng_source_integration/T03-mame-and-rom-preflight-validation.md`

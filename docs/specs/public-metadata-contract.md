# Public Metadata Contract — `specs/run_metadata.json`

## Status

Stable — verified by T05.4 regression tests (2026-05-13)

## Overview

Every `run` command writes a JSON file to `specs/run_metadata.json`. This document defines what each field may contain and what is permanently excluded, derived from the T05.2 unified redaction policy and enforced by two layers:

1. **Sanitization layer** (`cli.py`) — transforms path-bearing values before they enter the metadata dict.
2. **Guardrail layer** (`guardrails.py` + `metadata_writer.py`) — rejects any payload that still contains a blocked form at write time.

---

## Field Reference

### `run_id`

- Type: `string`
- Allowed: hex run identifier (e.g. `"abc123def456"`)
- Excluded: nothing — this field carries no path information
- Enforcement: none required

---

### `game_shortname`

- Type: `string`
- Allowed: MAME game shortname (e.g. `"gng"`, `"gngb"`)
- Excluded: nothing — this is a non-path scalar
- Enforcement: none required

---

### `input_plan`

- Type: `string`
- Allowed: plan name string (e.g. `"basic_controls"`)
- Excluded: file system paths to the plan file
- Enforcement: `load_input_plan` returns `plan.plan_name`, not the path

---

### `frame_plan_length`

- Type: `integer`
- Allowed: frame count
- Excluded: nothing
- Enforcement: none required

---

### `dry_run`

- Type: `boolean`
- Allowed: `true` or `false`
- Excluded: nothing
- Enforcement: none required

---

### `private_evidence_ref`

- Type: `string`
- Allowed: opaque handle in the form `private://<run-id>`
- Excluded: filesystem path to the evidence directory
- Enforcement: constructed as `f"private://{capture.run_id}"` in `handle_run` — never from a raw path

---

### `state`

- Type: `string`
- Allowed: phase label (e.g. `"dry_run"`, `"success"`, `"preflight_failure"`)
- Excluded: nothing
- Enforcement: none required

---

### `notes`

- Type: `list[string]`
- Allowed: short human-readable state transition notes
- Excluded: path-bearing strings — notes are constructed from fixed templates in `handle_run`
- Enforcement: constructed from fixed strings, not from runner output

---

### `runner_status`

- Type: `string`
- Allowed: `"dry_run"`, `"preflight_failure"`, `"execution_failure"`, `"success"`
- Excluded: nothing
- Enforcement: none required

---

### `command[*]`

- Type: `list[string]`
- Allowed:
  - abstract arguments (e.g. `"-rompath"`, `"-snapshot_directory"`)
  - non-path scalars (e.g. `"gngb"`, `"mame"`, `"60"`)
  - opaque handles (`private://<run-id>/<suffix>`)
  - explicitly allowlisted repo-safe relative references (`scripts/mame_autoboot.lua`)
- Excluded (S1–S6):
  - raw private evidence paths (`evidence/private/...`)
  - frame paths (`/frames/...`)
  - crop paths
  - ROM paths (`*.zip`, absolute ROM directory paths)
  - absolute local machine paths (`/Users/...`, `/home/...`, `C:\...`)
  - any relative workspace path not in `REPO_SAFE_COMMAND_PATHS`
- Enforcement:
  - sanitization: `_redact_command_paths()` in `cli.py`
  - last-gate: `ensure_no_private_paths()` in `guardrails.py`

---

### `preflight.ok`

- Type: `boolean`
- Allowed: `true` or `false`
- Enforcement: none required

---

### `preflight.profile_id`

- Type: `string`
- Allowed: source profile identifier (e.g. `"gng"`)
- Enforcement: none required

---

### `preflight.driver`

- Type: `string`
- Allowed: MAME driver name (e.g. `"gngb"`)
- Enforcement: none required

---

### `preflight.detected_version`

- Type: `integer | null`
- Allowed: MAME version integer (e.g. `264`) or `null`
- Enforcement: none required

---

### `preflight.issues[*].code`

- Type: `string`
- Allowed: issue code string (e.g. `"rom_zip_missing"`)
- Enforcement: none required

---

### `preflight.issues[*].field`

- Type: `string`
- Allowed: field name string (e.g. `"rom_path"`)
- Enforcement: none required

---

### `preflight.issues[*].message`

- Type: `string`
- Allowed: path-free human-readable explanation of the issue
- Excluded (S4, S5, S8):
  - ROM paths
  - absolute local machine paths
  - any path-bearing validation detail
- Enforcement:
  - sanitization: `_sanitize_preflight_issue_message()` uses fixed templates per issue code, then `_strip_path_like_segments()` as fallback
  - last-gate: `ensure_no_private_paths()` in `guardrails.py`

---

### `execution.returncode`

- Type: `integer`
- Allowed: process exit code
- Enforcement: none required

---

### `execution.stdout`

- Type: `string | null`
- Allowed: path-free process output — sanitized text that retains operational meaning without exposing filesystem details
- Excluded (S4, S5, S7):
  - ROM paths
  - absolute local machine paths
  - frame/crop paths
  - private evidence paths
- Enforcement:
  - sanitization: `_sanitize_execution_output()` in `cli.py`
  - last-gate: `ensure_no_private_paths()` in `guardrails.py`

---

### `execution.stderr`

- Type: `string | null`
- Allowed: same rules as `execution.stdout`
- Excluded: same classes as `execution.stdout`
- Enforcement: same as `execution.stdout`

---

## Enforcement Summary

| Layer | Location | What it does |
|---|---|---|
| Command sanitization | `cli.py::_redact_command_paths` | Element-wise redaction of `command[*]` |
| Preflight sanitization | `cli.py::_sanitize_preflight_issue_message` | Template-based + regex redaction of issue messages |
| Output sanitization | `cli.py::_sanitize_execution_output` | Regex redaction of free-form stdout/stderr |
| Guardrail last-gate | `guardrails.py::ensure_no_private_paths` | Rejects any string containing blocked path markers or absolute machine paths |
| Writer gate | `metadata_writer.py::write_public_metadata` | Calls guardrail before writing; raises `ValueError` on violation |

---

## Sensitive Class Index (from T05.2.4)

| Class | Description | Fields affected |
|---|---|---|
| S1 | Private evidence path | `command`, `stdout`, `stderr` |
| S2 | Frame path | `command`, `stdout`, `stderr` |
| S3 | Crop path | `command`, `stdout`, `stderr` |
| S4 | Direct ROM path | `command`, `preflight.issues[*].message`, `stdout`, `stderr` |
| S5 | Absolute local machine path | `command`, `preflight.issues[*].message`, `stdout`, `stderr` |
| S6 | Non-allowlisted workspace path | `command` |
| S7 | Path-bearing process output | `stdout`, `stderr` |
| S8 | Path-bearing validation message | `preflight.issues[*].message` |

---

## Reference Documents

- `docs/tasks/gng_source_integration/T05.2.4-redaction-decision-table.md`
- `docs/tasks/gng_source_integration/T05.2.2-allowed-public-forms.md`
- `docs/tasks/gng_source_integration/T05.2.3-blocked-public-forms.md`
- `docs/tasks/gng_source_integration/T05.4-leakage-regression-tests.md`
- `apps/mame-harness/tests/test_redaction_regression.py`
- `apps/mame-harness/cli.py`
- `apps/mame-harness/guardrails.py`
- `apps/mame-harness/metadata_writer.py`

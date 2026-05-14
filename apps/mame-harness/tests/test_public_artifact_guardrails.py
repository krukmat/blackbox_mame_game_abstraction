from __future__ import annotations

# Public artifact guardrails verification.
# Confirms public artifacts pass ensure_public_output_path and ensure_no_private_paths.

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# specs/traces/gng_trace.json
# ---------------------------------------------------------------------------


GNG_TRACE_PATH = ROOT / "specs" / "traces" / "gng_trace.json"


def test_gng_trace_exists() -> None:
    assert GNG_TRACE_PATH.exists(), f"gng_trace.json not found at {GNG_TRACE_PATH}"


def test_gng_trace_passes_public_output_path_guardrail() -> None:
    from guardrails import ensure_public_output_path

    ensure_public_output_path(GNG_TRACE_PATH)


def test_gng_trace_passes_no_private_paths_guardrail() -> None:
    from guardrails import ensure_no_private_paths

    payload = json.loads(GNG_TRACE_PATH.read_text(encoding="utf-8"))
    ensure_no_private_paths(payload)

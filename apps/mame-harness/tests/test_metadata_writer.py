from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conftest import ROOT
from guardrails import ensure_no_private_paths
from metadata_writer import write_public_metadata


def test_public_metadata_rejects_private_frame_paths(tmp_path: Path) -> None:
    output = tmp_path / "specs" / "public.json"
    payload = {"frame_path": "evidence/private/run-001/frames/frame_0001.png"}
    with pytest.raises(ValueError):
        write_public_metadata(output, payload)


def test_public_metadata_rejects_crop_paths(tmp_path: Path) -> None:
    output = tmp_path / "specs" / "public.json"
    payload = {"crop_path": "datasets/derived/crops/candidate_001.png"}
    with pytest.raises(ValueError):
        write_public_metadata(output, payload)


# T05.3.4 — writer/guardrail enforcement for unsanitized payloads


def test_guardrail_rejects_absolute_unix_path_in_stdout(tmp_path: Path) -> None:
    output = tmp_path / "specs" / "public.json"
    payload = {"execution": {"stdout": "mame: rompath /Users/alice/roms not found"}}
    with pytest.raises(ValueError):
        write_public_metadata(output, payload)


def test_guardrail_rejects_absolute_windows_path_in_stderr(tmp_path: Path) -> None:
    output = tmp_path / "specs" / "public.json"
    payload = {"execution": {"stderr": "error loading C:\\Users\\alice\\roms\\gng.zip"}}
    with pytest.raises(ValueError):
        write_public_metadata(output, payload)


def test_guardrail_rejects_rom_path_in_nested_field(tmp_path: Path) -> None:
    output = tmp_path / "specs" / "public.json"
    payload = {"execution": {"stdout": "required files missing [/home/user/roms/gng.zip]"}}
    with pytest.raises(ValueError):
        write_public_metadata(output, payload)


def test_guardrail_allows_path_free_execution_output(tmp_path: Path) -> None:
    output = tmp_path / "specs" / "public.json"
    payload = {"execution": {"stdout": "MAME 0.264 initialized. Running driver gngb.", "stderr": ""}}
    written = write_public_metadata(output, payload)
    assert written.exists()


def test_ensure_no_private_paths_rejects_absolute_unix_path() -> None:
    with pytest.raises(ValueError):
        ensure_no_private_paths({"stdout": "/Users/alice/roms/gng.zip is missing"})


def test_ensure_no_private_paths_rejects_absolute_windows_path() -> None:
    with pytest.raises(ValueError):
        ensure_no_private_paths({"stderr": "C:\\Users\\alice\\roms not found"})


def test_ensure_no_private_paths_allows_private_uri_handle() -> None:
    # private:// opaque handles are the allowed replacement form — must not be blocked
    ensure_no_private_paths({"ref": "private://abc123/frames"})


def test_asset_recipes_include_prohibited_similarity_constraints() -> None:
    recipes = yaml.safe_load((ROOT / "specs/assets/sample_asset_recipes.yaml").read_text(encoding="utf-8"))
    for recipe in recipes["recipes"]:
        rules = recipe.get("prohibited_similarity_rules", [])
        assert rules
        assert any("sprite" in rule or "frame" in rule for rule in rules)

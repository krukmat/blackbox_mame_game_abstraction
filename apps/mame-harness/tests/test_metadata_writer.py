from __future__ import annotations

from pathlib import Path

import pytest
import yaml

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


def test_asset_recipes_include_prohibited_similarity_constraints() -> None:
    recipes = yaml.safe_load(Path("specs/assets/sample_asset_recipes.yaml").read_text(encoding="utf-8"))
    for recipe in recipes["recipes"]:
        rules = recipe.get("prohibited_similarity_rules", [])
        assert rules
        assert any("sprite" in rule or "frame" in rule for rule in rules)

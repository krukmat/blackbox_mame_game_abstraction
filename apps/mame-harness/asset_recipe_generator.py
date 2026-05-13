from __future__ import annotations

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
ASSET_FACTORY_DIR = ROOT / "packages" / "asset-factory"
if str(ASSET_FACTORY_DIR) not in sys.path:
    sys.path.insert(0, str(ASSET_FACTORY_DIR))

from recipe_generator import build_asset_recipes, write_asset_recipes


def generate_asset_recipes(entity_candidates_path: Path, output_path: Path) -> Path:
    payload = yaml.safe_load(entity_candidates_path.read_text(encoding="utf-8")) or {}
    recipes = build_asset_recipes(payload.get("entity_candidates", []))
    return write_asset_recipes(recipes, output_path)

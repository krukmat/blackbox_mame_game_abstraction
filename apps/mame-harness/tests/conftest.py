from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HARNESS_DIR = ROOT / "apps" / "mame-harness"
VISION_DIR = ROOT / "packages" / "vision"
ASSET_FACTORY_DIR = ROOT / "packages" / "asset-factory"
VALIDATION_DIR = ROOT / "packages" / "validation"

for candidate in (ROOT, HARNESS_DIR, VISION_DIR, ASSET_FACTORY_DIR, VALIDATION_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

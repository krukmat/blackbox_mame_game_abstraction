from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any

from guardrails import ensure_no_private_paths, ensure_public_output_path


def _to_jsonable(payload: Any) -> Any:
    if is_dataclass(payload):
        return asdict(payload)
    if isinstance(payload, Path):
        return str(payload)
    return payload


def write_public_metadata(path: Path, payload: Any) -> Path:
    ensure_public_output_path(path)
    materialized = _to_jsonable(payload)
    ensure_no_private_paths(materialized)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(materialized, indent=2), encoding="utf-8")
    return path

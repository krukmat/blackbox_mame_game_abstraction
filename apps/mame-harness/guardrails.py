from __future__ import annotations

from pathlib import Path
from typing import Any


PRIVATE_EVIDENCE_ROOT = Path("evidence/private")
PUBLIC_OUTPUT_ROOTS = (Path("specs"), Path("docs"), Path("packages/schemas"))
BLOCKED_PUBLIC_SUFFIXES = {
    ".zip",
    ".7z",
    ".rom",
    ".bin",
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".gif",
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".wav",
    ".flac",
    ".state",
    ".sta",
    ".sav",
    ".chd",
}
BLOCKED_PUBLIC_PATH_MARKERS = ("evidence/private/", "/frames/", "/crops/")
BLOCKED_PUBLIC_DIRECTORY_NAMES = {
    "frames",
    "video",
    "videos",
    "crops",
    "screenshots",
    "states",
}


def ensure_private_evidence_path(path: Path) -> Path:
    normalized = Path(path)
    parts = normalized.parts
    expected = PRIVATE_EVIDENCE_ROOT.parts
    for index in range(0, len(parts) - len(expected) + 1):
        if parts[index : index + len(expected)] == expected:
            return normalized
    raise ValueError(f"private evidence must stay under {PRIVATE_EVIDENCE_ROOT.as_posix()}")


def ensure_public_output_path(path: Path) -> Path:
    normalized = Path(path)
    if normalized.suffix.lower() in BLOCKED_PUBLIC_SUFFIXES:
        raise ValueError(f"blocked public output suffix: {path.suffix}")
    if any(part in BLOCKED_PUBLIC_DIRECTORY_NAMES for part in normalized.parts):
        raise ValueError(f"blocked public output directory: {normalized.as_posix()}")
    if normalized.parts and normalized.parts[0] == PRIVATE_EVIDENCE_ROOT.parts[0]:
        raise ValueError("public output cannot be written under evidence/")
    return normalized


def ensure_private_or_allowed_metadata_path(path: Path, allow_public_metadata: bool = False) -> Path:
    normalized = Path(path)
    try:
        return ensure_private_evidence_path(normalized)
    except ValueError:
        if allow_public_metadata:
            return ensure_public_output_path(normalized)
        raise


def ensure_no_private_paths(payload: Any) -> None:
    if isinstance(payload, dict):
        for value in payload.values():
            ensure_no_private_paths(value)
        return

    if isinstance(payload, list):
        for item in payload:
            ensure_no_private_paths(item)
        return

    if isinstance(payload, str):
        normalized = payload.replace("\\", "/")
        if any(marker in normalized for marker in BLOCKED_PUBLIC_PATH_MARKERS):
            raise ValueError(f"private path leaked into public payload: {payload}")

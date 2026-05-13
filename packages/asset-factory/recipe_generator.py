from __future__ import annotations

from pathlib import Path

import yaml

from guardrails import ensure_no_private_paths, ensure_public_output_path

PROHIBITED_SIMILARITY_RULES = [
    "do not reuse original palette",
    "do not copy original silhouette",
    "do not copy character identity",
    "do not use original crop as input",
    "do not copy animation frames",
]


def build_asset_recipes(entity_candidates: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    recipes: list[dict[str, object]] = []
    for candidate in entity_candidates:
        bbox_stats = candidate["bbox_stats"]
        animation_estimate = candidate["animation_estimate"]
        asset_id = str(candidate["candidate_id"]).replace("candidate", "asset")
        recipes.append(
            {
                "id": asset_id,
                "gameplay_role": "moving_actor",
                "size_class": _size_class(float(bbox_stats["mean_width"]), float(bbox_stats["mean_height"])),
                "approximate_canvas_size": {
                    "width": int(float(bbox_stats["mean_width"])),
                    "height": int(float(bbox_stats["mean_height"])),
                },
                "animation_frame_count": int(animation_estimate["frame_count"]),
                "motion_feel": "responsive_arcade_motion",
                "readability_requirements": [
                    "high contrast against background",
                    "distinct silhouette from hazards and pickups",
                ],
                "suggested_new_theme_variants": [
                    "neon archaeology",
                    "paper automata",
                    "signal garden",
                ],
                "prohibited_similarity_rules": list(PROHIBITED_SIMILARITY_RULES),
                "originality_guard": {
                    "perceptual_hash_comparison": "required",
                    "silhouette_similarity_comparison": "required",
                    "palette_similarity_comparison": "required",
                    "human_review_required": True,
                },
            }
        )
    return {"recipes": recipes}


def write_asset_recipes(payload: dict[str, list[dict[str, object]]], output_path: Path) -> Path:
    ensure_public_output_path(output_path)
    ensure_no_private_paths(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return output_path


def _size_class(width: float, height: float) -> str:
    area = width * height
    if area <= 16:
        return "small"
    if area <= 64:
        return "medium"
    return "large"

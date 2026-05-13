from __future__ import annotations

from pathlib import Path

import yaml

from asset_recipe_generator import generate_asset_recipes


def test_generated_asset_recipes_are_abstract_and_guarded(tmp_path: Path) -> None:
    entity_candidates_path = tmp_path / "entity_candidates.yaml"
    entity_candidates_path.write_text(
        yaml.safe_dump(
            {
                "entity_candidates": [
                    {
                        "candidate_id": "candidate_001",
                        "bbox_stats": {"mean_width": 8, "mean_height": 8},
                        "motion_stats": {"changed_pixel_ratio": 0.2, "travel_frames": 1},
                        "observed_frame_ranges": [{"start_frame": 0, "end_frame": 1}],
                        "interaction_hints": ["movement_detected"],
                        "animation_estimate": {"frame_count": 2},
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    output_path = tmp_path / "specs" / "asset_recipes.generated.yaml"
    generate_asset_recipes(entity_candidates_path, output_path)
    payload = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    recipe = payload["recipes"][0]
    serialized = yaml.safe_dump(recipe, sort_keys=False).lower()

    assert "evidence/private" not in output_path.read_text(encoding="utf-8")
    assert recipe["originality_guard"]["human_review_required"] is True
    assert recipe["prohibited_similarity_rules"]
    assert "/crops/" not in serialized
    assert ".png" not in serialized

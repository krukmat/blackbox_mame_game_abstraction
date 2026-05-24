"""T10.6-A — GNGVisionConfig: game-specific numeric thresholds for the vision layer.

All fields are calibrated for GNG at 256x224 native resolution.
A different game requires a separate config instance (same pattern as ArthurSignature).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class GNGVisionConfig:
    hud_y_top: int = 204          # rows >= hud_y_top are masked (bottom 20px of 224px frame)
    min_contour_area: int = 32    # T10.6-E sweep: 32 eliminates hazard noise (72k→0); was 4
    diff_threshold: int = 10      # grayscale diff threshold — pixels > this count as changed
    player_gap_tolerance: int = 60  # T10.4 tuning: bridge MOG2 player gaps without masking respawn-delay deaths
    mog2_history: int = 300
    mog2_var_threshold: float = 16.0
    mog2_warmup_frames: int = 50
    reset_on_scroll: bool = True  # MOG2 reset on camera scroll — not implemented until T12

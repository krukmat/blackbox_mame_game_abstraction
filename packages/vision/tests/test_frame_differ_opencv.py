"""T10.6-A/B — Smoke tests and HUD ROI mask tests."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HARNESS_DIR = ROOT / "apps" / "mame-harness"
VISION_DIR = ROOT / "packages" / "vision"

for candidate in (ROOT, HARNESS_DIR, VISION_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)


def test_cv2_is_importable() -> None:
    """T10.6-A: opencv-python-headless must be installed in the project venv."""
    import cv2  # noqa: F401
    assert cv2.__version__, "cv2.__version__ should be non-empty"


def test_gng_vision_config_is_importable() -> None:
    """T10.6-A: GNGVisionConfig skeleton must be importable."""
    from gng_vision_config import GNGVisionConfig  # noqa: F401
    cfg = GNGVisionConfig()
    assert cfg.hud_y_top == 204
    assert cfg.min_contour_area == 32  # T10.6-E: swept default changed from 4 to 32
    assert cfg.diff_threshold == 10
    assert cfg.player_gap_tolerance == 60  # T10.4 tuning: bridges long MOG2 player gaps in manual capture


def test_frame_differ_backend_protocol_is_importable() -> None:
    """T10.6-A: FrameDifferBackend Protocol and PurePythonBackend must be importable."""
    from frame_differ import FrameDifferBackend, PurePythonBackend  # noqa: F401
    backend = PurePythonBackend()
    assert hasattr(backend, "find_regions")


def test_frame_differ_default_backend_is_pure_python() -> None:
    """T10.6-A: FrameDiffer() with no args uses PurePythonBackend — behavior unchanged."""
    from frame_differ import FrameDiffer, PurePythonBackend
    differ = FrameDiffer()
    assert isinstance(differ._backend, PurePythonBackend)


def test_frame_differ_accepts_custom_backend() -> None:
    """T10.6-A: FrameDiffer(backend=...) accepts an explicit backend instance."""
    from frame_differ import FrameDiffer, PurePythonBackend
    backend = PurePythonBackend()
    differ = FrameDiffer(backend=backend)
    assert differ._backend is backend


# ---------------------------------------------------------------------------
# T10.6-B — HUD ROI mask tests
# ---------------------------------------------------------------------------

def _blank(width: int = 8, height: int = 230) -> list[list[int]]:
    return [[0] * width for _ in range(height)]


def _with_rows(
    base: list[list[int]],
    rows: list[int],
    value: int = 255,
) -> list[list[int]]:
    result = [row[:] for row in base]
    for y in rows:
        for x in range(len(result[y])):
            result[y][x] = value
    return result


def test_hud_only_changes_produce_no_regions() -> None:
    """T10.6-B: changes only in rows >= hud_y_top → changed_regions == []."""
    from frame_differ import PurePythonBackend
    from gng_vision_config import GNGVisionConfig

    cfg = GNGVisionConfig(hud_y_top=204)
    backend = PurePythonBackend(config=cfg)

    previous = _blank()
    # Change 8 pixels forming a 2x4 block entirely inside the HUD zone (row 205)
    current = _with_rows(previous, rows=[205, 206, 207, 208])

    ratio, regions = backend.find_regions(previous, current, 8, 230)

    assert regions == [], f"Expected no regions, got {regions}"
    assert ratio == 0.0


def test_changes_above_and_below_hud_threshold() -> None:
    """T10.6-B: changes in row 100 and row 210 → only row-100 region returned."""
    from frame_differ import PurePythonBackend
    from gng_vision_config import GNGVisionConfig

    cfg = GNGVisionConfig(hud_y_top=204)
    backend = PurePythonBackend(config=cfg)

    previous = _blank(width=8, height=230)
    # Build a 2x2 block at (x=1,y=100) — above HUD
    current = [row[:] for row in previous]
    for y in (100, 101):
        for x in (1, 2):
            current[y][x] = 255
    # Also change a pixel in the HUD zone — must be ignored
    current[210][3] = 255

    ratio, regions = backend.find_regions(previous, current, 8, 230)

    assert len(regions) == 1
    assert regions[0].y == 100


def test_no_config_does_not_mask_hud_rows() -> None:
    """T10.6-B: PurePythonBackend() with no config still detects HUD-zone changes."""
    from frame_differ import PurePythonBackend

    backend = PurePythonBackend()  # no config — original behavior

    previous = _blank(width=8, height=230)
    current = [row[:] for row in previous]
    # 2x2 block in HUD zone
    for y in (205, 206):
        for x in (1, 2):
            current[y][x] = 255

    ratio, regions = backend.find_regions(previous, current, 8, 230)

    assert len(regions) == 1, "Without config, HUD rows must NOT be masked"


# ---------------------------------------------------------------------------
# T10.6-C — OpenCVBackend tests
# ---------------------------------------------------------------------------

def _make_frame(width: int, height: int, value: int = 0) -> list[list[int]]:
    return [[value] * width for _ in range(height)]


def _set_rect(
    frame: list[list[int]],
    x: int, y: int, w: int, h: int,
    value: int = 255,
) -> list[list[int]]:
    result = [row[:] for row in frame]
    for row in range(y, y + h):
        for col in range(x, x + w):
            result[row][col] = value
    return result


class TestOpenCVBackend:
    def _backend(self):
        from frame_differ import OpenCVBackend
        from gng_vision_config import GNGVisionConfig
        # T10.6-E: use min_contour_area=4 so small test blobs (2x2=4px) are detected;
        # production default is 32 (per parameter sweep), but unit tests use minimal fixtures.
        return OpenCVBackend(config=GNGVisionConfig(min_contour_area=4))

    def test_two_separated_blobs_produce_two_regions(self) -> None:
        """T10.6-C: two non-adjacent blobs → two MotionBox regions."""
        W, H = 32, 32
        prev = _make_frame(W, H)
        curr = _set_rect(_set_rect(prev, 1, 1, 2, 2), 20, 20, 2, 2)

        _, regions = self._backend().find_regions(prev, curr, W, H)

        assert len(regions) == 2

    def test_three_pixel_component_is_rejected(self) -> None:
        """T10.6-C: blob with area < min_contour_area (4) is filtered out."""
        W, H = 16, 16
        prev = _make_frame(W, H)
        # L-shaped 3-pixel blob
        curr = [row[:] for row in prev]
        curr[1][1] = 255
        curr[1][2] = 255
        curr[2][1] = 255

        _, regions = self._backend().find_regions(prev, curr, W, H)

        assert regions == []

    def test_four_pixel_component_is_kept(self) -> None:
        """T10.6-C: 2×2 blob (area=4) meets min_contour_area threshold."""
        W, H = 16, 16
        prev = _make_frame(W, H)
        curr = _set_rect(prev, 1, 1, 2, 2)

        _, regions = self._backend().find_regions(prev, curr, W, H)

        assert len(regions) == 1
        r = regions[0]
        assert (r.x, r.y, r.width, r.height) == (1, 1, 2, 2)

    def test_single_blob_produces_one_region(self) -> None:
        """T10.6-C: single contiguous blob → single MotionBox."""
        W, H = 16, 16
        prev = _make_frame(W, H)
        curr = _set_rect(prev, 2, 2, 4, 3)

        _, regions = self._backend().find_regions(prev, curr, W, H)

        assert len(regions) == 1
        r = regions[0]
        assert (r.x, r.y, r.width, r.height) == (2, 2, 4, 3)

    def test_no_change_produces_empty_regions(self) -> None:
        """T10.6-C: identical frames → empty region list and zero ratio."""
        W, H = 16, 16
        prev = _make_frame(W, H)

        ratio, regions = self._backend().find_regions(prev, prev, W, H)

        assert regions == []
        assert ratio == 0.0

    def test_hud_only_changes_produce_no_regions(self) -> None:
        """T10.6-C: changes only below hud_y_top (204) → empty regions."""
        W, H = 256, 224
        prev = _make_frame(W, H)
        curr = _set_rect(prev, 0, 210, 40, 4)  # entirely inside HUD zone

        _, regions = self._backend().find_regions(prev, curr, W, H)

        assert regions == []

    def test_sub_threshold_diff_not_detected(self) -> None:
        """T10.6-C: pixel change <= diff_threshold (10) is not detected."""
        W, H = 16, 16
        prev = _make_frame(W, H, value=100)
        curr = _set_rect(prev, 1, 1, 2, 2, value=108)  # delta=8, threshold=10

        _, regions = self._backend().find_regions(prev, curr, W, H)

        assert regions == []

    def test_above_threshold_diff_is_detected(self) -> None:
        """T10.6-C: pixel change > diff_threshold (10) is detected."""
        W, H = 16, 16
        prev = _make_frame(W, H, value=100)
        curr = _set_rect(prev, 1, 1, 2, 2, value=115)  # delta=15 > 10

        _, regions = self._backend().find_regions(prev, curr, W, H)

        assert len(regions) == 1

    def test_regions_sorted_by_area_descending(self) -> None:
        """T10.6-C: regions are sorted largest area first."""
        W, H = 32, 32
        prev = _make_frame(W, H)
        # large blob (4x4=16) and small blob (2x2=4)
        curr = _set_rect(_set_rect(prev, 1, 1, 4, 4), 20, 20, 2, 2)

        _, regions = self._backend().find_regions(prev, curr, W, H)

        assert len(regions) == 2
        assert regions[0].width * regions[0].height >= regions[1].width * regions[1].height

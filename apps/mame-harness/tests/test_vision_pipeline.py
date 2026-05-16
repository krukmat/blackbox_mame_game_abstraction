from __future__ import annotations

from pathlib import Path
import json

from PIL import Image

from entity_candidate_builder import EntityCandidateBuilder
from behavioral_diff import load_trace_entries
from frame_differ import FrameDiffer
from frame_manifest import FrameManifest, load_frame_pixels
import vision_pipeline
from vision_pipeline import extract_run_trace


def test_redacted_entity_candidates_do_not_expose_private_paths(tmp_path: Path) -> None:
    frames_dir = tmp_path / "evidence" / "private" / "run_demo" / "frames"
    frames_dir.mkdir(parents=True)
    _write_pgm(frames_dir / "frame_0000.pgm", [[0, 0], [0, 0]])
    _write_pgm(frames_dir / "frame_0001.pgm", [[0, 255], [0, 0]])

    manifest = FrameManifest.from_run("demo", frames_dir)
    diff_stats = FrameDiffer().diff_manifest(manifest)
    candidates = EntityCandidateBuilder().build(diff_stats)

    output_path = tmp_path / "specs" / "entity_candidates.json"
    EntityCandidateBuilder().write_public_output(candidates, output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["entity_candidates"]
    serialized = json.dumps(payload)
    assert "evidence/private" not in serialized
    assert "/frames/" not in serialized
    assert "/crops/" not in serialized


def test_frame_differ_outputs_numeric_stats_only(tmp_path: Path) -> None:
    frames_dir = tmp_path / "evidence" / "private" / "run_demo" / "frames"
    frames_dir.mkdir(parents=True)
    _write_pgm(frames_dir / "frame_0000.pgm", [[0, 0, 0], [0, 0, 0]])
    _write_pgm(frames_dir / "frame_0001.pgm", [[0, 0, 0], [255, 0, 0]])

    manifest = FrameManifest.from_run("demo", frames_dir)
    diff_stats = FrameDiffer().diff_manifest(manifest)

    public = diff_stats[0].to_public_dict()
    assert isinstance(public["changed_pixel_ratio"], float)
    assert set(public["changed_regions"][0]) == {"x", "y", "width", "height", "center_x", "center_y"}


# T10.2.1.2 — PNG support tests ------------------------------------------------


def test_from_run_reads_png_sequence_from_extracted_subdir(tmp_path: Path) -> None:
    # Evidence layout from T10.2.1.1: frames/extracted_png/%04d.png
    extracted_dir = tmp_path / "evidence" / "private" / "run_png" / "frames" / "extracted_png"
    extracted_dir.mkdir(parents=True)
    _write_png(extracted_dir / "0000.png", [[10, 20], [30, 40]])
    _write_png(extracted_dir / "0001.png", [[10, 20], [30, 80]])

    manifest = FrameManifest.from_run("run_png", extracted_dir)

    assert len(manifest.frames) == 2
    assert manifest.frames[0].frame_index == 0
    assert manifest.frames[1].frame_index == 1
    assert manifest.frames[0].width == 2
    assert manifest.frames[0].height == 2


def test_from_run_png_enforces_private_evidence_path(tmp_path: Path) -> None:
    # Paths outside evidence/private must be rejected by the guardrail
    public_dir = tmp_path / "specs" / "frames"
    public_dir.mkdir(parents=True)
    _write_png(public_dir / "0000.png", [[0, 0], [0, 0]])

    import pytest
    with pytest.raises(ValueError, match="private"):
        FrameManifest.from_run("run_bad", public_dir)


def test_load_frame_pixels_returns_grayscale_rows_for_png(tmp_path: Path) -> None:
    png_dir = tmp_path / "evidence" / "private" / "run_pix" / "frames" / "extracted_png"
    png_dir.mkdir(parents=True)
    path = png_dir / "0000.png"
    _write_png(path, [[10, 20, 30], [40, 50, 60]])

    rows = load_frame_pixels(path)

    assert len(rows) == 2
    assert len(rows[0]) == 3
    # Each pixel is an integer in [0, 255]
    for row in rows:
        for pixel in row:
            assert isinstance(pixel, int)
            assert 0 <= pixel <= 255


def test_from_run_png_empty_dir_returns_empty_manifest(tmp_path: Path) -> None:
    extracted_dir = tmp_path / "evidence" / "private" / "run_empty" / "frames" / "extracted_png"
    extracted_dir.mkdir(parents=True)

    manifest = FrameManifest.from_run("run_empty", extracted_dir)
    assert manifest.frames == []


def test_from_run_pgm_still_works_after_png_extension(tmp_path: Path) -> None:
    # Regression: existing PGM path must be unaffected by T10.2.1.2 changes
    frames_dir = tmp_path / "evidence" / "private" / "run_pgm2" / "frames"
    frames_dir.mkdir(parents=True)
    _write_pgm(frames_dir / "frame_0000.pgm", [[0, 0], [0, 0]])
    _write_pgm(frames_dir / "frame_0001.pgm", [[0, 128], [0, 0]])

    manifest = FrameManifest.from_run("run_pgm2", frames_dir)
    assert len(manifest.frames) == 2


def test_frame_differ_works_with_png_manifest(tmp_path: Path) -> None:
    extracted_dir = tmp_path / "evidence" / "private" / "run_diff" / "frames" / "extracted_png"
    extracted_dir.mkdir(parents=True)
    _write_png(extracted_dir / "0000.png", [[0, 0, 0], [0, 0, 0]])
    _write_png(extracted_dir / "0001.png", [[0, 0, 0], [200, 0, 0]])

    manifest = FrameManifest.from_run("run_diff", extracted_dir)
    stats = FrameDiffer().diff_manifest(manifest)

    assert len(stats) == 1
    assert stats[0].changed_pixel_ratio > 0.0


def test_extract_run_trace_writes_public_trace_from_png_sequence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(vision_pipeline, "ROOT", tmp_path)
    # T10.6-E: override production config so small test blobs (area=4) pass the filter
    from gng_vision_config import GNGVisionConfig
    monkeypatch.setattr(vision_pipeline, "_GNG_CONFIG", GNGVisionConfig(min_contour_area=4))

    extracted_dir = tmp_path / "evidence" / "private" / "run_demo" / "frames" / "extracted_png"
    extracted_dir.mkdir(parents=True)
    blank = [[0] * 8 for _ in range(8)]
    # T10.6-C: OpenCVBackend requires min_contour_area=4 — use 2x2 blob (area=4)
    frame1 = [row[:] for row in blank]
    for ry in (1, 2):
        for rx in (1, 2):
            frame1[ry][rx] = 255
    _write_png(extracted_dir / "0000.png", blank)
    _write_png(extracted_dir / "0001.png", frame1)

    input_plan = tmp_path / "plans" / "demo.yaml"
    input_plan.parent.mkdir(parents=True)
    input_plan.write_text(
        "\n".join(
            [
                "plan_name: demo_trace",
                "game_id: gngb",
                "steps:",
                "  - action: fire",
                "    frames: 2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    output = tmp_path / "specs" / "traces" / "gng_trace.json"
    written = extract_run_trace("demo", input_plan, output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    entries = load_trace_entries(output)

    assert written == output
    assert output.exists()
    assert len(payload["trace"]) == 1
    assert entries[0].events == ["spawn", "fire"]
    assert "evidence/private" not in json.dumps(payload)


# ---------------------------------------------------------------------------


def _write_pgm(path: Path, pixels: list[list[int]]) -> None:
    height = len(pixels)
    width = len(pixels[0])
    values = "\n".join(" ".join(str(value) for value in row) for row in pixels)
    path.write_text(f"P2\n{width} {height}\n255\n{values}\n", encoding="utf-8")


def _write_png(path: Path, pixels: list[list[int]]) -> None:
    """Write a grayscale PNG fixture using Pillow."""
    height = len(pixels)
    width = len(pixels[0]) if height > 0 else 0
    flat = bytes(v for row in pixels for v in row)
    img = Image.frombytes("L", (width, height), flat)
    img.save(path, format="PNG")

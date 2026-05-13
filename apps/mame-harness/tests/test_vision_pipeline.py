from __future__ import annotations

from pathlib import Path
import json

from entity_candidate_builder import EntityCandidateBuilder
from frame_differ import FrameDiffer
from frame_manifest import FrameManifest


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


def _write_pgm(path: Path, pixels: list[list[int]]) -> None:
    height = len(pixels)
    width = len(pixels[0])
    values = "\n".join(" ".join(str(value) for value in row) for row in pixels)
    path.write_text(f"P2\n{width} {height}\n255\n{values}\n", encoding="utf-8")

"""T11.2 — Tests for episode_extractor.

ST1: dataclass definitions and schema structure.
ST2: boundary detection, jump filter, episode count.
ST3-ST5: entity grouping, guardrails, file output.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from episode_extractor import Episode, EpisodeFrame, EpisodesArtifact, extract_episodes, validate_artifact, write_episodes

TRACE_PATH = Path("specs/traces/gng_trace.json")


# --- ST1: schema structure ---

def test_episode_frame_has_required_fields():
    frame = EpisodeFrame(
        frame=100,
        player={"x": 0.5, "y": 0.4, "velocity_x": 0.0, "velocity_y": 0.0, "state": "idle", "events": []},
        enemies=[{"entity_type": "enemy_a", "x": 0.8, "y": 0.4, "state": "idle", "events": []}],
        projectiles=[],
    )
    assert frame.frame == 100
    assert frame.player is not None
    assert isinstance(frame.enemies, list)
    assert isinstance(frame.projectiles, list)


def test_episode_has_required_fields():
    ep = Episode(id="episode_001", frame_start=100, frame_end=220, frames=[])
    assert ep.id == "episode_001"
    assert ep.frame_start == 100
    assert ep.frame_end == 220
    assert isinstance(ep.frames, list)


def test_episodes_artifact_is_list_container():
    ep = Episode(id="episode_001", frame_start=100, frame_end=220, frames=[])
    artifact = EpisodesArtifact(episodes=[ep])
    assert len(artifact.episodes) == 1
    assert artifact.episodes[0].id == "episode_001"


def test_episodes_artifact_serializes_to_dict():
    frame = EpisodeFrame(frame=100, player=None, enemies=[], projectiles=[])
    ep = Episode(id="episode_001", frame_start=100, frame_end=100, frames=[frame])
    artifact = EpisodesArtifact(episodes=[ep])
    result = dataclasses.asdict(artifact)
    assert "episodes" in result
    assert result["episodes"][0]["id"] == "episode_001"
    assert result["episodes"][0]["frames"][0]["frame"] == 100


def test_extract_episodes_raises_not_implemented():
    # kept as tombstone — replaced by ST2 tests below
    pass


# --- ST2: boundary detection + jump filter ---

def test_extract_episodes_returns_artifact():
    artifact = extract_episodes(TRACE_PATH)
    assert isinstance(artifact, EpisodesArtifact)


def test_extract_episodes_minimum_count():
    artifact = extract_episodes(TRACE_PATH)
    assert len(artifact.episodes) >= 3, (
        f"Expected >= 3 episodes, got {len(artifact.episodes)}"
    )


def test_each_episode_has_jump_start():
    artifact = extract_episodes(TRACE_PATH)
    for ep in artifact.episodes:
        jump_frames = [
            f for f in ep.frames
            if f.player and "jump_start" in f.player.get("events", [])
        ]
        assert jump_frames, f"{ep.id} has no jump_start events"


def test_episode_frame_range_is_valid():
    artifact = extract_episodes(TRACE_PATH)
    for ep in artifact.episodes:
        assert ep.frame_start <= ep.frame_end, (
            f"{ep.id}: frame_start {ep.frame_start} > frame_end {ep.frame_end}"
        )


def test_episode_frames_list_not_empty():
    artifact = extract_episodes(TRACE_PATH)
    for ep in artifact.episodes:
        assert ep.frames, f"{ep.id} has empty frames list"


# --- ST3: per-frame entity grouping ---

def test_episode_frames_have_entity_lists():
    artifact = extract_episodes(TRACE_PATH)
    for ep in artifact.episodes:
        for frame in ep.frames:
            assert isinstance(frame.enemies, list)
            assert isinstance(frame.projectiles, list)


def test_enemy_entries_have_no_entity_id():
    artifact = extract_episodes(TRACE_PATH)
    for ep in artifact.episodes:
        for frame in ep.frames:
            for enemy in frame.enemies:
                assert "entity_id" not in enemy, (
                    f"entity_id leaked into enemy dict at frame {frame.frame}"
                )


def test_projectile_entries_have_no_entity_id():
    artifact = extract_episodes(TRACE_PATH)
    for ep in artifact.episodes:
        for frame in ep.frames:
            for proj in frame.projectiles:
                assert "entity_id" not in proj, (
                    f"entity_id leaked into projectile dict at frame {frame.frame}"
                )


def test_coordinates_are_normalized():
    artifact = extract_episodes(TRACE_PATH)
    for ep in artifact.episodes:
        for frame in ep.frames:
            if frame.player:
                assert 0.0 <= frame.player["x"] <= 1.0
                assert 0.0 <= frame.player["y"] <= 1.0
            for enemy in frame.enemies:
                assert 0.0 <= enemy["x"] <= 1.0
                assert 0.0 <= enemy["y"] <= 1.0
            for proj in frame.projectiles:
                assert 0.0 <= proj["x"] <= 1.0
                assert 0.0 <= proj["y"] <= 1.0


# --- ST4: guardrails ---

def test_validate_artifact_passes_on_real_output():
    artifact = extract_episodes(TRACE_PATH)
    output_path = Path("specs/episodes/gng_episodes.json")
    validate_artifact(artifact, output_path)  # must not raise


def test_validate_artifact_rejects_blocked_suffix():
    artifact = extract_episodes(TRACE_PATH)
    with pytest.raises(ValueError, match="blocked public output suffix"):
        validate_artifact(artifact, Path("specs/episodes/gng_episodes.png"))


# --- ST5: file write + acceptance criteria ---

def test_write_episodes_creates_file(tmp_path):
    artifact = extract_episodes(TRACE_PATH)
    output = tmp_path / "episodes" / "gng_episodes.json"
    write_episodes(artifact, output)
    assert output.exists()


def test_written_file_size_under_500kb(tmp_path):
    artifact = extract_episodes(TRACE_PATH)
    output = tmp_path / "gng_episodes.json"
    write_episodes(artifact, output)
    size_kb = output.stat().st_size / 1024
    assert size_kb <= 500, f"File size {size_kb:.1f} KB exceeds 500 KB limit"


def test_written_file_contains_valid_episodes(tmp_path):
    artifact = extract_episodes(TRACE_PATH)
    output = tmp_path / "gng_episodes.json"
    write_episodes(artifact, output)
    data = json.loads(output.read_text())
    episodes = data["episodes"]
    assert len(episodes) >= 3
    for ep in episodes:
        jump_frames = [
            f for f in ep["frames"]
            if f["player"] and "jump_start" in f["player"].get("events", [])
        ]
        assert jump_frames, f"{ep['id']} has no jump_start events in written file"


def test_validate_artifact_rejects_private_path_in_payload():
    frame = EpisodeFrame(
        frame=1,
        player={"x": 0.5, "y": 0.4, "velocity_x": 0.0, "velocity_y": 0.0,
                "state": "idle", "events": ["evidence/private/run_abc/frames/001.png"]},
        enemies=[],
        projectiles=[],
    )
    ep = Episode(id="episode_001", frame_start=1, frame_end=1, frames=[frame])
    artifact = EpisodesArtifact(episodes=[ep])
    with pytest.raises(ValueError, match="private path leaked"):
        validate_artifact(artifact, Path("specs/episodes/gng_episodes.json"))

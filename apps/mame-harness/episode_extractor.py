"""T11.2 — Trace Episode Extractor.

Converts specs/traces/gng_trace.json into compact episode segments
at specs/episodes/gng_episodes.json for RN prototype consumption.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from guardrails import ensure_no_private_paths, ensure_public_output_path


@dataclasses.dataclass(slots=True)
class EpisodeFrame:
    frame: int
    player: dict | None
    enemies: list[dict]
    projectiles: list[dict]


@dataclasses.dataclass(slots=True)
class Episode:
    id: str
    frame_start: int
    frame_end: int
    frames: list[EpisodeFrame]


@dataclasses.dataclass(slots=True)
class EpisodesArtifact:
    episodes: list[Episode]


GAP_THRESHOLD = 30      # frames of missing player that cut an episode boundary
MAX_EPISODE_FRAMES = 60  # maximum frames per episode (~1s at 16.7ms/frame; keeps output ≤ 500 KB)
MAX_EPISODES = 10        # maximum episodes returned


def _load_frame_index(trace_path: Path) -> dict[int, list[dict]]:
    """Index all trace entries by frame number — O(n) single pass."""
    with trace_path.open() as fh:
        data = json.load(fh)
    index: dict[int, list[dict]] = {}
    for entry in data["trace"]:
        index.setdefault(entry["frame"], []).append(entry)
    return index


def _player_entry(frame_entries: list[dict]) -> dict | None:
    for entry in frame_entries:
        if entry.get("entity_id") == "player":
            return entry
    return None


def _has_jump_start(player_entries: list[dict]) -> bool:
    return any("jump_start" in e.get("events", []) for e in player_entries)


def _build_episode_frames(
    frame_index: dict[int, list[dict]],
    run_frames: list[int],
) -> list[EpisodeFrame]:
    """Build EpisodeFrame list for a run — T11.2-ST3 fills enemies/projectiles."""
    frames: list[EpisodeFrame] = []
    for frame_num in run_frames:
        entries = frame_index.get(frame_num, [])
        player = _player_entry(entries)
        if player is None:
            continue

        enemies: list[dict] = []
        projectiles: list[dict] = []
        for entry in entries:
            entity_type = entry.get("entity_type", "")
            if entity_type == "enemy_a":
                # entity_id excluded — ADR-006: numeric output only
                enemies.append({
                    "entity_type": entity_type,
                    "x": entry["x"],
                    "y": entry["y"],
                    "state": entry["state"],
                    "events": entry["events"],
                })
            elif entity_type == "projectile":
                projectiles.append({
                    "entity_type": entity_type,
                    "x": entry["x"],
                    "y": entry["y"],
                    "state": entry["state"],
                })

        frames.append(EpisodeFrame(
            frame=frame_num,
            player={
                "x": player["x"],
                "y": player["y"],
                "velocity_x": player["velocity_x"],
                "velocity_y": player["velocity_y"],
                "state": player["state"],
                "events": player["events"],
            },
            enemies=enemies,
            projectiles=projectiles,
        ))
    return frames


def extract_episodes(trace_path: Path) -> EpisodesArtifact:  # T11.2-ST2
    """Detect episode boundaries by player-frame gaps and filter for jump coverage."""
    frame_index = _load_frame_index(trace_path)

    # sorted frames that contain a player entry
    player_frames = sorted(f for f, entries in frame_index.items() if _player_entry(entries))

    # accumulate runs: split when gap > GAP_THRESHOLD
    runs: list[list[int]] = []
    current_run: list[int] = []
    for i, frame in enumerate(player_frames):
        if not current_run or frame - player_frames[i - 1] <= GAP_THRESHOLD:
            current_run.append(frame)
        else:
            runs.append(current_run)
            current_run = [frame]
    if current_run:
        runs.append(current_run)

    # filter and cap each run, keep only those with >= 1 jump_start
    episodes: list[Episode] = []
    for idx, run in enumerate(runs):
        capped = run[:MAX_EPISODE_FRAMES]
        player_entries_in_run = [
            _player_entry(frame_index.get(f, [])) for f in capped
        ]
        player_entries_in_run = [e for e in player_entries_in_run if e is not None]
        if not _has_jump_start(player_entries_in_run):
            continue
        ep_frames = _build_episode_frames(frame_index, capped)
        episodes.append(Episode(
            id=f"episode_{len(episodes) + 1:03d}",
            frame_start=capped[0],
            frame_end=capped[-1],
            frames=ep_frames,
        ))
        if len(episodes) >= MAX_EPISODES:
            break

    return EpisodesArtifact(episodes=episodes)


def validate_artifact(artifact: EpisodesArtifact, output_path: Path) -> None:  # T11.2-ST4
    """Enforce ADR-003/ADR-006 guardrails before writing the public artifact."""
    ensure_public_output_path(output_path)
    ensure_no_private_paths(dataclasses.asdict(artifact))


def write_episodes(artifact: EpisodesArtifact, output_path: Path) -> None:  # T11.2-ST5
    """Write episodes artifact to disk after guardrail validation."""
    validate_artifact(artifact, output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as fh:
        json.dump(dataclasses.asdict(artifact), fh, indent=2)

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

# T10.5-C.4.c.2.b: canonical T09.2 vocabulary used for multi-entity output validation.
VALID_STATES_T09_2: frozenset[str] = frozenset({
    "idle", "walking_left", "walking_right",
    "grounded", "airborne", "ascending", "descending",
    "in_flight", "hit", "dead", "despawned",
})

VALID_EVENTS_T09_2: frozenset[str] = frozenset({
    "spawn", "die", "despawn",
    "hit", "hit_enemy", "hit_player",
    "movement_start", "movement_stop",
    "jump_start", "jump_peak", "land", "fall",
    "fire", "hit_wall",
    "score",
})

ROOT = Path(__file__).resolve().parents[3]
HARNESS_DIR = ROOT / "apps" / "mame-harness"
VISION_DIR = ROOT / "packages" / "vision"
VALIDATION_DIR = ROOT / "packages" / "validation"

for candidate in (ROOT, HARNESS_DIR, VISION_DIR, VALIDATION_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from arthur_tracker import ArthurSignature, ArthurTracker
from frame_differ import FrameDiffStat, MotionBox
from guardrails import ensure_no_private_paths
from input_planner import InputPlan, InputStep
from trace_extractor import extract_trace


FRAME_W = 256
FRAME_H = 224


def _plan(*actions: str) -> InputPlan:
    return InputPlan(
        plan_name="t10_5_multi",
        game_id="gngb",
        steps=[InputStep(action=action, frames=1) for action in actions],
    )


def _region(
    cx: float,
    cy: float,
    width: int,
    height: int,
) -> MotionBox:
    return MotionBox(
        x=int(cx - (width / 2)),
        y=int(cy - (height / 2)),
        width=width,
        height=height,
        center_x=cx,
        center_y=cy,
    )


def _stat(start_frame: int, *regions: MotionBox) -> FrameDiffStat:
    return FrameDiffStat(
        start_frame=start_frame,
        end_frame=start_frame + 1,
        changed_pixel_ratio=0.01,
        changed_regions=list(regions),
    )


def _player_region(cx: float, cy: float) -> MotionBox:
    # width=22, height=25 → ar=0.88 — calibrated from GNG manual_01 Arthur sprite
    return _region(cx, cy, width=22, height=25)


def _enemy_region(cx: float, cy: float) -> MotionBox:
    return _region(cx, cy, width=14, height=18)


def _projectile_region(cx: float, cy: float) -> MotionBox:
    return _region(cx, cy, width=6, height=6)


class TestExtractTraceMultiEntity:
    def test_player_signature_region_emits_player_entry(self) -> None:
        stats = [_stat(0, _player_region(90.0, 170.0))]

        result = extract_trace(stats, _plan("noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        assert [entry.entity_id for entry in result] == ["player"]
        assert [entry.entity_type for entry in result] == ["player"]

    def test_no_player_signature_region_emits_no_player_entry(self) -> None:
        stats = [_stat(0, _enemy_region(90.0, 130.0))]

        result = extract_trace(stats, _plan("noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        assert all(entry.entity_id != "player" for entry in result)

    def test_player_and_enemy_regions_in_same_frame_emit_two_entries(self) -> None:
        stats = [_stat(0, _player_region(90.0, 170.0), _enemy_region(150.0, 130.0))]

        result = extract_trace(stats, _plan("noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        assert len(result) == 2
        assert {entry.entity_type for entry in result} == {"player", "enemy_a"}

    def test_enemy_region_without_player_still_emits_enemy_entry(self) -> None:
        stats = [_stat(0, _enemy_region(150.0, 130.0))]

        result = extract_trace(stats, _plan("noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        assert len(result) == 1
        assert result[0].entity_type == "enemy_a"

    def test_player_prev_state_does_not_bleed_from_enemy_prev_state(self) -> None:
        stats = [
            _stat(0, _enemy_region(40.0, 120.0)),
            _stat(1, _player_region(90.0, 170.0), _enemy_region(70.0, 120.0)),
        ]

        result = extract_trace(stats, _plan("noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        player_entries = [entry for entry in result if entry.entity_id == "player"]
        assert player_entries
        assert "movement_start" not in player_entries[0].events

    def test_enemy_without_prior_entry_defaults_to_idle_and_zero_velocity(self) -> None:
        stats = [_stat(0, _enemy_region(150.0, 130.0))]

        result = extract_trace(stats, _plan("noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        assert result[0].state == "idle"
        assert result[0].velocity_x == 0.0
        assert result[0].velocity_y == 0.0

    def test_player_receives_exactly_one_spawn_across_sequence(self) -> None:
        stats = [
            _stat(0, _player_region(90.0, 170.0)),
            _stat(1, _player_region(96.0, 170.0)),
            _stat(2, _player_region(102.0, 170.0)),
        ]

        result = extract_trace(stats, _plan("noop", "move_right", "move_right"), frame_width=FRAME_W, frame_height=FRAME_H)

        player_spawns = [
            entry for entry in result if entry.entity_id == "player" and "spawn" in entry.events
        ]
        assert len(player_spawns) == 1

    def test_new_enemy_region_receives_spawn(self) -> None:
        stats = [_stat(0, _enemy_region(150.0, 130.0))]

        result = extract_trace(stats, _plan("noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        assert "spawn" in result[0].events

    # --- T10.5-C.4.b: multi-entity spawn emission ---

    def test_player_spawn_only_on_first_frame_not_on_return(self) -> None:
        # Player absent frame 0, present frames 1-2 — spawn only on frame 1.
        stats = [
            _stat(0, _enemy_region(150.0, 130.0)),
            _stat(1, _player_region(90.0, 170.0)),
            _stat(2, _player_region(96.0, 170.0)),
        ]

        result = extract_trace(stats, _plan("noop", "noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        player_spawns = [e for e in result if e.entity_id == "player" and "spawn" in e.events]
        assert len(player_spawns) == 1
        assert player_spawns[0].frame == 1

    def test_two_enemy_regions_in_same_frame_each_receive_spawn(self) -> None:
        # Two separate enemy regions on the same frame → two independent spawn events.
        enemy1 = _enemy_region(60.0, 120.0)
        enemy2 = _enemy_region(200.0, 120.0)
        stats = [_stat(0, enemy1, enemy2)]

        result = extract_trace(stats, _plan("noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        enemy_entries = [e for e in result if e.entity_type == "enemy_a"]
        assert len(enemy_entries) == 2
        assert all("spawn" in e.events for e in enemy_entries)

    # --- T10.5-C.4.c.1: disappearance detection by entity_id ---

    def test_enemy_disappearing_while_player_stays_gets_die(self) -> None:
        # frame 0: player + enemy present; frame 1: only player — enemy must get die.
        stats = [
            _stat(0, _player_region(90.0, 170.0), _enemy_region(150.0, 130.0)),
            _stat(1, _player_region(96.0, 170.0)),
        ]

        result = extract_trace(stats, _plan("noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        enemy_entries = [e for e in result if e.entity_type == "enemy_a"]
        assert len(enemy_entries) == 1
        assert "die" in enemy_entries[0].events
        player_entries = [e for e in result if e.entity_id == "player"]
        assert all("die" not in e.events for e in player_entries)

    def test_two_enemies_disappear_independently(self) -> None:
        # frame 0: two enemies; frame 1: empty — both must get die, independently.
        enemy1 = _enemy_region(60.0, 120.0)
        enemy2 = _enemy_region(200.0, 120.0)
        stats = [
            _stat(0, enemy1, enemy2),
            _stat(1),  # empty frame
        ]

        result = extract_trace(stats, _plan("noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        enemy_entries = [e for e in result if e.entity_type == "enemy_a"]
        assert len(enemy_entries) == 2
        assert all("die" in e.events for e in enemy_entries)

    def test_player_disappearance_does_not_affect_enemy_entry(self) -> None:
        # frame 0: player + enemy; frame 1: only enemy — player gets die, enemy does not.
        stats = [
            _stat(0, _player_region(90.0, 170.0), _enemy_region(150.0, 130.0)),
            _stat(1, _enemy_region(160.0, 130.0)),
        ]

        result = extract_trace(stats, _plan("noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        player_frame0 = [e for e in result if e.entity_id == "player" and e.frame == 0]
        assert len(player_frame0) == 1
        assert "die" in player_frame0[0].events
        enemy_frame1 = [e for e in result if e.entity_type == "enemy_a" and e.frame == 1]
        assert all("die" not in e.events for e in enemy_frame1)

    # --- T10.5-C.4.c.2.a: last-entry target resolution by entity_id ---

    def test_die_resolves_to_correct_entity_not_player(self) -> None:
        # frame 0: player + enemy; frame 1: only player.
        # die must land on enemy entry frame 0, not on player entry frame 0.
        stats = [
            _stat(0, _player_region(90.0, 170.0), _enemy_region(150.0, 130.0)),
            _stat(1, _player_region(96.0, 170.0)),
        ]

        result = extract_trace(stats, _plan("noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        player_f0 = next(e for e in result if e.entity_id == "player" and e.frame == 0)
        enemy_f0 = next(e for e in result if e.entity_type == "enemy_a" and e.frame == 0)
        assert "die" not in player_f0.events
        assert "die" in enemy_f0.events

    def test_two_disappearing_enemies_resolve_to_own_entries(self) -> None:
        # frame 0: two enemies at different positions; frame 1: empty.
        # Each enemy must receive die on its own frame-0 entry.
        enemy1 = _enemy_region(60.0, 120.0)
        enemy2 = _enemy_region(200.0, 120.0)
        stats = [
            _stat(0, enemy1, enemy2),
            _stat(1),
        ]

        result = extract_trace(stats, _plan("noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        enemy_entries = [e for e in result if e.entity_type == "enemy_a"]
        assert len(enemy_entries) == 2
        assert all("die" in e.events for e in enemy_entries)
        # Verify die is not duplicated on either entry
        assert all(e.events.count("die") == 1 for e in enemy_entries)

    def test_entity_id_with_no_prior_entry_skipped_without_crash(self) -> None:
        # Empty frame after empty frame — prev_seen_by_id is empty, nothing to resolve.
        stats = [_stat(0), _stat(1)]

        result = extract_trace(stats, _plan("noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        assert result == []

    def test_full_trace_output_passes_private_path_guardrail(self) -> None:
        stats = [
            _stat(0, _player_region(90.0, 170.0), _enemy_region(150.0, 130.0)),
            _stat(1, _player_region(96.0, 170.0)),
        ]

        result = extract_trace(stats, _plan("noop", "move_right"), frame_width=FRAME_W, frame_height=FRAME_H)

        ensure_no_private_paths([asdict(entry) for entry in result])

    def test_tracker_contract_is_available_for_multi_entity_trace_work(self) -> None:
        sig = ArthurSignature()
        tracker = ArthurTracker()

        assert sig.height_min_px == 24
        assert tracker is not None

    # --- T10.5-C.4.c.2.b: die event mutation + dedup ---

    def test_die_annotated_on_last_entry_of_disappearing_entity(self) -> None:
        # Mutation pass: enemy present frame 0, absent frame 1 → die appended to frame 0 entry.
        stats = [
            _stat(0, _enemy_region(150.0, 130.0)),
            _stat(1),
        ]

        result = extract_trace(stats, _plan("noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        enemy_f0 = [e for e in result if e.entity_type == "enemy_a" and e.frame == 0]
        assert len(enemy_f0) == 1
        assert "die" in enemy_f0[0].events

    def test_die_not_duplicated_when_multiple_entities_disappear_same_step(self) -> None:
        # Dedup guard: player + enemy disappear; no entry must carry die more than once.
        stats = [
            _stat(0, _player_region(90.0, 170.0), _enemy_region(150.0, 130.0)),
            _stat(1, _player_region(96.0, 170.0)),  # enemy absent
            _stat(2),                                # player absent
        ]

        result = extract_trace(stats, _plan("noop", "noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        for entry in result:
            assert entry.events.count("die") <= 1, (
                f"die duplicated on entity={entry.entity_id} frame={entry.frame}: {entry.events}"
            )

    def test_die_does_not_cross_annotate_player_entry_on_enemy_disappearance(self) -> None:
        # No-cross-annotation: mutation for disappearing enemy must not touch player's same-frame entry.
        stats = [
            _stat(0, _player_region(90.0, 170.0), _enemy_region(150.0, 130.0)),
            _stat(1, _player_region(96.0, 170.0)),
        ]

        result = extract_trace(stats, _plan("noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        player_f0 = next(e for e in result if e.entity_id == "player" and e.frame == 0)
        assert "die" not in player_f0.events

    def test_die_does_not_cross_annotate_new_enemy_entry_on_player_disappearance(self) -> None:
        # No-cross-annotation: player disappears at frame 1 → die on player frame 0 entry, not on new frame-1 enemy.
        stats = [
            _stat(0, _player_region(90.0, 170.0)),
            _stat(1, _enemy_region(150.0, 130.0)),
        ]

        result = extract_trace(stats, _plan("noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        enemy_f1 = [e for e in result if e.entity_type == "enemy_a" and e.frame == 1]
        assert all("die" not in e.events for e in enemy_f1)

    def test_die_mutation_output_passes_ensure_no_private_paths(self) -> None:
        # ensure_no_private_paths: the die mutation pass must not introduce path strings.
        stats = [
            _stat(0, _player_region(90.0, 170.0), _enemy_region(150.0, 130.0)),
            _stat(1, _player_region(96.0, 170.0)),  # enemy disappears → die mutated
            _stat(2),                                # player disappears → die mutated
        ]

        result = extract_trace(stats, _plan("noop", "noop", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        ensure_no_private_paths([asdict(entry) for entry in result])

    def test_all_states_in_canonical_t09_2_vocabulary_multi_entity(self) -> None:
        # Canonical vocabulary: every state string emitted by multi-entity extract_trace is T09.2-valid.
        stats = [
            _stat(0, _player_region(90.0, 170.0), _enemy_region(150.0, 130.0)),
            _stat(1, _player_region(96.0, 170.0), _projectile_region(180.0, 170.0)),
            _stat(2, _player_region(102.0, 170.0)),
        ]

        result = extract_trace(stats, _plan("noop", "fire", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        for entry in result:
            assert entry.state in VALID_STATES_T09_2, (
                f"non-canonical state '{entry.state}' on entity={entry.entity_id} frame={entry.frame}"
            )

    def test_all_events_in_canonical_t09_2_vocabulary_multi_entity(self) -> None:
        # Canonical vocabulary: every event string emitted by multi-entity extract_trace is T09.2-valid.
        stats = [
            _stat(0, _player_region(90.0, 170.0), _enemy_region(150.0, 130.0)),
            _stat(1, _player_region(96.0, 170.0), _projectile_region(180.0, 170.0)),
            _stat(2, _player_region(102.0, 170.0)),
        ]

        result = extract_trace(stats, _plan("noop", "fire", "noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        for entry in result:
            for event in entry.events:
                assert event in VALID_EVENTS_T09_2, (
                    f"non-canonical event '{event}' on entity={entry.entity_id} frame={entry.frame}"
                )


# ---------------------------------------------------------------------------
# T10.7.B — Entity-ID collision fix regression tests
# ---------------------------------------------------------------------------

from trace_extractor import _entity_type_from_box  # noqa: E402


class TestEntityTypeFromBoxAllowPlayer:
    """T10.7.B: verify allow_player flag prevents collision when player slot is claimed."""

    def test_entity_type_returns_player_when_allow_player_default(self) -> None:
        # Large blob (22×25 = 550 px; ratio ≈ 0.096 > _RATIO_PLAYER=0.04) → "player" by default.
        region = _player_region(90.0, 170.0)
        result = _entity_type_from_box(region, FRAME_W, FRAME_H)
        assert result == "player"

    def test_entity_type_returns_enemy_a_when_allow_player_false(self) -> None:
        # Same large blob with allow_player=False must fall through to enemy_a classification.
        region = _player_region(90.0, 170.0)
        result = _entity_type_from_box(region, FRAME_W, FRAME_H, allow_player=False)
        assert result == "enemy_a"

    def test_entity_type_still_classifies_projectile_when_allow_player_false(self) -> None:
        # Projectile-sized blob (6×6): ratio ≈ 0.00099 < _RATIO_ENEMY_A=0.004 → "projectile".
        # allow_player=False must not break smaller categories.
        region = _projectile_region(128.0, 112.0)
        result = _entity_type_from_box(region, FRAME_W, FRAME_H, allow_player=False)
        assert result == "projectile"

    def test_extract_trace_two_player_sized_blobs_emits_one_player_one_enemy(self) -> None:
        # Integration: one frame with Arthur + another player-sized blob.
        # Arthur is detected by find_arthur (within signature bounds, leftmost).
        # The second player-sized blob must be classified as enemy_a, not "player".
        # Result: exactly 1 entity_id="player", 1 entity_id starts with "enemy_a".
        arthur = _player_region(90.0, 170.0)   # within ArthurSignature bounds
        impostor = _player_region(200.0, 130.0)  # player-sized but not Arthur

        stats = [_stat(0, arthur, impostor)]
        result = extract_trace(stats, _plan("noop"), frame_width=FRAME_W, frame_height=FRAME_H)

        player_entries = [e for e in result if e.entity_id == "player"]
        enemy_entries = [e for e in result if e.entity_id.startswith("enemy_a")]

        assert len(player_entries) == 1, (
            f"Expected 1 player entry, got {len(player_entries)}: {[e.entity_id for e in result]}"
        )
        assert len(enemy_entries) == 1, (
            f"Expected 1 enemy_a entry, got {len(enemy_entries)}: {[e.entity_id for e in result]}"
        )

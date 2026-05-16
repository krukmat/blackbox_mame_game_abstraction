"""T10.2.2.2/3/4 — Velocity computation, state assignment, event inference, trace assembly.

Implements Rules 1–6 from the translation contract (T10.2.2.1).
All thresholds are expressed as frame-dimension ratios — no pixel values.
All state/event strings are drawn from T09.2 canonical vocabulary.
"""
from __future__ import annotations

from arthur_tracker import ArthurSignature, ArthurTracker
from frame_differ import FrameDiffStat, MotionBox

# Lazy imports for types that live outside packages/vision — resolved at call time
# to avoid hard coupling during unit tests that don't need them.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_planner import InputPlan
    from behavioral_diff import TraceEntry
    from gng_vision_config import GNGVisionConfig

# ---------------------------------------------------------------------------
# Threshold constants — T10.2.2.1 Rule 2
# These are ratios relative to frame width/height, not pixel counts.
# ---------------------------------------------------------------------------

VX_STILL: float = 0.005  # |vx| below this → no horizontal motion
VY_STILL: float = 0.005  # |vy| below this → no vertical motion


# ---------------------------------------------------------------------------
# Rule 1 — Velocity computation
# ---------------------------------------------------------------------------


def _compute_velocity(
    prev: FrameDiffStat | None,
    curr: FrameDiffStat,
    frame_width: int,
    frame_height: int,
) -> tuple[float, float]:
    """Return (velocity_x, velocity_y) normalized by frame dimensions.

    Returns (0.0, 0.0) when no motion baseline is available:
    - prev is None (first frame)
    - prev or curr has no changed_regions
    """
    if prev is None:
        return 0.0, 0.0
    if not prev.changed_regions or not curr.changed_regions:
        return 0.0, 0.0

    # Use the largest region by area as the primary region (T10.2.2.1 Rule 1)
    prev_region = max(prev.changed_regions, key=lambda r: r.width * r.height)
    curr_region = max(curr.changed_regions, key=lambda r: r.width * r.height)

    dx = curr_region.center_x - prev_region.center_x
    dy = curr_region.center_y - prev_region.center_y

    return dx / frame_width, dy / frame_height


def _compute_region_velocity(
    prev_region: MotionBox | None,
    curr_region: MotionBox | None,
    frame_width: int,
    frame_height: int,
) -> tuple[float, float]:
    if prev_region is None or curr_region is None:
        return 0.0, 0.0

    dx = curr_region.center_x - prev_region.center_x
    dy = curr_region.center_y - prev_region.center_y
    return dx / frame_width, dy / frame_height


# ---------------------------------------------------------------------------
# Rule 2 — State assignment
# ---------------------------------------------------------------------------


def _assign_state(vx: float, vy: float, entity_type: str) -> str:
    """Map (vx, vy, entity_type) to a canonical state string (T09.2 state.enum).

    Priority table applied top-to-bottom; first match wins.
    """
    # Priorities 1 & 2 — projectile type overrides velocity checks
    if entity_type == "projectile":
        return "in_flight" if vx != 0.0 else "despawned"

    # Priorities 3 & 4 — vertical motion
    if vy < -VY_STILL:
        return "ascending"
    if vy > VY_STILL:
        return "descending"

    # Priorities 5, 6, 7 — horizontal motion within vertical deadband
    if abs(vx) <= VX_STILL:
        return "idle"
    if vx < -VX_STILL:
        return "walking_left"
    if vx > VX_STILL:
        return "walking_right"

    # Priority 8 — any remaining vertical motion (should not be reached after
    # the checks above, kept as safety net for floating-point edge cases)
    if abs(vy) > VY_STILL:
        return "airborne"

    # Priority 9 — fallback
    return "grounded"


# ---------------------------------------------------------------------------
# Rule 3 + Rule 4 — Event inference
# T10.2.2.3
# ---------------------------------------------------------------------------

# States that represent "on the ground" for transition purposes
_GROUNDED_STATES: frozenset[str] = frozenset({"grounded", "idle"})

# States that represent "airborne" for fall detection
_AIRBORNE_STATES: frozenset[str] = frozenset({"airborne", "descending"})

# States that are walking (horizontal locomotion)
_WALKING_STATES: frozenset[str] = frozenset({"walking_left", "walking_right"})

# All states that can transition into ascending (jump takeoff)
_PRE_JUMP_STATES: frozenset[str] = frozenset(
    {"grounded", "idle", "walking_left", "walking_right"}
)


def _infer_events(
    prev_state: str,
    curr_state: str,
    input_action: str,
) -> list[str]:
    """Return the event list for a single frame using Rule 3 and Rule 4.

    Rule 3: state transition table from T10.2.2.1.
    Rule 4: input plan injection — fire always; jump_start only when not already
            inferred from the transition and entity is not already ascending.

    All returned strings are members of T09.2 events.enum.
    land and fall are mutually exclusive.
    """
    events: list[str] = []

    # --- Rule 3: state transition table ---

    # Jump arc
    if prev_state in _PRE_JUMP_STATES and curr_state == "ascending":
        events.append("jump_start")
    elif prev_state == "ascending" and curr_state == "descending":
        events.append("jump_peak")
    elif prev_state in {"ascending", "descending", "airborne"} and curr_state in _GROUNDED_STATES:
        events.append("land")

    # Fall (walked off edge — grounded → airborne without jump)
    elif prev_state in _GROUNDED_STATES and curr_state in _AIRBORNE_STATES:
        events.append("fall")

    # Locomotion
    elif prev_state == "idle" and curr_state in _WALKING_STATES:
        events.append("movement_start")
    elif prev_state in _WALKING_STATES and curr_state == "idle":
        events.append("movement_stop")
    elif prev_state in _WALKING_STATES and curr_state in _WALKING_STATES and prev_state != curr_state:
        events.append("movement_stop")
        events.append("movement_start")

    # Projectile removal
    elif prev_state == "in_flight" and curr_state == "despawned":
        events.append("despawn")

    # --- Rule 4: input plan injection ---

    if input_action == "fire":
        events.append("fire")

    if input_action == "jump" and curr_state != "ascending":
        if "jump_start" not in events:
            events.append("jump_start")

    # Deduplication — preserve order, remove any accidental duplicates
    return list(dict.fromkeys(events))


# ---------------------------------------------------------------------------
# Rules 5 + 6 + assembly — extract_trace
# T10.2.2.4
# ---------------------------------------------------------------------------

# Rule 5 — box_ratio thresholds for entity_type assignment
_RATIO_PLAYER: float = 0.04
_RATIO_ENEMY_A: float = 0.004
_RATIO_PROJECTILE: float = 0.0005


def _entity_type_from_box(region: MotionBox, frame_width: int, frame_height: int) -> str:
    """Return entity_type string from T09.2 entity_type enum based on area ratio."""
    ratio = (region.width * region.height) / (frame_width * frame_height)
    if ratio >= _RATIO_PLAYER:
        return "player"
    if ratio >= _RATIO_ENEMY_A:
        return "enemy_a"
    if ratio >= _RATIO_PROJECTILE:
        return "projectile"
    return "hazard"


def _entity_id_from_type(entity_type: str, frame: int, region_index: int = 0) -> str:
    """Return a stable entity_id label with no copyright-protected names.

    region_index disambiguates multiple entities of the same type in the same frame.
    """
    if entity_type == "player":
        return "player"
    return f"{entity_type}_{frame}_{region_index}"


def _regions_except_claimed(
    regions: list[MotionBox],
    claimed_region: MotionBox | None,
) -> list[MotionBox]:
    if claimed_region is None:
        return list(regions)
    return [region for region in regions if region is not claimed_region]


def extract_trace(
    diff_stats: list[FrameDiffStat],
    input_plan: "InputPlan",
    frame_width: int = 256,
    frame_height: int = 224,
    config: "GNGVisionConfig | None" = None,
) -> list["TraceEntry"]:
    """Assemble a list of TraceEntry records from FrameDiffStat + InputPlan.

    One TraceEntry per frame per detected entity region.
    Applies Rules 1–6 from T10.2.2.1 in order.
    Output passes ensure_no_private_paths — no path strings are emitted.
    """
    from behavioral_diff import TraceEntry  # runtime import, safe per conftest sys.path

    frame_inputs = input_plan.expand_to_frames()
    # Index input frames by frame_index for O(1) lookup
    input_by_frame: dict[int, str] = {fi.frame_index: fi.action for fi in frame_inputs}
    legacy_aggregate_compat = input_plan.game_id == "gng"

    # T10.6-E: player_gap_tolerance from config (0 = original immediate-die behavior)
    player_gap_tolerance: int = config.player_gap_tolerance if config is not None else 0

    entries: list[TraceEntry] = []
    tracker = ArthurTracker()
    sig = ArthurSignature()
    prev_state_by_entity: dict[str, str] = {}
    prev_region_by_entity: dict[str, MotionBox] = {}
    prev_state_by_type: dict[str, str] = {}
    prev_region_by_type: dict[str, MotionBox] = {}

    # T10.5-C.4.a: presence bookkeeping keyed by entity_id (not entity_type).
    # Key: entity_id (e.g. "player", "enemy_a_5"), value: last seen frame index.
    prev_seen_by_id: dict[str, int] = {}

    # T10.6-E: consecutive absent-frame counter for "player" only.
    # Incremented each frame the player is not detected; reset to 0 on detection.
    player_gap_counter: int = 0
    # T10.6-E: last frame where the player was *actually* detected (not slid forward).
    # Used to stamp the "die" event on the correct real entry when the gap exceeds tolerance.
    player_last_real_frame: int = -1

    for curr_stat in diff_stats:
        action = input_by_frame.get(curr_stat.start_frame, "noop")

        # T10.5-C.4.c.1: detect disappearances — entities seen last frame but absent now.
        # Runs on both empty and partial frames before emitting new entries.
        current_frame_ids: set[str] = set()
        if curr_stat.changed_regions:
            player_region_peek = tracker.find_arthur(curr_stat.changed_regions, sig)
            if player_region_peek is not None:
                current_frame_ids.add("player")
            remaining_peek = _regions_except_claimed(curr_stat.changed_regions, player_region_peek)
            for ri, region in enumerate(remaining_peek):
                etype = _entity_type_from_box(region, frame_width, frame_height)
                current_frame_ids.add(_entity_id_from_type(etype, curr_stat.start_frame, ri))

        # T10.6-E: update player gap counter before disappearance logic
        if "player" in current_frame_ids:
            player_gap_counter = 0
        elif "player" in prev_seen_by_id:
            player_gap_counter += 1

        for eid, last_frame in list(prev_seen_by_id.items()):
            if last_frame == curr_stat.start_frame - 1 and eid not in current_frame_ids:
                # T10.6-E: for "player", suppress die if within gap tolerance window
                if eid == "player" and player_gap_counter <= player_gap_tolerance:
                    # Hold — slide last_frame forward so next iteration re-enters this branch.
                    prev_seen_by_id[eid] = curr_stat.start_frame
                    continue

                # Emit die on the last *real* detection frame (not the slid frame).
                die_frame = player_last_real_frame if eid == "player" and player_last_real_frame >= 0 else last_frame
                for entry in reversed(entries):
                    if entry.entity_id == eid and entry.frame == die_frame:
                        if "die" not in entry.events:
                            entry.events.append("die")
                        break
                del prev_seen_by_id[eid]
                if eid == "player":
                    player_gap_counter = 0
                    player_last_real_frame = -1

        if not curr_stat.changed_regions:
            continue

        frame_prev_state_by_entity = dict(prev_state_by_entity)
        frame_prev_region_by_entity = dict(prev_region_by_entity)
        frame_prev_state_by_type = dict(prev_state_by_type)
        frame_prev_region_by_type = dict(prev_region_by_type)

        regions_to_emit: list[tuple[str, str, MotionBox]] = []

        player_region = tracker.find_arthur(curr_stat.changed_regions, sig)
        if player_region is not None:
            regions_to_emit.append(("player", "player", player_region))

        remaining_regions = _regions_except_claimed(curr_stat.changed_regions, player_region)
        for region_index, region in enumerate(remaining_regions):
            entity_type = _entity_type_from_box(region, frame_width, frame_height)
            # T10.5-C.4.b: region_index disambiguates multiple entities of same type in one frame.
            entity_id = _entity_id_from_type(entity_type, curr_stat.start_frame, region_index)
            regions_to_emit.append((entity_id, entity_type, region))

        for entity_id, entity_type, region in regions_to_emit:
            prev_region = frame_prev_region_by_entity.get(entity_id)
            if prev_region is None and legacy_aggregate_compat:
                # Older harness tests model a single aggregate blob without
                # Arthur's signature. Keep that path type-continuous while
                # T10.5/gngb traces use strict per-entity IDs.
                prev_region = frame_prev_region_by_type.get(entity_type)
            vx, vy = _compute_region_velocity(
                prev_region,
                region,
                frame_width,
                frame_height,
            )

            prev_state = frame_prev_state_by_entity.get(entity_id, "idle")
            if entity_id not in frame_prev_state_by_entity and legacy_aggregate_compat:
                prev_state = frame_prev_state_by_type.get(entity_type, "idle")

            # Rule 2 — state
            curr_state = _assign_state(vx, vy, entity_type)

            # Rule 3 + 4 — events
            events = _infer_events(prev_state, curr_state, action)

            # Rule 6 — spawn detection. T10.5-C.4.a: keyed by entity_id.
            was_present = entity_id in prev_seen_by_id
            if not was_present:
                if "spawn" not in events:
                    events.insert(0, "spawn")

            prev_seen_by_id[entity_id] = curr_stat.start_frame
            if entity_id == "player":  # T10.6-E: track actual detection frame for die stamping
                player_last_real_frame = curr_stat.start_frame

            entries.append(TraceEntry(
                frame=curr_stat.start_frame,
                entity_id=entity_id,
                entity_type=entity_type,
                x=round(region.center_x / frame_width, 4),
                y=round(region.center_y / frame_height, 4),
                velocity_x=round(vx, 4),
                velocity_y=round(vy, 4),
                state=curr_state,
                events=events,
                score_delta=0,
            ))
            prev_state_by_entity[entity_id] = curr_state
            prev_region_by_entity[entity_id] = region
            if legacy_aggregate_compat:
                prev_state_by_type[entity_type] = curr_state
                prev_region_by_type[entity_type] = region

    return entries

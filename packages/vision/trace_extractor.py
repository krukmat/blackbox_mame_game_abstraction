"""T10.2.2.2/3/4 — Velocity computation, state assignment, event inference, trace assembly.

Implements Rules 1–6 from the translation contract (T10.2.2.1).
All thresholds are expressed as frame-dimension ratios — no pixel values.
All state/event strings are drawn from T09.2 canonical vocabulary.
"""
from __future__ import annotations

from frame_differ import FrameDiffStat, MotionBox

# Lazy imports for types that live outside packages/vision — resolved at call time
# to avoid hard coupling during unit tests that don't need them.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_planner import InputPlan
    from behavioral_diff import TraceEntry

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
_RATIO_ENEMY_A: float = 0.005
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


def _entity_id_from_type(entity_type: str, frame: int) -> str:
    """Return a stable entity_id label with no copyright-protected names."""
    if entity_type == "player":
        return "player"
    return f"{entity_type}_{frame}"


def extract_trace(
    diff_stats: list[FrameDiffStat],
    input_plan: "InputPlan",
    frame_width: int = 256,
    frame_height: int = 224,
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

    entries: list[TraceEntry] = []

    # Track which entity_type buckets were present in the previous diff
    # for Rule 6 spawn/die detection.  Key: entity_type, value: last seen frame.
    prev_seen: dict[str, int] = {}

    # Build prev-stat lookup: prev_stat[i] = diff_stats[i-1] or None
    for idx, curr_stat in enumerate(diff_stats):
        prev_stat = diff_stats[idx - 1] if idx > 0 else None
        action = input_by_frame.get(curr_stat.start_frame, "noop")

        if not curr_stat.changed_regions:
            # Rule 6 die detection: entity present last frame but absent now
            for etype, last_frame in list(prev_seen.items()):
                if last_frame == curr_stat.start_frame - 1:
                    # entity disappeared — emit die on the last frame it was seen
                    # (we already emitted its last real entry; add a synthetic die entry)
                    # Per contract: die on frame F when F+1 has no region.
                    # We annotate the last entry for this entity if it exists.
                    for entry in reversed(entries):
                        if entry.entity_type == etype and entry.frame == last_frame:
                            # Mutate the events list on the existing entry
                            if "die" not in entry.events:
                                entry.events.append("die")
                            break
                    del prev_seen[etype]
            continue

        # Rule 5 — assign entity type from primary region
        primary = max(curr_stat.changed_regions, key=lambda r: r.width * r.height)
        entity_type = _entity_type_from_box(primary, frame_width, frame_height)
        entity_id = _entity_id_from_type(entity_type, curr_stat.start_frame)

        # Rule 1 — velocity
        vx, vy = _compute_velocity(prev_stat, curr_stat, frame_width, frame_height)

        # Determine prev_state for this entity from last entry of same type
        prev_state = "idle"
        for entry in reversed(entries):
            if entry.entity_type == entity_type:
                prev_state = entry.state
                break

        # Rule 2 — state
        curr_state = _assign_state(vx, vy, entity_type)

        # Rule 3 + 4 — events
        events = _infer_events(prev_state, curr_state, action)

        # Rule 6 — spawn detection
        was_present = entity_type in prev_seen
        if not was_present:
            if "spawn" not in events:
                events.insert(0, "spawn")

        prev_seen[entity_type] = curr_stat.start_frame

        entries.append(TraceEntry(
            frame=curr_stat.start_frame,
            entity_id=entity_id,
            entity_type=entity_type,
            x=round(primary.center_x / frame_width, 4),
            y=round(primary.center_y / frame_height, 4),
            velocity_x=round(vx, 4),
            velocity_y=round(vy, 4),
            state=curr_state,
            events=events,
            score_delta=0,
        ))

    return entries

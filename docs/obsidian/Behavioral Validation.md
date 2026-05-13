# Behavioral Validation

tags: #validation #testing #traces

`packages/validation/behavioral_diff.py`

## Purpose

Compare the abstract behavior of the [[React Native Prototype]] against the behavior observed from MAME, without any pixel or image comparison. All validation artifacts are safe to commit.

## Trace Format

A trace is a `list[TraceEntry]`. Each entry is one entity's state at one frame:

```python
@dataclass
class TraceEntry:
    frame: int
    entity_id: str
    entity_type: str
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    state: str           # "grounded" | "jumping" | "dead" | ...
    events: list[str]    # ["spawn", "hit", "score", ...]
    score_delta: int
```

Traces are stored as JSON (array of dicts under `"trace"` key) in `specs/validation/`.

## BehavioralDiff

Aligns observed and simulated traces by `(frame, entity_id)` key. Checks:

| Check | Tolerance |
|---|---|
| `x` position | configurable (default 1.0) |
| `y` position | configurable (default 1.0) |
| `state` | exact match |
| `events` | exact list match |
| `score_delta` | exact match |

Returns `BehavioralDiffResult`:
- `passed: bool`
- `confidence: float` — fraction of non-mismatched keys (0.0–1.0)
- `mismatches: list[str]` — human-readable descriptions
- `recommended_tuning: list[str]`

## Output Reports

Both outputs go through `ensure_public_output_path` and `ensure_no_private_paths`:

- `specs/validation/reports/behavioral_validation.generated.json` — machine-readable
- `specs/validation/reports/behavioral_validation.generated.md` — human-readable

## Golden Master Cases

`specs/validation/golden_master_cases.yaml` — YAML-format behavioral assertions against abstract event sequences. Safe to commit (no pixels, no paths).

## Known Limitations

- `movement_tolerance` default (1.0 unit) is a placeholder. Correct value depends on the game's coordinate scale.
- State and event strings must match exactly — there is no vocabulary enforcement, so naming drift between layers causes false mismatches.
- Event timing tolerance is not supported — an event one frame off is a mismatch.

## Related

- [[React Native Prototype]]
- [[ADR-008 Behavioral Validation No Pixels]]
- `packages/validation/behavioral_diff.py`
- `apps/mame-harness/behavioral_validation.py`
- `specs/validation/`

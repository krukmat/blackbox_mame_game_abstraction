# ADR-005 — Source Profile Pattern

tags: #adr #configuration #gng

Status: **Accepted** | Date: 2026-05-13

> See the full ADR at `docs/adr/ADR-005-source-profile-pattern.md`

## Summary

A `SourceProfile` frozen dataclass is the canonical configuration for one game observation source. It encodes driver name, ROM zip name, default parameters, and the explicit statement that this is private observation only.

## Critical: `gng.zip` → `gngb` driver

The GNG profile declares `mame_driver="gngb"`. The local `gng.zip` matches the bootleg variant (`gngb`), not the parent driver (`gng`). This is validated by [[Preflight]] before any run.

## Known Limitation

Driver validation has a hardcoded `if profile.profile_id == "gng"` check. Adding a second game requires adding another branch. A proper fix would embed a `required_driver` field in the profile itself.

## Related

- [[MAME Runner]]
- [[Preflight]]
- [[Source Profile]]

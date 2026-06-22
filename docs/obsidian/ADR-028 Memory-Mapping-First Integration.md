# ADR-028 Memory-Mapping-First Integration

tags: #adr #architecture #clean-room

Status: Accepted (2026-06-18)

Promotes the MAME Lua memory tap ([[ADR-026 Internal-State Observation Boundary]]) from a
private accelerator to the **default** source of entity position/state. The CV pipeline
([[ADR-012 Entity Signature-Based Player Identification]], [[ADR-013 OpenCV Vision Backend]],
[[ADR-021 Enemy Tracking Continuity]], [[ADR-022 Scroll-Aware Vision Pipeline]]) becomes
optional fallback/cross-check.

Adopts the gym-retro / RetroAchievements / BizHawk design: a declarative per-game
**integration bundle** (typed RAM variables + a scenario event layer + `rom.sha` + a savestate
anchor) and a **guided address-search tool** (reset → filter by change → verify by poke;
addresses are observational, never ROM-disassembled). Constants are calibrated from
savestate-anchored isolation experiments ([[ADR-024 Designed Experiment Calibration]]) over
the RAM state timeline; player-input events stay sourced from
[[ADR-023 Ground-Truth Input Timeline]].

Public boundary unchanged: only numbers cross ([[ADR-001 Clean-Room Layered Architecture]],
[[ADR-003 Public Output Blocklist]], [[ADR-006 Vision Layer Numeric Output]]); ADR-026
clause 4 (explainable as observable behavior) is binding.

Deprecates the unauthored vision-rewrite reservations (ADR-025 optical-flow, ADR-027 VLM) and
tasks T20.7–T20.10 in the automated mapping pipeline plan; their goals are met by the
memory-mapping design.

## Related

- [[ADR-026 Internal-State Observation Boundary]]
- [[ADR-024 Designed Experiment Calibration]]
- [[ADR-023 Ground-Truth Input Timeline]]
</content>

# GNG Integration Plan

tags: #gng #plan #tasks

Source: `docs/plans/gng_source_integration_plan.md`

## Goal

Make `gng.zip` (Ghosts'n Goblins) a reproducible, legally bounded observation source that feeds the clean-room pipeline. **Not a faithful port — a bounded observation input.**

## Task Status

| Task | Title | Status |
|------|-------|--------|
| T01 | Python 3.11 Runtime Normalization | ✅ Done |
| T02 | GNG Source Profile Definition | ✅ Done |
| T03 | MAME and ROM Preflight Validation | ✅ Done |
| T04 | MAME Runner Hardening | ✅ Done |
| T05 | Public Metadata Redaction Hardening | ✅ Done |
| T05.1 | Redaction Boundary Audit | ✅ Done |
| T05.2 | Unified Redaction Policy | ✅ Done |
| T06 | GNG Contract Test Coverage | ✅ Done — 2026-05-13 |
| T07 | CLI Source Profile Integration | ✅ Done — 2026-05-13 |
| T08 | Initial Private GNG Capture | 🔄 In Progress |
| T08.1 | Dry-run Verification | ✅ Done — 2026-05-13 |
| T08.2.1 | Pre-capture Environment Gate | 🔲 Planned |
| T08.2.2 | Single 300-frame MAME Execution | 🔲 Planned |
| T08.2.3 | Private Evidence Directory Layout Audit | 🔲 Planned |
| T08.2.4 | Public Metadata Clean-room Audit | ✅ Done — 2026-05-13 |
| T08.2.5 | Capture Pipeline Fixes (aviwrite path + Lua API) | ✅ Done — 2026-05-13 |
| T09 | First Abstract Observation Schema | 🔄 In Progress |
| T09.1 | Mechanics Inventory | ✅ Done — 2026-05-13 |
| T09.2 | Schema Field Definitions | 🔲 Planned |
| T09.3 | Clean-room Boundary Review | 🔲 Planned |
| T09.4 | Schema File + Examples | 🔲 Planned |
| T10 | Private Evidence to Public Abstract Spec Transformation | 🔲 Planned |
| T11 | RN Prototype Hookup | 🔲 Planned |

## Dependency Order

T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08 → T09 → T10 → T11

Each task depends on the stabilized contract from all prior tasks.

After T11, the next documented phase is T12 Original Game Definition. T12 does not change the GNG source integration exit criteria; it defines the original game direction, encounter grammar, scene recipes, transformation rules, progression, and originality validation needed before RN product work advances beyond mechanics playback.

## Exit Criteria

The stage is complete when:
- `gng` launches through a profile-driven repo command
- Public outputs contain no local absolute paths, ROM paths, or frame paths
- At least one real private capture run has completed
- At least one public abstract mechanics artifact exists
- The RN prototype consumes that artifact without depending on ROMs or private evidence

## Key Decisions Made During This Stage

- Driver is `gngb`, not `gng` (encoded in [[Source Profile]])
- Runner uses structured results, not exceptions ([[ADR-004 MAME Runner Structured Results]])
- Redaction uses `private://` URIs ([[ADR-002 Private URI Scheme]])
- Three-layer output blocklist ([[ADR-003 Public Output Blocklist]])

## Next Steps (T08 onwards)

1. **T08**: Run `python apps/mame-harness/cli.py run --rom gng --rom-path <local/roms> --frames-to-run 300` with a real MAME install and `gng.zip`.
2. **T09**: Define the abstract observation schema (locomotion, jump arc, projectile timing, gravity state).
3. **T10**: Transform private frame evidence into the public abstract spec using the schema.
4. **T11**: Connect one RN prototype scene to the public abstract spec.
5. **T12**: Define the original game layer for Signal Garden using public abstract artifacts only.

## Related

- [[MAME Runner]]
- [[Source Profile]]
- [[Preflight]]
- [[Public Original Game Definition Layer]]
- `docs/plans/gng_source_integration_plan.md`
- `docs/plans/original_game_definition_plan.md`
- `docs/tasks/gng_source_integration/`

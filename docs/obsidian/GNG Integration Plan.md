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
| T06 | GNG Contract Test Coverage | ✅ Done |
| T07 | CLI Source Profile Integration | ✅ Done |
| T08 | Initial Private GNG Capture | 🔲 Planned |
| T09 | First Abstract Observation Schema | 🔲 Planned |
| T10 | Private Evidence to Public Abstract Spec Transformation | 🔲 Planned |
| T11 | RN Prototype Hookup | 🔲 Planned |

## Dependency Order

T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08 → T09 → T10 → T11

Each task depends on the stabilized contract from all prior tasks.

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

1. **T08**: Run `python3.11 apps/mame-harness/cli.py run --rom gng --rom-path <local/roms> --frames-to-run 300` with a real MAME install and `gng.zip`.
2. **T09**: Define the abstract observation schema (locomotion, jump arc, projectile timing, gravity state).
3. **T10**: Transform private frame evidence into the public abstract spec using the schema.
4. **T11**: Connect one RN prototype scene to the public abstract spec.

## Related

- [[MAME Runner]]
- [[Source Profile]]
- [[Preflight]]
- `docs/plans/gng_source_integration_plan.md`
- `docs/tasks/gng_source_integration/`

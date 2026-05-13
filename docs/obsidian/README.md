# Obsidian Vault — blackbox_mame_game_abstraction

This directory is an Obsidian vault for the project. Open `docs/obsidian/` as a vault in Obsidian to get full wikilink navigation, graph view, and tag filtering.

## Entry Points

- [[00 - Project Overview]] — Start here. Pipeline, layout, ADR index, current phase.
- [[Visual Architecture]] — Five Mermaid diagrams: pipeline, layers, guardrails, data flow, task status.
- [[Legal Guardrails]] — Hard rules, what is forbidden, what is allowed.
- [[GNG Integration Plan]] — Active work: T01–T11 task status and next steps.

## Architecture Notes

- [[Private vs Public Boundary]] — The most important invariant in the project.
- [[Guardrails]] — Code enforcement: the three blocklist functions.
- [[MAME Runner]] — Structured results, private path enforcement, dry-run flow.
- [[Source Profile]] — Canonical game config, gng/gngb disambiguation.
- [[Preflight]] — Validation chain before any MAME invocation.
- [[Input Plan]] — YAML-defined deterministic frame sequences.
- [[Vision Layer]] — Private-only frame analysis → numeric entity candidates.
- [[Asset Factory]] — Abstract recipes with originality contract.
- [[Behavioral Validation]] — Trace comparison, no pixel matching.
- [[React Native Prototype]] — Spec-driven TypeScript engine.

## ADR Summaries (Obsidian format)

- [[ADR-001 Clean-Room Layered Architecture]]
- [[ADR-002 Private URI Scheme]]
- [[ADR-003 Public Output Blocklist]]
- [[ADR-004 MAME Runner Structured Results]]
- [[ADR-005 Source Profile Pattern]]
- [[ADR-006 Vision Layer Numeric Output]]
- [[ADR-007 Asset Recipe Originality Contract]]
- [[ADR-008 Behavioral Validation No Pixels]]
- [[ADR-009 Input Plan Determinism]]

## Full ADRs

See `docs/adr/` for the complete ADR documents with full context, consequences, and alternatives considered.

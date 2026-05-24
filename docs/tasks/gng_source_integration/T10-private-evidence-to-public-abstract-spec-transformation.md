# T10 - Private Evidence to Public Abstract Spec Transformation

## Status

✅ Done

## Subtask Status

| Subtask | Title | Effort | Reasoning | Status |
|---------|-------|--------|-----------|--------|
| T10.1 | Gameplay Capture with Active Input Plan | — | — | ✅ Done — 2026-05-13 |
| T10.1.1 | Lua Frame Signaling Resolution | — | — | ✅ Done — 2026-05-13 |
| T10.1.1.1 | MAME 0.287 Lua API Research | `S` | `Medium` | ✅ Done — 2026-05-13 |
| T10.1.1.2 | Lua Script Implementation | `M` | `Medium` | ✅ Done — 2026-05-13 |
| T10.1.1.3 | Lua Signal Verification with Dry MAME Run | `S` | `Low` | ✅ Done — 2026-05-13 |
| T10.1.2 | GNG Input Plan Definition | `S` | `Medium` | ✅ Done — 2026-05-13 |
| T10.1.3 | Gameplay Capture Execution + Evidence Verification | `M` | `Medium` | ✅ Done — 2026-05-13 |
| T10.1.4 | Lua Input Injection | `L` | `High` | ✅ Done — 2026-05-13 |
| T10.2 | Frame-by-Frame Behavioral Extraction | — | — | ✅ Done — 2026-05-14 |
| T10.2.1 | Frame Format Verification + PGM/PNG Compatibility Gate | — | — | ✅ Done — 2026-05-13 |
| T10.2.1.1 | Frame Output Format Audit | `S` | `Medium` | ✅ Done — 2026-05-13 |
| T10.2.1.2 | FrameManifest Format Extension | `M` | `Medium` | ✅ Done — 2026-05-13 |
| T10.2.1.3 | Format Compatibility Regression Gate | `S` | `Low` | ✅ Done — 2026-05-13 |
| T10.2.2 | Motion-to-TraceEntry Translator | — | — | ✅ Done — 2026-05-14 |
| T10.2.2.1 | Translation Contract Design | `S` | `Medium` | ✅ Done — 2026-05-13 |
| T10.2.2.2 | Velocity + State Extraction | `M` | `Medium` | ✅ Done — 2026-05-13 |
| T10.2.2.3 | Event Inference from State Transitions | `M` | `Medium` | ✅ Done — 2026-05-14 |
| T10.2.2.4 | TraceExtractor Integration + Clean-room Verification | `S` | `Low` | ✅ Done — 2026-05-14 |
| T10.2.3 | Trace Output Writer + Guardrails Verification | `S` | `Medium` | ✅ Done — 2026-05-14 |
| T10.3 | Timing Calibration | `M` | `Medium` | ✅ Done — 2026-05-14 |
| T10.4 | Public Artifact Generation + Guardrails Verification | `M` | `Medium` | ✅ Done |
| T10.5 | ArthurTracker — Entity Signature-Based Player Identification | `L` | `High` | ✅ Done |

## Subtask Files

- [T10.1-gameplay-capture-with-active-input-plan.md](T10.1-gameplay-capture-with-active-input-plan.md)
- [T10.1.1-lua-frame-signaling-resolution.md](T10.1.1-lua-frame-signaling-resolution.md)
- [T10.1.1.1-mame-lua-api-research.md](T10.1.1.1-mame-lua-api-research.md)
- [T10.1.1.2-lua-script-implementation.md](T10.1.1.2-lua-script-implementation.md)
- [T10.1.1.3-lua-signal-verification.md](T10.1.1.3-lua-signal-verification.md)
- [T10.1.2-gng-input-plan-definition.md](T10.1.2-gng-input-plan-definition.md)
- [T10.1.3-gameplay-capture-execution.md](T10.1.3-gameplay-capture-execution.md)
- [T10.1.4-lua-input-injection.md](T10.1.4-lua-input-injection.md)
- [T10.2-frame-by-frame-behavioral-extraction.md](T10.2-frame-by-frame-behavioral-extraction.md)
- [T10.2.1-frame-format-verification.md](T10.2.1-frame-format-verification.md)
- [T10.2.1.1-frame-output-format-audit.md](T10.2.1.1-frame-output-format-audit.md)
- [T10.2.1.2-frame-manifest-format-extension.md](T10.2.1.2-frame-manifest-format-extension.md)
- [T10.2.1.3-format-compatibility-regression-gate.md](T10.2.1.3-format-compatibility-regression-gate.md)
- [T10.2.2-motion-to-trace-entry-translator.md](T10.2.2-motion-to-trace-entry-translator.md)
- [T10.2.2.1-translation-contract-design.md](T10.2.2.1-translation-contract-design.md)
- [T10.2.2.2-velocity-state-extraction.md](T10.2.2.2-velocity-state-extraction.md)
- [T10.2.2.3-event-inference-state-transitions.md](T10.2.2.3-event-inference-state-transitions.md)
- [T10.2.2.4-trace-extractor-integration.md](T10.2.2.4-trace-extractor-integration.md)
- [T10.2.3-trace-output-writer.md](T10.2.3-trace-output-writer.md)
- [T10.3-timing-calibration.md](T10.3-timing-calibration.md)
- [T10.4-public-artifact-generation.md](T10.4-public-artifact-generation.md)
- [T10.5-arthur-tracker.md](T10.5-arthur-tracker.md)

## Purpose

Implement the transformation that converts private `gng` observations into the first clean-room-safe public mechanics artifact.

## Reference Reasoning

`High`

Reasoning basis:

- the task operationalizes the clean-room boundary, not just documents it
- it requires mapping real private evidence into public abstractions without leaking source-specific structure
- it combines transformation logic, guardrails, and output validation in one boundary-sensitive step

## Scope

- read the relevant private evidence outputs
- map them into the public abstract schema from `T09`
- enforce output guardrails before writing public files
- generate one first mechanics artifact suitable for prototype consumption

## Out of Scope

- advanced inference engine work
- full automation for every mechanic in the game
- ML-based pattern extraction

## Inputs

- private capture from `T08`
- public schema from `T09`

## Deliverables

- one transformation path from private evidence to public abstract mechanics output
- one generated sample artifact

## Dependencies

- `T09`

## Blocks

- `T11`

## Acceptance Criteria

- the generated artifact contains no direct private evidence paths
- the generated artifact contains no original asset references
- the artifact is structurally valid and usable by downstream code

## Implementation Notes

- prioritize correctness of the abstraction boundary over breadth of mechanic coverage

## Reference Documents

- [T09-first-abstract-observation-schema.md](T09-first-abstract-observation-schema.md)
- [T09.4-schema-file-and-examples.md](T09.4-schema-file-and-examples.md)
- [gng_source_integration_plan.md](../../plans/gng_source_integration_plan.md)
- [ADR-002](../../adr/ADR-002-private-evidence-uri-scheme.md)
- [ADR-003](../../adr/ADR-003-public-output-blocklist.md)
- [ADR-006](../../adr/ADR-006-vision-layer-numeric-only-output.md)
- [ADR-008](../../adr/ADR-008-behavioral-validation-no-pixel-comparison.md)
- [ADR-009](../../adr/ADR-009-input-plan-determinism.md)
- [docs/obsidian/Vision Layer.md](../../obsidian/Vision%20Layer.md)
- [docs/obsidian/Input Plan.md](../../obsidian/Input%20Plan.md)
- [docs/obsidian/Behavioral Validation.md](../../obsidian/Behavioral%20Validation.md)

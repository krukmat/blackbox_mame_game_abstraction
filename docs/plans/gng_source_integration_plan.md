# GNG Source Integration Plan

## Purpose

Use the local `gng.zip` ROM set and the existing MAME installation as a private observation source for this repository's clean-room abstraction workflow.

The immediate goal is not a faithful Ghosts'n Goblins port. The immediate goal is to make `gng` a reproducible, legally bounded input source that can feed private evidence capture and a first public abstract mechanics spec.

## Stage Objective

Deliver a working `gng` source profile with:

- deterministic MAME configuration
- private-only capture outputs
- public metadata redaction
- preflight validation for MAME and ROM inputs
- one initial private capture run
- one initial public abstract mechanics artifact

## Scope Boundary

### In Scope

- Python 3.11 execution normalization for this repo
- `gng` source profile definition
- MAME and ROM preflight validation
- runner error handling hardening
- public metadata redaction hardening
- contract tests for `gng` integration
- CLI integration for a profile-driven `gng` run
- one real private capture
- one first-pass public abstract mechanics schema and output
- RN prototype hookup to the abstract spec

### Out of Scope

- faithful game migration
- pixel-perfect validation
- public screenshots, videos, save states, or sprite outputs
- generalized multi-game plugin architecture
- full ROM manifest decoder parity with the separate `gng` project
- advanced CV/ML inference
- full stage scripting, enemy catalog, or progression parity

## Dependency Order

The tasks below must execute in this order because each later task depends on a stabilized contract from the earlier tasks.

1. `T01` Python 3.11 Runtime Normalization
2. `T02` GNG Source Profile Definition
3. `T03` MAME and ROM Preflight Validation
4. `T04` MAME Runner Hardening
5. `T05` Public Metadata Redaction Hardening
6. `T06` GNG Contract Test Coverage
7. `T07` CLI Source Profile Integration
8. `T08` Initial Private GNG Capture
9. `T09` First Abstract Observation Schema
10. `T10` Private Evidence to Public Abstract Spec Transformation
11. `T11` RN Prototype Hookup

## Dependency Rationale

- `T01` must come first because the repo already declares Python `>=3.11`, and any test or CLI contract work is unreliable if contributors invoke the wrong interpreter.
- `T02` must come before `T03` because the preflight rules depend on a canonical statement of what `gng` means in this repo.
- `T03` must come before `T04` because the runner should consume structured preflight results instead of embedding ad hoc checks.
- `T04` must come before `T05` because the runner output shape must stabilize before public redaction rules can be finalized.
- `T05` must come before `T06` so tests encode the final public-safety contract.
- `T06` must come before `T07` so CLI integration uses already-tested primitives.
- `T07` must come before `T08` so the first real capture uses the intended profile path rather than manual flags.
- `T08` must come before `T09` and `T10` because the first public abstraction should be grounded in real private evidence, not assumptions.
- `T10` must come before `T11` because the RN prototype must consume public abstract specs, never direct private evidence.

## Deliverables

- a canonical `gng` source profile
- MAME/ROM preflight module
- hardened Python runner contract
- public metadata redaction coverage for local sensitive paths
- task-level automated tests
- one successful private capture directory under `evidence/private`
- one first public abstract mechanics artifact
- one RN prototype scene driven by the public abstract mechanics artifact

## Reasoning Reference Scale

Each task in this stage must declare its reference reasoning level.

- `Low`: bounded local change, limited ambiguity, mostly mechanical implementation
- `Medium`: cross-module reasoning, contract alignment, moderate ambiguity, test design required
- `High`: architectural or boundary-sensitive work, evidence interpretation, abstraction design, or legal/clean-room risk

The reasoning reference is not optional metadata. It is part of the task definition and should be used to judge whether the task is being executed with the appropriate care.

## Exit Criteria

This stage is complete only when all of the following are true:

- `gng` can be launched through a profile-driven repo command
- the repo forces the correct MAME driver choice for the local `gng.zip` set
- public outputs contain no local absolute paths, ROM paths, frame paths, crop paths, or direct evidence references beyond sanctioned private handles
- at least one real private capture run has completed successfully
- at least one public abstract mechanics artifact exists and contains only clean-room-safe information
- the RN prototype consumes that artifact without depending on ROMs, MAME, or private evidence paths

## Task Index

- [T01 - Python 3.11 Runtime Normalization](../tasks/gng_source_integration/T01-python-3.11-runtime-normalization.md)
- [T02 - GNG Source Profile Definition](../tasks/gng_source_integration/T02-gng-source-profile-definition.md)
- [T03 - MAME and ROM Preflight Validation](../tasks/gng_source_integration/T03-mame-and-rom-preflight-validation.md)
- [T04 - MAME Runner Hardening](../tasks/gng_source_integration/T04-mame-runner-hardening.md)
- [T05 - Public Metadata Redaction Hardening](../tasks/gng_source_integration/T05-public-metadata-redaction-hardening.md)
- [T06 - GNG Contract Test Coverage](../tasks/gng_source_integration/T06-gng-contract-test-coverage.md)
- [T07 - CLI Source Profile Integration](../tasks/gng_source_integration/T07-cli-source-profile-integration.md)
- [T08 - Initial Private GNG Capture](../tasks/gng_source_integration/T08-initial-private-gng-capture.md)
- [T09 - First Abstract Observation Schema](../tasks/gng_source_integration/T09-first-abstract-observation-schema.md)
- [T10 - Private Evidence to Public Abstract Spec Transformation](../tasks/gng_source_integration/T10-private-evidence-to-public-abstract-spec-transformation.md)
- [T11 - RN Prototype Hookup](../tasks/gng_source_integration/T11-rn-prototype-hookup.md)

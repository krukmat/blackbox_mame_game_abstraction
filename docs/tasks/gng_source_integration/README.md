# GNG Source Integration Tasks

This directory contains the execution tasks for the `gng` source integration stage.

## Execution Order

1. [T01 - Python 3.11 Runtime Normalization](./T01-python-3.11-runtime-normalization.md)
2. [T02 - GNG Source Profile Definition](./T02-gng-source-profile-definition.md)
3. [T03 - MAME and ROM Preflight Validation](./T03-mame-and-rom-preflight-validation.md)
4. [T04 - MAME Runner Hardening](./T04-mame-runner-hardening.md)
5. [T05 - Public Metadata Redaction Hardening](./T05-public-metadata-redaction-hardening.md)
6. [T06 - GNG Contract Test Coverage](./T06-gng-contract-test-coverage.md)
7. [T07 - CLI Source Profile Integration](./T07-cli-source-profile-integration.md)
8. [T08 - Initial Private GNG Capture](./T08-initial-private-gng-capture.md)
9. [T09 - First Abstract Observation Schema](./T09-first-abstract-observation-schema.md)
10. [T10 - Private Evidence to Public Abstract Spec Transformation](./T10-private-evidence-to-public-abstract-spec-transformation.md)
11. [T11 - RN Prototype Hookup](./T11-rn-prototype-hookup.md)

## Post-T11 Handoff

After T11, product-like RN work should move to the T12 Original Game Definition phase rather than extending this source-integration task set. T12 is indexed at [../original_game_definition/README.md](../original_game_definition/README.md) and planned in [../../plans/original_game_definition_plan.md](../../plans/original_game_definition_plan.md).

T12 defines the original game direction, encounter grammar, scene recipes, transformation rules, progression model, and originality validation using public abstract artifacts only.

## Current T05 Artifacts

- [T05.1 - Redaction Boundary Audit](./T05.1-redaction-boundary-audit.md) ✓
- [T05.2 - Unified Redaction Policy Subtasks](./T05.2-unified-redaction-policy-subtasks.md) ✓
- [T05.2.1 - Sensitive Surface Inventory Consolidation](./T05.2.1-sensitive-surface-inventory-consolidation.md) ✓
- [T05.2.2 - Allowed Public Forms](./T05.2.2-allowed-public-forms.md) ✓
- [T05.2.3 - Blocked Public Forms](./T05.2.3-blocked-public-forms.md) ✓
- [T05.2.4 - Redaction Decision Table](./T05.2.4-redaction-decision-table.md) ✓
- [T05.2.5 - Boundary Consistency Review Subtasks](./T05.2.5-boundary-consistency-review-subtasks.md) ✓
- [T05.2.5 - Final Boundary Synthesis](./T05.2.5-final-boundary-synthesis.md) ✓
- [T05.3 - Redaction Implementation Subtasks](./T05.3-redaction-implementation-subtasks.md) ✓
- [T05.4 - Leakage Regression Tests](./T05.4-leakage-regression-tests.md) ✓
- [T05.5 - Public Metadata Contract Documentation](./T05.5-public-metadata-contract-documentation.md) ✓

## Rule

Do not start a task if any of its declared dependencies are still incomplete.

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

## Rule

Do not start a task if any of its declared dependencies are still incomplete.

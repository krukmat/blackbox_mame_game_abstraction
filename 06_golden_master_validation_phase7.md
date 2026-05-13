# Prompt — Golden Master Validation Phase 7

Implement Phase 7: Golden Master behavioral validation.

## Goal

Compare abstract behavior between MAME observation metadata and the React Native implementation without requiring pixel-perfect matching.

## Input

```text
specs/validation/golden_master_cases.yaml
MAME-derived redacted observations
React Native simulation traces
```

## Output

Create:

```text
validation report JSON
validation report Markdown
```

## Implement

### 1. Trace schema

Each trace entry should include:

```text
frame
entity_id
entity_type
x
y
velocity_x
velocity_y
state
events
```

### 2. `BehavioralDiff`

Support:

```text
movement timing tolerance
collision outcome match
event sequence match
state transition match
scoring delta match
```

### 3. Report

The report must include:

```text
pass/fail
confidence
mismatched frames/events
recommended tuning
```

### 4. Explicit exclusions

Do not implement:

```text
pixel-perfect comparison
original sprite comparison
original audio comparison
```

## Add tests

Tests must prove:

```text
matching traces pass
traces outside tolerance fail
reports do not include private evidence paths
```

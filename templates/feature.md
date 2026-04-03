# FEAT-{NNN}: {Title}

| Field | Value |
|-------|-------|
| **Category** | Feature |
| **Status** | Draft |
| **Plan-Version** | 1 |
| **Created** | {DATE} |
| **Priority** | {High/Medium/Low} |
| **Estimated effort** | {Duration} |
| **Skill** | {skill or null} |
| **Reference** | {Links or —} |

## Summary

{What is being built and why?}

## Motivation

{What problem does this feature solve?}

## Acceptance Criteria

- [ ] AC-1: {precise, testable, measurable — e.g. "POST /api/v1/foo with body {x} returns 201 + {y}"}
- [ ] AC-2: {precise, testable, measurable}
- [ ] AC-3: {precise, testable, measurable}

## Edge Cases (min. 3)

| Edge Case | Trigger | Expected Behavior | Severity |
|-----------|---------|-------------------|----------|
| {Description} | {When does it occur?} | {What should happen?} | {High/Medium/Low} |
| {Description} | {When does it occur?} | {What should happen?} | {High/Medium/Low} |
| {Description} | {When does it occur?} | {What should happen?} | {High/Medium/Low} |

## Public Interface

- **Endpoints:** {POST /api/v1/foo, GET /api/v1/foo/:id}
- **Exports:** {FooComponent (Props: { bar: string, baz?: number })}
- **Store changes:** {fooStore.addFoo(), fooStore.removeFoo()}

## Test Specification (for Black-Box Agent)

### Public Interface
- {Endpoint/export/function with request/response types}

### Expected Behavior
| # | Input/Action | Expected Result |
|---|-------------|-----------------|
| 1 | {Input} | {Output} |
| 2 | {Input} | {Output} |

### Edge Cases
| # | Scenario | Expected Result |
|---|----------|-----------------|
| 1 | {Scenario} | {Result} |

### Preconditions
- {Auth, DB state, services required}

### Not in Scope
- {What is explicitly excluded from testing}

## Implementation Plan

### Step 1: {Description}
{Details}

### Step 2: {Description}
{Details}

## Affected Files

| File | Change |
|------|--------|
| {Path} | {Description} |

## Dependencies

- {None or list of task IDs}

## Cross-Cutting Checklist

<!-- Mark non-relevant items with "n/a" + justification — do NOT delete them -->

### Production Readiness
- [ ] Error handling: specific errors (no generic 500s)
- [ ] Input validation: at system boundaries
- [ ] Resource cleanup: files, connections, subscriptions on error/abort
- [ ] Logging: critical operations with context
- [ ] Concurrency: race conditions considered

### Legacy / Tech Debt
- [ ] Legacy code in affected area identified and documented
- [ ] Obsolete fields/imports/helpers removed or TODO with ticket ID
- [ ] No new workarounds on known tech debt

### Test Requirements
- [ ] Tests for new/changed endpoints and services
- [ ] Tests for new/changed stores and components
- [ ] Edge case tests: plan-defined edge cases covered
- [ ] Existing tests don't break

### Persistence
- [ ] DB migrations reversible
- [ ] Export/import flow considers new data
- [ ] State persistence for new data

### Documentation
- [ ] Doc comments (Purpose/Usage/Rationale/Feature) for new classes/functions
- [ ] Public interface documented
- [ ] CLAUDE.md update needed?

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| {Description} | {Low/Medium/High} | {Low/Medium/High} | {Action} |

# REFAC-{NNN}: {Title}

| Field | Value |
|-------|-------|
| **Category** | Refactoring |
| **Status** | Draft |
| **Plan-Version** | 1 |
| **Created** | {DATE} |
| **Priority** | {High/Medium/Low} |
| **Estimated effort** | {Duration} |
| **Skill** | {skill or null} |

## Summary

{What is being improved and why?}

## Motivation

{What problem does this refactoring solve?}

## Before / After

### Before
{Current structure/pattern}

### After
{Desired structure/pattern}

## Acceptance Criteria

- [ ] AC-1: {precise, testable, measurable}
- [ ] AC-2: No behavior change — existing tests still pass

## Edge Cases (min. 3)

| Edge Case | Trigger | Expected Behavior | Severity |
|-----------|---------|-------------------|----------|
| {Description} | {When does it occur?} | {What should happen?} | {High/Medium/Low} |
| {Description} | {When does it occur?} | {What should happen?} | {High/Medium/Low} |
| {Description} | {When does it occur?} | {What should happen?} | {High/Medium/Low} |

## Public Interface

- **Changed exports:** {List or "none"}
- **API changes:** {List or "none — purely internal"}

## Test Specification (for Black-Box Agent)

### Public Interface
- {Affected endpoint/export/function with types}

### Expected Behavior
| # | Input/Action | Expected Result |
|---|-------------|-----------------|
| 1 | {Input} | {Same output as before refactoring} |

### Edge Cases
| # | Scenario | Expected Result |
|---|----------|-----------------|
| 1 | {Scenario} | {Result — behavior unchanged} |

### Preconditions
- {Auth, DB state, services required}

### Not in Scope
- {What is explicitly excluded from testing}

## Metrics

| Metric | Before | After |
|--------|--------|-------|
| {e.g. Files} | {Value} | {Value} |
| {e.g. Complexity} | {Value} | {Value} |

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

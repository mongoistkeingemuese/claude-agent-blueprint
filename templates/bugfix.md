# BUG-{NNN}: {Title}

| Field | Value |
|-------|-------|
| **Category** | Bugfix |
| **Status** | Draft |
| **Plan-Version** | 1 |
| **Created** | {DATE} |
| **Priority** | {High/Medium/Low} |
| **Estimated effort** | {Duration} |
| **Skill** | {skill or null} |

## Summary

{What is broken?}

## Reproduction Steps

1. {Step 1}
2. {Step 2}
3. {Expected vs. actual behavior}

## Root Cause

{Analysis of the underlying cause}

## Acceptance Criteria

- [ ] AC-1: {precise, testable, measurable}
- [ ] AC-2: {precise, testable, measurable}

## Edge Cases (min. 3)

| Edge Case | Trigger | Expected Behavior | Severity |
|-----------|---------|-------------------|----------|
| {Description} | {When does it occur?} | {What should happen?} | {High/Medium/Low} |
| {Description} | {When does it occur?} | {What should happen?} | {High/Medium/Low} |
| {Description} | {When does it occur?} | {What should happen?} | {High/Medium/Low} |

## Public Interface

- **Affected endpoints:** {List}
- **Affected components:** {List}

## Test Specification (for Black-Box Agent)

### Public Interface
- {Affected endpoint/export/function with types}

### Expected Behavior
| # | Input/Action | Expected Result |
|---|-------------|-----------------|
| 1 | {Reproduction input} | {Correct behavior after fix} |

### Edge Cases
| # | Scenario | Expected Result |
|---|----------|-----------------|
| 1 | {Scenario} | {Result} |

### Preconditions
- {Auth, DB state, services required}

### Not in Scope
- {What is explicitly excluded from testing}

## Fix Plan

{Minimal, targeted changes — no scope creep}

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

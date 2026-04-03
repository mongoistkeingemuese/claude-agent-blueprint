# Cross-Cutting Checklist

Include this in every task plan. Mark non-relevant items with "n/a" + justification — do NOT delete them.

Adapt these sections to your project's stack and conventions.

## Production Readiness
- [ ] Error handling: specific errors (no generic 500s)
- [ ] Input validation: at system boundaries
- [ ] Resource cleanup: files, connections, subscriptions on error/abort
- [ ] Logging: critical operations with context
- [ ] Concurrency: race conditions considered

## Legacy / Tech Debt
- [ ] Legacy code in affected area identified and documented
- [ ] Obsolete fields/imports/helpers removed or TODO with ticket ID
- [ ] No new workarounds on known tech debt

## Test Requirements
- [ ] Tests for new/changed endpoints and services
- [ ] Tests for new/changed stores and components
- [ ] Edge case tests: plan-defined edge cases covered
- [ ] Existing tests don't break

## Persistence
- [ ] DB migrations reversible
- [ ] Export/import flow considers new data
- [ ] State persistence for new data

## Documentation
- [ ] Doc comments (Purpose/Usage/Rationale/Feature) for new classes/functions
- [ ] Public interface documented
- [ ] CLAUDE.md update needed?

# /task -- Task Planning with Validation

**User input:** $ARGUMENTS

You are the task manager for this project. You create validated task plans
with testable acceptance criteria, edge cases, and public interfaces.

---

## Phase 1: Categorization

Analyze the task:
- **Feature (FEAT):** New functionality, new behavior, new UI elements
- **Bugfix (BUG):** Error correction, wrong behavior, crashes
- **Refactoring (REFAC):** Code improvement without behavior change
- **Test (TEST):** Test suites, test infrastructure, test coverage

Briefly justify the categorization.

---

## Phase 1b: ID Reservation

1. Note current branch
2. Switch to base branch
3. Determine next free ID from state.json
4. Switch back to previous branch

---

## Phase 1c: Skill Detection

| Trigger Keywords | Skill | Description |
|-----------------|-------|-------------|
| *(add your project-specific skills here)* | `your-skill` | Your domain |

If no skill detected: `SKILL` -> `null`

**Customization:** Define trigger keywords that map to your specialist agents.
Each skill corresponds to a `.claude/commands/{skill}.md` file.

---

## Phase 2: Create Plan

1. Read matching template from `docs/templates/`
2. Analyze project: structure, existing patterns
3. Create plan from filled template:
   - Filename: `{CAT}-{NNN}_{short_description_snake_case}.md`
   - Directory: `docs/backlog/features/`, `bugfix/`, `refactor/`, or `tests/`
   - Status: "Draft"
   - Set skill field

### Mandatory Sections (ALL must be present)

#### Acceptance Criteria
```markdown
## Acceptance Criteria
- [ ] Criterion 1: {PRECISE, testable, measurable}
```

**NOT:** "Feature works"
**BUT:** "POST /api/v1/foo with body {x} returns 201 + {y}"

#### Edge Cases (min. 3)
```markdown
## Edge Cases (min. 3)
| Edge Case | Trigger | Expected Behavior | Severity |
|-----------|---------|-------------------|----------|
| Empty input | User sends {} | 422 with error message | Medium |
```

#### Public Interface
```markdown
## Public Interface
- Endpoints: POST /api/v1/foo, GET /api/v1/foo/:id
- Exports: FooComponent (Props: { bar: string })
- Store changes: fooStore.addFoo()
```

#### Cross-Cutting Checklist
```markdown
## Cross-Cutting Checklist
- Production Readiness (error handling, validation, cleanup, logging, concurrency)
- Legacy / Tech Debt (identified, cleaned up, no new workarounds)
- Test Requirements (unit, integration, edge cases, existing tests)
- Persistence (migrations, export/import, state persistence)
- Documentation (docstrings, interface docs, updated project docs)
```

Mark non-relevant items with "n/a" + justification -- do NOT delete them.

---

## Phase 3: Independent Validation

Start a sub-agent (general-purpose) that validates the plan:

### Validation Checks

1. **Acceptance Criteria Quality:**
   Each criterion must be precise enough for a black-box test.
   Can `/test` verify this without knowing the implementation?

2. **Edge Case Minimum:**
   Min. 3 edge cases with trigger + expectation + severity.

3. **Public Interface:**
   Documented what `/test` can access from outside?

4. **Architecture Check:**
   File paths correct? Compatible with existing architecture?
   Conflicts with other plans in docs/backlog/?

5. **Production Readiness:**
   Error handling? Input validation? Resource cleanup?

6. **Cross-Cutting Checklist:**
   All sections present? Non-relevant items justified with "n/a"?

**REJECT if:**
- Acceptance criteria not testable
- Fewer than 3 edge cases
- Public interface missing
- Cross-cutting checklist missing or sections skipped without "n/a" justification

---

## Phase 4: Plan Adjustment

- **PROBLEM:** Adjust plan, explain to user
- **WARNING:** Show warnings, ask if adjustment desired
- **OK:** Continue to Phase 5

---

## Phase 5: User Approval

Compact summary: category, ID, title, skill, key steps, validation result.

Ask: **"Should this plan be implemented as-is?"**
- "Adjust plan": what to adjust, ask again
- "Discard task": delete plan file

---

## Phase 6: Update Documentation

1. Set plan status to "Approved"
2. state.json: add new entry in matching section:
   ```json
   "{ID}": {
     "title": "{TITLE}",
     "status": "approved",
     "deps": [],
     "plan": "docs/backlog/{type}/{ID}_{name}.md",
     "skill": null
   }
   ```
3. Commit: `docs({ID}): add approved plan for {short title}`

---

## Rules

- Skip no steps
- Validation agent MUST run as independent sub-agent
- On ambiguity: involve user
- Base branch: configured in state.json
- State path: `docs/orchestrator_state.json`

## Learnings

- Acceptance criteria containing "works" or "correct" are not testable.
  Always specify concrete inputs/outputs.
- Refactoring plans with exact before/after code snippets + line numbers eliminate
  implementation ambiguity and lead to zero-retry execution.
- Edge cases that block the test runner (e.g., infinite loop in main thread, >100MB
  memory allocation) should be marked as "not unit-testable" with justification.

# /execute-task -- Fully Automated Task Execution

Fully automated execution of a single task with black-box testing and learning.
Main = dispatcher, sub-agents = workers.

**Task-ID:** $ARGUMENTS

---

## Phase Tracking

Update the phase in state.json at EVERY phase transition.
Category path: FEAT -> `.features`, BUG -> `.bugfixes`, REFAC -> `.refactors`, TEST -> `.tests`

**Atomic state.json updates with flock:**
```bash
(
  flock -x 201
  jq --arg id "{ID}" '.{category}[$id].phase = "{phase}"' docs/orchestrator_state.json > docs/orchestrator_state.json.tmp && mv docs/orchestrator_state.json.tmp docs/orchestrator_state.json
) 201>docs/.state.lock
```

Phases: `preflight`, `branch`, `plan_validate`, `implement`, `rebase`, `review`, `test`, `validate`, `merge`, `cleanup`, `docs`, `learn`

---

## Phase 0: Pre-Flight (Main)

**Phase update:** `preflight`

1. **Validate ID:** Format `^(FEAT|BUG|REFAC|TEST)-\d{3}[a-z]?$`
2. **Directory:** FEAT -> `docs/backlog/features/`, BUG -> `docs/backlog/bugfix/`, REFAC -> `docs/backlog/refactor/`, TEST -> `docs/backlog/tests/`
3. **Task file:** Glob `{dir}/{ID}_*.md`. Store absolute path as `TASK_FILE`.
4. **Check status:** "Approved" or "In Progress" (retry/crash recovery) allowed. "Draft" tasks must first be approved via `/task`.
5. **Check deps:** state.json -> referenced deps must be "done".
6. **Base branch:** `git rev-parse --abbrev-ref HEAD` -> `BASE_BRANCH`
7. **Skill routing:**
   a) state.json -> `{category}.{ID}.skill`
   b) If not found: task file -> `| **Skill** | {value} |`
   c) Store as `TASK_SKILL`

### Skill Routing Table

```
Task has skill: "your-skill"  --> /your-skill (specialist agent)
Task has skill: null           --> normal feature cycle (inline implementation)
```

**Customization:** Add your own specialists to this table. Each specialist is a
`.claude/commands/{skill}.md` file that handles domain-specific implementation.

---

## Phase 1: Branch + Worktree (Main)

**Phase update:** `branch`

### 1a: Branch

```bash
BRANCH_NAME="{prefix}/{ID}_{short_name}"
# prefix: feat/ for FEAT, fix/ for BUG, refac/ for REFAC, test/ for TEST
```

**If branch already exists (retry/crash recovery):**
```bash
git worktree add .claude/worktrees/{ID} {BRANCH_NAME}
cd .claude/worktrees/{ID}
git merge {BASE_BRANCH} --no-edit   # Merge base branch in (NO rebase -- revert-safe)
```

**If new:**
```bash
git worktree add -b {BRANCH_NAME} .claude/worktrees/{ID} {BASE_BRANCH}
```

State: branch -> `{BRANCH_NAME}`

### 1b: Worktree Working Directory

All subsequent phases work in: `.claude/worktrees/{ID}/`

---

## Phase 2: Implementation

**Phase update:** `implement`

### 2a: Plan Validation (Quick)

Read task file. Check:
- Acceptance criteria present and testable?
- If retry: pitfalls section present? Apply pitfalls!
- Public interface documented?

### 2b: Skill Routing

**If TASK_SKILL is set:** delegate to specialist agent:

> Read and follow `{ABS_PATH}/.claude/commands/{TASK_SKILL}.md`.
> Task-ID: {ID}
> Task plan: {TASK_FILE}
> Working directory: {WORKTREE_PATH}
>
> Execute the complete implementation according to the task plan.
>
> Result (ONLY 5 lines):
> STATUS: done|blocked|failed
> FILES: [created/changed files]
> TESTS: {new} new, {total} total, {passed} passed, {failed} failed
> LINT: OK|FAILED ({N} errors)
> SUMMARY: [1 sentence]

**If TASK_SKILL is null:** normal feature cycle (sub-agent implements based on task plan).

### 2c: Implementation Sub-Agent (for null skill)

Sub-Agent:

> Implement task {ID} according to the plan.
> `cd {WORKTREE_PATH}`
>
> ## Task Plan
> {TASK_FILE content -- acceptance criteria, steps, edge cases}
>
> ## Rules
> - Follow ALL code conventions from CLAUDE.md
> - Implement ALL acceptance criteria
> - Handle ALL edge cases from the plan
> - If retry: apply ALL pitfalls from the plan
> - Commit after implementation: `{type}({ID}): {summary}`
>
> Result (ONLY 5 lines):
> STATUS: done|blocked|failed
> FILES: [created/changed files]
> TESTS: n/a (tests written by /test, not implementer)
> LINT: OK|FAILED ({N} errors)
> SUMMARY: [1 sentence]

---

## Phase 2b: Rebase

**Phase update:** `rebase`

```bash
cd {WORKTREE_PATH}
git fetch origin {BASE_BRANCH}
git rebase origin/{BASE_BRANCH}   # or merge if revert-safety needed
```

On conflict: STATUS: blocked, recommend `/resolve {ID}`.

---

## Phase 2c: Code Review

**Phase update:** `review`

Sub-Agent:

> Read and follow `{ABS_PATH}/.claude/commands/review.md`.
> Task plan: {TASK_FILE}
> Working directory: {WORKTREE_PATH}
> Skill: {TASK_SKILL}
>
> Review the implementation against the task plan.
>
> Result (ONLY 5 lines):
> STATUS: pass|warn|fail
> FINDINGS: {n} total ({critical} critical, {warnings} warnings)
> CRITICAL: [list of critical findings]
> CONVENTIONS: {OK|{n} violations}
> SUMMARY: [1 sentence]

### Review Fix Loop (max 2 iterations)

If STATUS = "fail":
1. Fix critical findings (sub-agent with findings list)
2. Re-run /review
3. After 2 failed iterations: STATUS: blocked

If STATUS = "warn": continue (warnings documented for /learn)
If STATUS = "pass": continue

---

## Phase 3: Black-Box Testing

**Phase update:** `test`

Sub-Agent:

> Read and follow `{ABS_PATH}/.claude/commands/test.md`.
> Task-ID: {ID}
> Task plan: {TASK_FILE}
> Working directory: {WORKTREE_PATH}
>
> Write and run black-box acceptance tests.
>
> Result (ONLY 5 lines):
> STATUS: pass|fail
> TESTS_WRITTEN: {n}
> TESTS_PASSED: {n}/{m}
> EDGE_CASES: {tested}/{planned}
> SUMMARY: [1 sentence]

### Test Fix Loop (max 3 iterations)

If STATUS = "fail":

Sub-Agent:

> Read and follow `{ABS_PATH}/.claude/commands/testfix.md`.
> TASK_ID: {ID}
> TASK_PLAN: {TASK_FILE}
> WORKTREE: {WORKTREE_PATH}
> FAILED_TESTS: {failure output}
> ITERATION: {1|2|3}
>
> Analyze failures and fix code or tests (no coverage loss).

After 3 failed iterations: STATUS: blocked.

---

## Phase 4: Pre-Merge Validation

**Phase update:** `validate`

**Inline (Main -- no sub-agent):**

```bash
cd {WORKTREE_PATH}

# Run your project's full test suite + linting
# Adapt to your project:
# npm test && npm run lint
# pytest && mypy src/
# cargo test && cargo clippy
```

All must pass. On failure: fix inline or STATUS: blocked.

---

## Phase 5: Merge

**Phase update:** `merge`

### 5a: Merge to Base Branch

```bash
cd {ABS_PATH}   # Back to main repo
git merge --no-ff {BRANCH_NAME} -m "merge({ID}): {title}"
```

State: merged -> true

### 5b: Worktree Cleanup

```bash
git worktree remove .claude/worktrees/{ID}
```

---

## Phase 6: Documentation Update

**Phase update:** `docs`

Inline (no sub-agent):
- Update any documentation that references changed files
- Update CLAUDE.md if new patterns/stores/endpoints were introduced

---

## Phase 7: Learning

**Phase update:** `learn`

Sub-Agent:

> Read and follow `{ABS_PATH}/.claude/commands/learn.md`.
> Task-ID: {ID}
> Task plan: {TASK_FILE}
> Review result: {REVIEW_RESULT}
> Review fix count: {REVIEW_FIX_COUNT}
> Test result: {TEST_RESULT}
> Test fix count: {TEST_FIX_COUNT}

---

## Result Format

```
STATUS: done|blocked|failed
MERGED: true|false
TESTS: {new} new, {total} total, {passed} passed, {failed} failed
LINT: OK|FAILED ({N} errors)
SUMMARY: [1 sentence]
```

---

## Rules

1. EVERY phase transition updates state.json
2. ALL work happens in the worktree, NEVER on the base branch
3. Sub-agent results: structured, max 5 lines
4. On merge conflict: set merged:false, recommend `/resolve`
5. Implementation and testing are SEPARATED (different agents)
6. Specialist agents handle domain-specific tasks
7. Worktree cleanup after merge or on failure

## Learnings

- Worktree isolation prevents conflicts between tasks and keeps the base branch clean.
- Separating implementation and testing (different agents) catches more bugs because
  the test agent has no implementation bias.
- Review before test catches structural issues early, saving test iterations.
- Pitfalls section in retry plans prevents repeating the same mistakes.
- Atomic state.json updates with flock prevent corruption from concurrent access.

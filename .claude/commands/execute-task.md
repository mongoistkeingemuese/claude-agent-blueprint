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

Phases: `preflight`, `branch`, `plan_validate`, `implement`, `ac_gate`, `rebase`, `review`, `test`, `validate`, `merge`, `cleanup`, `docs`, `learn`

---

## Phase 0: Pre-Flight (Main)

**Phase update:** `preflight`

1. **Validate ID:** Format `^(FEAT|BUG|REFAC|TEST)-\d{3}[a-z]?$`
2. **Infrastructure check (optional, adapt to your project):**
   ```bash
   # Check that required services are running before starting work.
   # E.g., database, Docker containers, external services.
   # Adapt to your project:
   # timeout 5 docker exec my-db pg_isready -U postgres >/dev/null 2>&1 \
   #   || { echo "BLOCKER: Database not ready."; exit 1; }
   ```
3. **Directory:** FEAT -> `docs/backlog/features/`, BUG -> `docs/backlog/bugfix/`, REFAC -> `docs/backlog/refactor/`, TEST -> `docs/backlog/tests/`
4. **Task file:** Glob `{dir}/{ID}_*.md`. Store absolute path as `TASK_FILE`.
5. **Check status:** "Approved" or "In Progress" (retry/crash recovery) allowed. "Draft" tasks must first be approved via `/task`.
6. **Check deps:** state.json -> referenced deps must be "done".
7. **Base branch:** `git rev-parse --abbrev-ref HEAD` -> `BASE_BRANCH`
8. **Skill routing:**
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
mkdir -p .claude/worktrees
if ! git worktree list | grep -q ".claude/worktrees/{ID}"; then
    git worktree add .claude/worktrees/{ID} {BRANCH_NAME}
fi
cd .claude/worktrees/{ID}
# IMPORTANT: No `git rebase`! If base branch contains a revert of our
# merge commit, rebase silently drops all commits.
# Instead: merge base branch in (preserves our commits).
git merge {BASE_BRANCH} --no-edit
```

Set `IS_RETRY = true`. Inventory existing changes:
```bash
EXISTING_DIFF=$(git diff --stat {BASE_BRANCH}...HEAD)
EXISTING_LOG=$(git log --oneline {BASE_BRANCH}..HEAD)
```

**If new:**
```bash
git branch {BRANCH_NAME} {BASE_BRANCH}
mkdir -p .claude/worktrees
git worktree add .claude/worktrees/{ID} {BRANCH_NAME}
```

Set `IS_RETRY = false`.
State: branch -> `{BRANCH_NAME}`, status -> "in_progress"

### 1b: Worktree Working Directory

All subsequent phases work in: `.claude/worktrees/{ID}/`

---

## Phase 1b: Plan Validation & Revision (Sub-Agent)

**Phase update:** `plan_validate`

**On retry (IS_RETRY == true): LIGHTWEIGHT validation.**
The fix analysis agent just updated the plan. With sequential execution,
code hasn't changed since the last attempt. Skip the full check suite.

Sub-Agent:
> Check pitfalls section is present and coherent.
> Verify pitfall solutions are consistent with implementation steps.
> Result (3 lines):
> PLAN_STATUS: valid|revised
> PITFALLS_COHERENT: true|false
> REVISION_SUMMARY: [1 sentence]

---

**On first attempt (IS_RETRY == false): FULL validation.**

Most critical quality gate in the workflow. Checks whether the task plan
still matches the current codebase BEFORE implementation starts.

Sub-Agent (general-purpose):

> Working directory: {WORKTREE_PATH}
> Read task plan: `{TASK_FILE}`
> Read CLAUDE.md for project conventions.
>
> ## Step 1: Build Plan Inventory
> Extract ALL concrete references from the task plan:
> - File paths, function/method names + expected signatures
> - Interface/type definitions, import paths
> - Store fields, API endpoints, DB models
> - External dependencies
>
> ## Step 2: Code Reality Check (8 Checks)
>
> ### Check 1: Files & Paths
> For EACH referenced file: does it exist? Renamed/moved?
>
> ### Check 2: Interfaces & Signatures
> For EACH referenced function/interface: does the signature match?
>
> ### Check 3: Recently Merged Changes
> `git log --oneline --since="$(git log -1 --format=%ci {TASK_FILE})" {BASE_BRANCH}`
> Overlap with plan files?
>
> ### Check 4: Acceptance Criteria Testability
> For EACH AC: concrete enough for an automated test?
>
> ### Check 5: Scope & Side Effects
> Circular imports? Unexpected test breakage?
>
> ### Check 6: Production Readiness
> Error handling, loading/empty states, validation, concurrent access,
> resource cleanup, logging, backwards compatibility?
>
> ### Check 7: Edge Cases
> Min. 3 edge cases documented? Data, concurrency, system, state edge cases?
>
> ### Check 8: Test Specification for Black-Box Agent
> Public interface, expected behavior, edge case behavior,
> testable preconditions, scope boundaries?
>
> ## Step 3: Classify Findings
> INFO | MINOR | MAJOR | BLOCKER
>
> ## Step 4: Update Plan (for MINOR/MAJOR)
> Update affected sections, add Plan-Revision section with findings table.
> Git commit: `docs({ID}): revise plan -- {N} findings ({severity_summary})`
>
> ## Step 5: Risk Assessment
> low (0 findings or INFO only) | medium (MINOR, no MAJOR) |
> high (MAJOR, ACs changed) | blocker (BLOCKER)
>
> ## Result (9 lines):
> PLAN_STATUS: valid|revised|blocked
> FINDINGS: {total} ({info} INFO, {minor} MINOR, {major} MAJOR, {blocker} BLOCKER)
> FILES_CHECKED: {count}
> CRITERIA_VALID: {valid}/{total} acceptance criteria
> EDGE_CASES: {count} defined (min. 3 required)
> PROD_READY: {open} open / {total} checked
> TEST_SPEC: complete|added|incomplete
> REVISION_SUMMARY: [1 sentence]
> RISK: low|medium|high|blocker

### Result Handling (Main)

| PLAN_STATUS | RISK | Action |
|-------------|------|--------|
| valid | low | Continue to Phase 1* (Auto-Validate Check) |
| revised | medium | Continue, store REVISION_SUMMARY for Phase 2 |
| revised | high | Continue automatically, findings documented |
| blocked | blocker | state.json status -> "blocked". Task back to `/task` |

---

## Phase 1*: Auto-Validate Trigger (Main)

**Heuristic -- `/validate` is automatically triggered when:**
- Task type is `REFAC` or `FEAT` with >3 ACs
- Plan affects >3 files (in "Affected Files" section)
- Plan contains keywords: `"refactor"`, `"migration"`, `"breaking"`, `"architecture"`

**Re-trigger guard:**
Flag `VALIDATED = true` is set after successful validate (in-memory).
Prevents re-triggering when revised plan still matches heuristic.

**Flow:**
1. Check if `/validate` was already run manually (plan contains "Plan-Revision" with validate reference) -> Skip
2. Check if `VALIDATED == true` -> Skip
3. Evaluate heuristic
4. If heuristic does NOT match -> Skip, continue to Phase 2
5. If heuristic matches:
   Sub-Agent: Run `/validate` against the task plan.
6. Process validate result:

   | RISK | Action |
   |------|--------|
   | low | `VALIDATED = true`, continue to Phase 2 |
   | medium | Automatic plan revision, `VALIDATED = true`, continue |
   | high | User confirmation required. Pipeline stops. |
   | blocker | state.json status -> "blocked" |

7. **Plan Revision (for findings >= MINOR, RISK != high):**
   a. Parse validate report, extract CRITICAL/RECOMMENDED items
   b. Update plan file (ACs, edge cases, affected files)
   c. Append Plan-Revision section
   d. Increment `plan_version` in header (store as `PLAN_VERSION`)
   e. Git commit: `docs({ID}): revise plan V{N} -- {M} findings from /validate`

---

## Plan-Version Propagation

After Phase 1b (and possibly Phase 1* plan revision):

```
PLAN_VERSION=$(grep "Plan-Version" {TASK_FILE} | awk '{print $NF}')
# Default: 1 if no Plan-Version header present
```

`PLAN_VERSION` is passed to Phase 2c (Review) and Phase 3 (Test) as parameter.
Review and Test check: "Am I working against the current plan version?"

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

**On first attempt (IS_RETRY == false):**

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
> - Feature traceability: add `Feature: {ID}` to docstrings on new/changed code
> - Commit after implementation: `{type}({ID}): {summary}`
>
> Result (ONLY 5 lines):
> STATUS: done|blocked|failed
> FILES: [created/changed files]
> TESTS: n/a (tests written by /test, not implementer)
> LINT: OK|FAILED ({N} errors)
> SUMMARY: [1 sentence]

**On retry (IS_RETRY == true):**

Sub-Agent:

> **RETRY** of task {ID}. Read PITFALLS section first.
> Existing work on branch:
> ```
> {EXISTING_LOG}
> {EXISTING_DIFF}
> ```
> Fix targeted -- do NOT rewrite everything.
> Commit: `fix({ID}): address pitfalls from attempt {N}`

---

## Phase 2.5: AC-Checklist Gate (Main -- inline)

**Position:** After implementation (Phase 2), before Rebase (Phase 2b).

Verifies every acceptance criterion has corresponding implementation before Review.
Without explicit AC-matching, ACs get "forgotten" and are only discovered in test or later.

**Flow:**
1. Extract all acceptance criteria from task plan (lines with `- [ ] AC` or `- [x] AC`)
2. Read `git diff {BASE_BRANCH}...HEAD` in worktree
3. For EACH AC individually:
   - Is there corresponding code in the diff? (grep/file check)
   - Does the code implement the AC correctly? (semantic check)
4. Gate decision

**Works identically for skill delegation (TASK_SKILL != null):**
Skill agents deliver the standard 5-line result without AC mapping.
Phase 2.5 reads `git diff` in the worktree and checks ACs independently.

**Output format:**
```
AC-CHECKLIST:
AC-1: PASS -- Implemented in {file}:{line}
AC-2: FAIL -- Missing: {what's missing}
AC-3: PASS -- Implemented in {file}:{line}
RESULT: {covered}/{total} ACs covered -- {PASS|BLOCKED}
```

**Rules:**
- Each AC must be checked INDIVIDUALLY -- no "looks good overall"
- On FAIL: concrete description of which AC is missing and what's needed
- No proceeding to Phase 2b while any AC is FAIL -> back to Phase 2

**Follow-Up Queue:** Out-of-scope findings during AC check go to `.build/followup_queue.json`.

---

## Phase 2b: Rebase

**Phase update:** `rebase`

**On retry (IS_RETRY == true): SKIP Phase 2b.**
(Base branch was already integrated in Phase 1 via `git merge`)

**On first attempt (IS_RETRY == false):**

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
> Plan-Version: {PLAN_VERSION}
>
> Review the implementation against the task plan.
> Check: does the plan version match the current plan?
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

Track `REVIEW_FIX_COUNT` (0 = no fix needed, 1 = first fix, 2 = second fix).

---

## Phase 3: Black-Box Testing

**Phase update:** `test`

**On retry (IS_RETRY == true): check if tests already exist.**
```bash
cd {WORKTREE_PATH}
git diff --name-only {BASE_BRANCH}...HEAD | grep -E "test_|\.test\." | head -5
```
- **Tests exist:** Run tests only, do NOT rewrite.
  On failure -> Phase 3b (test fix loop).
- **No tests:** Normal /test workflow (see below).

**On first attempt or no tests on branch:**

Sub-Agent:

> Read and follow `{ABS_PATH}/.claude/commands/test.md`.
> Task-ID: {ID}
> Task plan: {TASK_FILE}
> Working directory: {WORKTREE_PATH}
> Plan-Version: {PLAN_VERSION}
>
> Write and run black-box acceptance tests.
> Do NOT read implementation code.
> Check: does the plan version match the current plan?
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

**Inline (Main -- no sub-agent).** Fail-fast order:

```bash
cd {WORKTREE_PATH}

# Run your project's full test suite + linting
# Adapt to your project:
# npm test && npm run lint
# pytest && mypy src/
# cargo test && cargo clippy
```

### 4b: Test-Coverage Check Against Acceptance Criteria

After successful tests, BEFORE merge is allowed:

1. Extract all ACs from task plan
2. Identify all test files in diff (`git diff --name-only {BASE_BRANCH}...HEAD | grep -E "test_|\.test\."`)
3. For EACH AC: is there at least 1 test that checks this AC?
4. For EACH edge case in plan: is there a corresponding test?

**Output format:**
```
TEST-COVERAGE:
COVERAGE: {tested}/{total} ACs, {tested_ec}/{total_ec} Edge Cases
AC-1: PASS -- test_foo.py::test_creates_widget
AC-2: FAIL -- No test found
EC-1: PASS -- test_foo.py::test_null_input
EC-2: WARN -- No test (WARNING)
RESULT: PASS|FAIL -- {reason}
```

**Rules:**
- AC coverage < 100% -> Phase 4 FAIL, back to Phase 3
- Edge case coverage < 100% -> WARNING, not a blocker
- Mapping must be traceable (which test checks which AC)

### 4c: Follow-Up Queue VERIFY/high Gate

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
if [ -f "$REPO_ROOT/.build/followup_queue.json" ]; then
  VERIFY_HIGH=$(jq '[.items[] | select(.category == "VERIFY" and .priority == "high")] | length' "$REPO_ROOT/.build/followup_queue.json")
  if [ "$VERIFY_HIGH" -gt 0 ]; then
    echo "BLOCKED: $VERIFY_HIGH VERIFY/high items in Follow-Up Queue"
  fi
fi
```

All checks OK = continue to Phase 5, otherwise FAILED.

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

**Phase update:** `cleanup`

```bash
git worktree remove .claude/worktrees/{ID}
```

**Cleanup on failure/blocked (no merge):**
1. `git worktree remove --force .claude/worktrees/{ID}`
2. Branch is NOT deleted (kept for debugging/retry)
3. state.json: status -> "blocked"/"failed", phase -> null

---

## Phase 6: Documentation Update + Follow-Up Presentation

**Prerequisite:** Only if `merged: true`.

**Phase update:** `docs`

Inline (no sub-agent):
1. state.json: status -> "done", phase -> null
2. Task file: set status field to "Done"
3. Git commit: `docs({ID}): mark task done`

### Follow-Up Queue Presentation

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
QUEUE_FILE="$REPO_ROOT/.build/followup_queue.json"
```

If `$QUEUE_FILE` exists and has items:

```
===================================================
  FOLLOW-UP QUEUE: {ID} -- {n} Items
===================================================
| # | Category | Priority | Title | Source |
|---|----------|----------|-------|--------|
| 1 | VERIFY | high | ... | review/2c |
| 2 | REFAC | medium | ... | test/3 |
| 3 | IDEA | low | ... | implement/2 |

For each item:
  [Execute] -> generates task spec from queue entry (via /task)
  [Backlog] -> writes to docs/backlog/ as new task
  [Dismiss] -> removes with justification
```

Queue is archived in state.json under the task entry after Phase 6.

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
> Retry info: {IS_RETRY}, Attempt: {current attempt number}
> Pitfalls: {pitfalls section from task file, if present}
> Attempt history: {errors[].attempts from state.json, if present}

**On retry success (IS_RETRY == true):** The learning agent receives the complete
failure history and should extract patterns for the Learnings sections.

---

## Context Rules

- Main reads ONLY: task file (status), state.json (deps), `.build/followup_queue.json` (Phase 4c + Phase 6)
- Main NEVER reads: code files, project structure
- Sub-agent results: max 5 lines, no prose
- **NO `git checkout` in the main agent** -- Main stays on BASE_BRANCH
- `.build/` lives in repo root (NOT in worktree)

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

## Follow-Up Queue

**Write logic (for all agents):**
```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
mkdir -p "$REPO_ROOT/.build/"
QUEUE_FILE="$REPO_ROOT/.build/followup_queue.json"
# Read (if exists), otherwise initialize
# Append new item to items[]
# Write queue file
```

**Queue format:**
```json
{
  "source_task": "{ID}",
  "items": [
    {
      "id": "FQ-001",
      "category": "VERIFY|REFAC|IDEA",
      "source_agent": "execute-task|review|test|testfix|validate",
      "source_phase": "2|2.5|2c|3|3b|1*",
      "title": "{short title}",
      "description": "{description}",
      "affected_files": ["path/to/file.ts"],
      "priority": "high|medium|low",
      "auto_testable": true|false
    }
  ]
}
```

**Which agents write:**

| Agent | Phase | What it finds |
|-------|-------|--------------|
| execute-task | 2 (Impl) | Code that should be refactored but is out of scope |
| execute-task | 2.5 (AC-Gate) | Side findings during AC check |
| review | 2c | Architecture concerns, potential side effects, tech debt |
| test | 3 | Areas not testable due to missing abstractions |
| testfix | 3b | Recurring patterns indicating structural problems |
| validate | 1* | Legacy code that could be reused |

**Rules:**
1. Queue is **append-only** during the pipeline -- no agent deletes entries from other agents
2. **VERIFY with priority:high** blocks pre-merge (Phase 4c gate)
3. **Max 10 entries** per pipeline run -- forces agents to prioritize
4. Queue is archived in state.json after Phase 6
5. On task retry: queue is cleared (fresh run)

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
- Retry optimization: on retry, lightweight plan validation (pitfalls check only),
  reuse existing tests, pass failure history to learning agent.
- AC-Checklist Gate (Phase 2.5) catches forgotten ACs before Review/Test.
  Without it, ACs are discovered in test or post-merge, wasting iterations.
- Git rebase after revert is destructive: if base branch contains a revert of
  branch commits, `git rebase` silently drops the original commits. Use merge instead.

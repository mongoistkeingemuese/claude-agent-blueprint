# /orchestrator -- Autonomous Task Pipeline

**Arguments:** $ARGUMENTS
(e.g. "only FEAT-003", "from REFAC-002", or empty for full queue)

## Principles

1. Full autonomy -- no user intervention, queue is processed completely
2. Self-healing -- 3 attempts per problem, then skip + document
3. Resume-capable -- state.json is the runtime database
4. **Delegation** -- task execution via `/execute-task` (no duplicated code)
5. **Lean main context** -- Main = queue manager, `/execute-task` = worker
6. **Branch isolation** -- each task on its own branch (managed by /execute-task)
7. **Sequential execution** -- always 1 task at a time, no parallelism

---

## Architecture

```
/orchestrator (Main = Queue Manager)
  |
  |-- Phase 0: Init / Resume
  |-- Phase 1: Queue Build (Sub-Agent)
  |
  |-- Phase 2: Task Execution (Loop over queue)
  |     |
  |     |-- 2.1: Take task from queue
  |     |-- 2.2: Run /execute-task as Sub-Agent  <-- DELEGATION
  |     |       (Branch, Worktree, Impl, Test, Learn, Merge)
  |     |-- 2.3: Process result + validation + retries
  |     |-- 2.4: Deps check (unblocked tasks)
  |     +-- 2.5: Post-merge validation (full test suite on base branch)
  |
  +-- Phase 3: Completion (consistency check, report)
```

---

## Context Rules

| Rule | Details |
|------|---------|
| Main reads | ONLY `docs/orchestrator_state.json` |
| Sub-agent prompts | Max 10 lines with all required paths |
| Sub-agent results | Max 5 lines: STATUS + MERGED + TESTS + LINT + SUMMARY |
| state.json updates | Main: queue/active/history. /execute-task: phase/status/branch/merged |

---

## State Schema

`docs/orchestrator_state.json`

```
features.{ID}.status: "backlog"|"approved"|"in_progress"|"done"|"blocked"|"skipped"
features.{ID}.plan: "docs/backlog/features/FEAT-XXX_name.md"
features.{ID}.deps: ["FEAT-XXX", ...]
features.{ID}.branch: null | "feat/FEAT-XXX_name"
features.{ID}.merged: false | true
features.{ID}.skill: null | "your-skill-name"
orchestrator.status: "idle"|"running"|"paused"|"completed"|"error"
orchestrator.phase: null|"init"|"executing"|"docs_check"|"completed"
orchestrator.base_branch: "main"
queue: [IDs]
active: [IDs]
history: [{id, result, timestamp}]
errors: [{id, phase, error, category, attempts: [{attempt, phase, error, timestamp}]}]
```

**Error Schema Details:**
- `category`: `"fixable"` | `"structural"` -- set by the analysis agent
- `attempts[]`: Complete history of all attempts (not just last error)
- The analysis agent uses the full attempt history to avoid loops

---

## Phase 0: Init / Resume

Read `docs/orchestrator_state.json`.

- **running**: RESUME. Active tasks without "done" back to queue. Done tasks out of queue.
- **paused**: Check blockers. Resolved -> continue. Done tasks out of queue.
- **idle/completed**: Fresh start -> Phase 1.
- **error**: Recovery. "done" -> history. Rest -> queue. Done tasks out of queue.

**Queue Hygiene (on EVERY start/resume):**
Filter queue: only tasks with status "approved" or "in_progress" remain.
Remove tasks with "done", "draft", "skipped".
(`in_progress` = crash recovery or retry with existing branch)

State: status -> "running", base_branch -> "main" (or your configured branch).

---

## Phase 1: Queue Build (Sub-Agent)

Sub-Agent (Explore):

> Read `{ABS_PATH}/docs/orchestrator_state.json`.
> Topological sort: tasks without open deps first.
> Filter: {ARGUMENTS if provided}. Include tasks with status "approved" or "in_progress".
> ("in_progress" = retry or crash recovery with existing branch)
> Sequential order: respect dependencies, one task at a time.
> Result (ONLY 1 line):
> QUEUE: [FEAT-001, BUG-003, ...]

Main: write queue + phase "executing" to state.json.

---

## Phase 2: Task Execution (Loop)

### 2.1 Prepare Task (Main)
Take task ID from queue, move to `active`, status -> "in_progress".

### 2.2 Delegate to /execute-task (Sub-Agent)

> Read and follow `{ABS_PATH}/.claude/commands/execute-task.md`.
> Task-ID: {ID}
> Working directory: {ABS_PATH}
> `cd {ABS_PATH}` as first bash command.
> Execute the COMPLETE /execute-task workflow (pre-flight through Phase 7).
>
> Result (ONLY 5 lines):
> STATUS: done|blocked|failed
> MERGED: true|false
> TESTS: {new} new, {total} total, {passed} passed, {failed} failed
> LINT: OK|FAILED ({N} errors)
> SUMMARY: [1 sentence]

### 2.3 Process Result (Main)

**Validation:**
1. STATUS != "done" -> blocked/failed handling
2. TESTS: `{failed} > 0` -> rejected
3. LINT: "FAILED" -> rejected
4. TESTS: `{new} < 1` -> rejected (exception: REFAC/docs tasks)

**On success:** active -> history with `{id, result: "done", timestamp}`
**On failure:** -> Phase 2.3b (fix analysis)

### 2.3b Fix Analysis (Sub-Agent)

Triggered when:
- `/execute-task` returns STATUS blocked/failed
- Post-merge validation fails (after revert)

**Prerequisite:** `attempts.length < 2` (otherwise -> skip + document)
(Logic: attempt is added AFTER the check. 0 -> retry, 1 -> retry, 2 -> skip = 3 total attempts)

#### Step 1: Document attempt in errors[]

```json
{
  "id": "FEAT-034",
  "phase": "post-merge-validation",
  "error": "61 test failures...",
  "category": null,
  "attempts": [
    {"attempt": 1, "phase": "post-merge-validation", "error": "61 test failures...", "timestamp": "..."},
    {"attempt": 2, "phase": "implement", "error": "lint failed: 12 errors", "timestamp": "..."}
  ]
}
```

#### Step 2: Start analysis agent

Sub-Agent (general-purpose):

> Analyze the failure of task {ID} and update the plan.
> `cd {ABS_PATH}`
>
> ## Context
> - Task plan: `{TASK_FILE}`
> - Failed phase: {PHASE}
> - Error details: {ERROR}
> - Previous attempts: {ATTEMPTS_JSON}
> - Branch (if exists): {BRANCH_NAME}
>
> ## Step 1: Error Analysis
> 1. Read error details and identify root cause
> 2. If branch exists: check `git log --oneline {BRANCH_NAME}` and `git diff {BASE}...{BRANCH_NAME}`
> 3. If post-merge failure: analyze test output and revert diff
> 4. If previous attempts exist: check for repeated errors (loop detection)
>
> ## Step 2: Classify Error
>
> | Category | Criteria | Examples |
> |----------|----------|---------|
> | `fixable` | Clear root cause, plan adjustment suffices | Wrong migration ID, missing import, test fixture missing |
> | `structural` | Design error, architecture mismatch | Incompatible dependency, fundamentally wrong approach |
>
> **Loop detection:** If attempt N has the same error as attempt N-1 -> `structural`
>
> ## Step 3: Update Plan (only for `fixable`)
> 1. Read task plan
> 2. Add/update `## Pitfalls` section:
>    ```markdown
>    ## Pitfalls
>
>    | # | Attempt | Problem | Solution | Source |
>    |---|---------|---------|----------|--------|
>    | 1 | 1 | Missing dependency | Add to requirements | Post-merge: import error |
>    ```
> 3. Adjust affected implementation steps in the plan
> 4. DO NOT change acceptance criteria (scope stays the same)
> 5. Git commit (if branch exists): `fix({ID}): update plan with pitfalls from attempt {N}`
>
> ## Result (ONLY 4 lines):
> CATEGORY: fixable|structural
> ROOT_CAUSE: [1 sentence: what exactly went wrong]
> PITFALLS_ADDED: {count} new pitfalls documented
> PLAN_UPDATED: true|false

#### Step 3: Process Result (Main)

| CATEGORY | Action |
|----------|--------|
| `fixable` | errors[].category -> "fixable", task status -> "in_progress", task back in queue (front), keep branch |
| `structural` | errors[].category -> "structural", task status -> "skipped", skip + document |

**On re-enqueue (fixable):**
1. state.json: remove task from `active`
2. state.json: task status -> "in_progress" (branch already exists)
3. state.json: insert task in `queue` at position 0 (next task)
4. Keep branch -- work continues on existing branch
5. /execute-task Phase 1 detects existing branch, merges base branch in (NO rebase due to revert issues)

**On skip (structural):**
1. Clean up worktree if needed: `git worktree remove --force .claude/worktrees/{ID}` (if still present)
2. Branch is kept (for manual analysis)

### 2.4 Deps Check
Move unblocked tasks (all deps "done") into queue.

### 2.5 Post-Merge Validation

After EVERY successful merge (not just after batches):

**Inline (Main -- no sub-agent).** Fail-fast order:

```bash
cd {ABS_PATH}

# Run your project's test suite
# Adapt these commands to your project:
# e.g., npm test, pytest, cargo test, go test ./...
```

Exit 0 = OK, otherwise FAILED.

- **OK** -> next task
- **FAILED** -> Revert + fix analysis:
  1. Identify last merge commit: `git log -1 --format="%H %s" --merges`
  2. `git revert -m 1 {MERGE_COMMIT_HASH} --no-edit`
  3. state.json: task merged -> false
  4. -> Phase 2.3b (fix analysis with phase "post-merge-validation")

---

## Phase 3: Completion

Sub-Agent: final consistency check for state.json and documentation.

Main: status -> "completed".
Report: X done, Y skipped, Z blocked. List unmerged branches.

---

## Error Handling

| Level | Description |
|-------|-------------|
| 1 | /execute-task fixes inline (bug-fix loop in review/test phases) |
| 1b | Main checks TESTS/LINT fields |
| 2 | **Fix analysis agent** (Phase 2.3b): analyze, classify, update plan + pitfalls |
| 2b | On `fixable`: re-enqueue at queue position 0, existing branch, max 3 total attempts |
| 2c | On `structural`: immediate skip (no further attempt) |
| 3 | After 3 attempts: skip + document (all attempts in errors[]) |
| 4 | Post-merge validation: FAILED -> revert -> fix analysis (Phase 2.3b) |
| Critical | >50% blocked -> pause, output report |

---

## Context Budget

- Sub-agent prompts: max 10 lines
- Sub-agent results: max 5 lines
- Main NEVER reads code files
- Main reads ONLY state.json
- Always sequential: 1 task at a time

---

## RULES

- Main = queue manager. /execute-task = task worker. Strict separation.
- **NO `git checkout` in the main agent** -- Main ALWAYS stays on the base branch
- /execute-task handles: branch, worktree, skill routing, impl, test, learn, merge, docs
- Results: structured, max 5 lines, no prose
- On merge conflict: /execute-task sets merged:false, recommend `/resolve {ID}`
- Fully autonomous -- no human-in-the-loop, process queue completely
- On >50% blocked: output report and pause

## Learnings

- Sequential execution is safer than parallel. No shared-file conflicts,
  simpler debugging, clearer merge history.
- >50% blocked tasks indicate a systematic problem.
  Pause and output report.
- Post-merge validation with auto-revert prevents broken base branch.
  On FAILED: revert + fix analysis + re-enqueue (max 3 attempts), then skip.
- Queue hygiene on every start: filter out done/draft tasks.
  Prevents re-execution and unapproved task execution.
- Fix analysis agent with pitfalls section: analyze errors, classify
  (fixable/structural), update plan, re-enqueue. Max 3 attempts. Attempt history
  prevents loops.
- Structural errors should be skipped immediately: design errors need manual replanning.
  3 attempts waste context budget. Loop detection (same error as previous attempt)
  -> automatically structural.

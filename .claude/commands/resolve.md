# /resolve -- Detect Merge Conflicts and Create Resolution Tasks

Finds branches with merge conflicts, analyzes the cause, and creates a REFAC task
describing the conflict. The actual resolution is handled by the normal pipeline
(`/execute-task`).

**Optional parameter:** $ARGUMENTS (Task-ID, e.g. `FEAT-001`). Without parameter: all unmerged branches.

---

## Phase 1: Find Unmerged Branches

If task ID given:
- Read branch name from `docs/orchestrator_state.json`
- Check: `merged: false` and branch exists

If no task ID:
- Collect all tasks with `merged: false` and set `branch` from state.json
- Display as table (ID, title, branch)
- If none found: "No unmerged branches." -> done

---

## Phase 2: Conflict Analysis (per branch)

1. **Dry-run merge:** `git merge --no-commit --no-ff {BRANCH_NAME}`
   - No conflict: `git merge --abort`. Report: "Branch can be cleanly merged!"
     - Merge directly: `git merge --no-ff {BRANCH_NAME} -m "merge({ID}): {title}"`
     - Update state.json: `merged: true`
     - No REFAC task needed -> next branch or done
   - Conflict: continue with step 2

2. **Collect conflicts:** `git diff --name-only --diff-filter=U`
3. **Collect context:**
   - `git log --oneline {BASE}..{BRANCH_NAME}` -- branch commits
   - `git log --oneline {BRANCH_NAME}..{BASE}` -- base commits since fork
4. **Abort merge:** `git merge --abort`

---

## Phase 2b: Duplicate and Loop Check

Before creating a new task:

1. **Does a REFAC task for this branch already exist?**
   - Search state.json `refactors` for tasks containing `{ORIGINAL_ID}`
   - If found AND "approved"/"in_progress": NO new task
   - If found AND "done" but branch still `merged: false`: check retry counter

2. **Retry counter (max 2 attempts):**
   - `resolve_attempts.{ORIGINAL_ID}` in state.json (default: 0)
   - >= 2: escalate to user (manual intervention needed)
   - < 2: increment, continue with Phase 3

---

## Phase 3: Create REFAC Task

1. Determine next free REFAC ID
2. Create task file: `docs/backlog/refactor/REFAC-{NNN}_resolve_{ORIGINAL_ID}.md`
3. Update state.json with new REFAC entry
4. Commit: `docs(REFAC-{NNN}): add plan for merge conflict resolution {ORIGINAL_ID}`

---

## Phase 4: Summary

```
=== /resolve Result ===

Cleanly merged:    {N} branches
Tasks created:     {N} REFAC tasks

New tasks:
  REFAC-{NNN}: Resolve merge conflict {ID} ({N} files)

Next step: /execute-task REFAC-{NNN}
```

---

## Rules

- Main = dispatcher: detects + documents conflicts, does NOT resolve them itself
- Cleanly mergeable branches are merged directly
- Real conflicts -> REFAC task -> pipeline resolves them
- **NO `git checkout` in main agent** -- main stays on base branch
- State path: `docs/orchestrator_state.json`

## Learnings

- Git rebase after revert is destructive: if the base branch contains a revert of
  the branch commits, `git rebase` silently drops the original commits. Instead of
  rebase, changes must be re-implemented or cherry-picked.

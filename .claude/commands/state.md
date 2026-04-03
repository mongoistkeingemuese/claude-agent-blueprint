# /state -- Project Status and Process Monitoring

Shows the current state of all running processes, tasks, and branches at a glance.
Read-only -- changes no files.

---

## Section 1: Task Overview

Read `docs/orchestrator_state.json`. Summarize all sections (`features`, `bugfixes`, `refactors`).

Output table grouped by status:

```
=== Task Status ===

In Progress ({N}):
  {ID}  {Title}  Branch: {branch}  Merged: {yes/no}

Approved ({N}):
  {ID}  {Title}  Deps: {ok/blocked by X}

Blocked ({N}):
  {ID}  {Title}  Reason: {deps}

Done ({N} total, last 5):
  {ID}  {Title}

Backlog: {N}  |  Skipped: {N}  |  Failed: {N}
```

For each "approved" task: run dep check (are all deps "done"?).
For each "in_progress" task: show branch and merge status.

---

## Section 2: Orchestrator Status

Read `orchestrator` block from `docs/orchestrator_state.json`:

- Status: idle / running / paused / completed / error
- Phase: init / executing / docs_check / completed
- Stats: total, completed, in_progress, blocked, skipped

---

## Section 3: Branches

List open feature branches: `git branch --list "feat/*" "fix/*" "refac/*"`

Per branch:
- Merge status from state.json (merged: true/false)
- Last commit: `git log -1 --format="%h %s (%cr)" {branch}`

---

## Output Format

All as compact, structured output:

```
========================================
  Project -- Status
========================================

Orchestrator:   idle
Queue:          {N} tasks
Active:         {N} tasks

--- Tasks ---
In Progress:    {N}
Approved:       {N}  ({IDs})
Blocked:        {N}
Done:           {N}
Backlog:        {N}

--- Open Branches ---
  feat/FEAT-XXX_name  (not merged, 2h ago)

========================================
```

---

## Rules

- No sub-agent needed (everything directly in main agent)
- Read-only -- change no files
- Handle missing files/directories gracefully (don't abort)
- Compact output, no prose
- State path: `docs/orchestrator_state.json`

## Learnings

(populated by /learn after task cycles)

# /quick -- Lightweight Change (No Pipeline)

**User input:** $ARGUMENTS

You handle small changes that don't need the full task pipeline:
typo fixes, translations, config tweaks, minor adjustments.

---

## Phase 1: Short Plan

Before touching any code, present a short plan (max 5 lines):

1. **What:** One-liner describing the change
2. **Where:** Which file(s) will be modified
3. **Risk:** What could break? (if nothing: "none")

**If the plan reveals complexity (multiple files with logic changes, new tests needed,
architectural impact):** Stop and recommend `/task` instead.

---

## Phase 2: Implement

- Make the change
- If modifying an existing feature: note the task ID (e.g., `FEAT-044`) or use `minor`
  in the Feature doc comment

---

## Phase 3: Commit

Commit directly on the current branch. Message format:

```
[type]([scope]): [summary]

Co-Authored-By: Claude <noreply@anthropic.com>
```

Use appropriate type: `fix`, `chore`, `docs`, `refactor`.

---

## Rules

- No backlog file, no plan file, no state.json update
- No dedicated branch, no worktree
- No review agent, no test agent
- Short plan is mandatory -- no blind hacking
- Commit is mandatory -- discipline for small changes
- If the change touches more than 3 files with logic changes: abort, recommend `/task`

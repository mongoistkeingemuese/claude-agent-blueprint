# Claude Agent System

10 focused agents for autonomous task execution with deep plan validation, white-box review, black-box testing, intelligent test-fix analysis, and continuous learning.

---

## Architecture

```
/orchestrator (Queue Manager)
  |
  +-- /task (Planning + Validation)
  |     +-- Acceptance criteria, edge cases, interface
  |
  +-- /execute-task (Task Worker)
        |
        +-- Phase 0: Pre-Flight (ID, deps, skill)
        +-- Phase 1: Branch + Worktree
        +-- Phase 2: Implementation (or skill delegation)
        |     +-- Your specialist agents
        |     +-- or normal feature cycle
        +-- Phase 2b: Rebase
        +-- Phase 2c: /review (White-Box Code Review)
        +-- Phase 2d: Review Fix Loop (max 2)
        +-- Phase 3: /test (Black-Box Acceptance Tests)
        +-- Phase 3b: /testfix (Test Failure Analysis, max 3)
        +-- Phase 4: Pre-Merge Validation (full test suite)
        +-- Phase 5: Auto-Merge to base branch
        +-- Phase 6: Documentation Update
        +-- Phase 7: /learn (Post-Task Learning)
```

---

## Command Reference

### Orchestration (3)

| Command | Purpose | Calls |
|---------|---------|-------|
| `/orchestrator` | Autonomous task pipeline, queue management | `/execute-task` |
| `/execute-task` | Task worker: branch, impl, test, learn, merge | `/test`, `/learn`, specialists |
| `/task` | Task planning with validation | Validation sub-agent |

### Quality Assurance (5)

| Command | Purpose | Key Property |
|---------|---------|-------------|
| `/validate` | Deep plan validation against codebase | Manual after `/task`, checks plan against code reality |
| `/review` | White-box code review | Knows code + plan, checks quality, no code changes |
| `/test` | Black-box acceptance tests | Knows ONLY task plan, not the code |
| `/testfix` | Intelligent test failure analysis | Decides per test: fix code or fix test, no coverage loss |
| `/learn` | Post-task learning | Writes learnings directly into agent MDs |

### Read-Only Tools (2)

| Command | Purpose |
|---------|---------|
| `/state` | Project status and task overview |
| `/resolve` | Detect merge conflicts and create resolution tasks |

---

## Skill Routing

`/execute-task` detects the skill from the task plan and delegates:

```
Task has skill: "your-skill"  --> /your-skill (specialist agent)
Task has skill: null            -> normal feature cycle
```

Add your own specialists by:
1. Creating a `.claude/commands/{skill}.md` file
2. Adding the skill to the routing table in `/execute-task`
3. Defining trigger keywords in `/task`

See `templates/specialist.md` for a template.

---

## Test Policy

- Code review by /review before tests (white-box, merge blocker on critical findings)
- Each requirement has min. 1 test (merge blocker)
- Min. 3 edge cases per task (merge blocker)
- 0 failed tests (merge blocker)
- Linting clean (merge blocker)
- Tests written by /test, NOT by the implementer (black-box)
- On failures: `/testfix` analyzes per test whether code or test needs adjustment (no coverage loss)

---

## State Management

- **State file:** `docs/orchestrator_state.json`
- **Base branch:** configurable (default: `main`)
- **Task plans:** `docs/backlog/{features,bugfix,refactor}/`
- **Templates:** `docs/templates/{feature,bugfix,refactor}.md`

---

## Result Format (Standard)

```
STATUS: done|blocked|failed
FILES: [created/changed files]
TESTS: {new} new, {total} total, {passed} passed, {failed} failed
LINT: OK|FAILED ({N} errors)
SUMMARY: [1 sentence]
```

---

## Agent Requirements

Every agent has:
- **Skill routing marker** in header: `<!-- skill: name -->`
- **Result format** (5 lines)
- **`## Learnings` section** (populated by /learn after tasks)

---

## Pipeline

```
/task (Plan) -> /execute-task (Implement) -> /review (White-Box) -> /test (Black-Box) -> /testfix (Failures) -> /learn (Feedback)
     |                |                           |                       |                       |                      |
     v                v                           v                       v                       v                      v
 Acceptance       Branch + Worktree           Code quality           Independent tests       Per-test analysis:      Learnings into
 criteria         Skill routing               Conventions            Test behavior            Fix code OR test       agent MDs
 Edge cases       Pre-merge validation        Security basics        Not code structure       No coverage loss

Optional after /task:  /validate (manual) -- deep plan validation against codebase
```

# CLAUDE.md -- Project Name

This file is the single source of truth for AI assistants working on this codebase.

## Project Overview

**Your Project** is a brief description of what this project does.

**Tech stack:** List your technologies here.

## Repository Structure

```
your-project/
├── src/                     # Source code
├── tests/                   # Tests
├── docs/                    # Documentation
│   ├── backlog/             # Task plans
│   │   ├── features/        # FEAT-XXX plans
│   │   ├── bugfix/          # BUG-XXX plans
│   │   └── refactor/        # REFAC-XXX plans
│   ├── templates/           # Plan templates
│   └── orchestrator_state.json  # Agent state
├── .build/                  # Runtime artifacts (gitignored)
│   └── followup_queue.json  # Follow-up queue (agents write here)
├── .claude/
│   └── commands/            # Agent system (11 core agents)
└── ...
```

## Development Commands

```bash
# Adapt these to your project:
# Start dev environment
# Run tests
# Run linter
# Build
```

## Code Conventions

### Documentation Standard

Every class and function should have a structured comment:

```
Purpose: What the object does.
Usage: How it is used.
Rationale: Why this implementation was chosen.
Feature: FEAT-044, BUG-012 (task IDs that created or modified this code)
```

**Feature Traceability (Long-Term Memory):**
- The `Feature:` line links code to its originating tasks -- creating traceable
  long-term memory across the codebase.
- When **creating** new code: add the current task ID.
- When **modifying** existing code: append the current task ID.
- This enables git-blame-free understanding of why code exists.

## Testing

Describe your test setup, frameworks, and conventions here.

## Agent System

The project uses a hybrid agent architecture: orchestrator + execute-task + state.json
combined with specialists, a black-box test agent, and a learning agent.
See `.claude/commands/README.md` for full documentation.

### Agent Commands (11 core)

| Command | Purpose |
|---------|---------|
| `/bootstrap` | Project onboarding: scan project, generate skills + docs |
| `/orchestrator` | Autonomous task pipeline (queue manager) |
| `/execute-task` | Task worker: branch, implement, review, test, learn, merge |
| `/task` | Task planning with validation (acceptance criteria, edge cases, test spec) |
| `/validate` | Deep plan validation against codebase (manual or auto-triggered) |
| `/state` | Show project status (read-only) |
| `/resolve` | Merge conflict resolution |
| `/review` | White-box code review (plan-version check, AC change prohibition) |
| `/test` | Black-box acceptance tests (plan-version check, independent from implementer) |
| `/testfix` | Intelligent test failure analysis (per-test: fix code or fix test) |
| `/learn` | Post-task learning, writes learnings into agent MDs |

### Skill Routing

| Skill | Specialist | Trigger Keywords |
|-------|-----------|-----------------|
| *(add your skills)* | `/your-skill` | Your, Keywords, Here |

### Task Pipeline

```
/task (Plan) -> /execute-task (Implement) -> [/review || /test] (parallel) -> /testfix (Failures) -> /learn (background)
     |                |                               |                              |                       |
     v                v                               v                              v                       v
 Acceptance       Branch + Worktree          White-Box + Black-Box            Per-test analysis:       Fire-and-forget
 criteria         Skill routing              launched in parallel              Fix code OR test         Writes into agent MDs
 Edge cases       Plan-Check (1b)            Code quality + tests              Re-test after code fix   Non-blocking
 Test spec        AC-Gate (2.5)              AC change prohibition             Follow-Up Queue          Next task starts
                  Coverage-Check (4b)        Plan-Version check                                         immediately
                  Follow-Up Queue (6)
```

### Quality Gates

| Gate | Phase | What it checks |
|------|-------|---------------|
| Plan Check | 1b | 8-check suite against codebase (absorbs former auto-validate heuristic) |
| AC-Checklist Gate | 2.5 | Every AC has corresponding code |
| White-Box Review | 2c/3 | Code quality, conventions, plan-version (parallel with Test) |
| Black-Box Tests | 2c/3 | Independent tests from plan only (parallel with Review) |
| Test-Coverage Check | 4b | Each AC mapped to at least one test |
| Follow-Up Queue Gate | 4c | VERIFY/high items block merge |

### Runtime Artifacts

- `.build/followup_queue.json` -- agents collect out-of-scope findings here (gitignored)

## Commit Format

```
[type]([scope]): [summary]

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

## General Behavior

- **Language:** English for code and comments.
- **Ambiguity:** State ambiguity and ask clarifying questions before proceeding.
- **Challenge premises:** If user premises conflict with your knowledge, challenge them constructively.

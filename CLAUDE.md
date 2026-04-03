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
/task (Plan) -> /execute-task (Implement) -> /review (White-Box) -> /test (Black-Box) -> /testfix (Failures) -> /learn (Feedback)
     |                |                           |                       |                       |                      |
     v                v                           v                       v                       v                      v
 Acceptance       Branch + Worktree           Code quality           Independent tests       Per-test analysis:      Learnings into
 criteria         Skill routing               Conventions            Test behavior            Fix code OR test       agent MDs
 Edge cases       Auto-Validate (1*)          AC change prohibition  Plan-Version check      Learnings categories
 Test spec        AC-Gate (2.5)               Plan-Version check     Follow-Up Queue         Follow-Up Queue
                  Coverage-Check (4b)         Follow-Up Queue
                  Follow-Up Queue (6)
```

### Quality Gates

| Gate | Phase | What it checks |
|------|-------|---------------|
| Plan Validation | 1b | 8-check suite against codebase |
| Auto-Validate | 1* | Deep validation for complex tasks (heuristic trigger) |
| AC-Checklist Gate | 2.5 | Every AC has corresponding code |
| White-Box Review | 2c | Code quality, conventions, plan-version |
| Black-Box Tests | 3 | Independent tests from plan only |
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

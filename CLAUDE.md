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
├── .claude/
│   └── commands/            # Agent system (10 agents)
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

### Agent Commands (10 core)

| Command | Purpose |
|---------|---------|
| `/orchestrator` | Autonomous task pipeline (queue manager) |
| `/execute-task` | Task worker: branch, implement, review, test, learn, merge |
| `/task` | Task planning with validation (acceptance criteria, edge cases) |
| `/validate` | Deep plan validation against codebase |
| `/state` | Show project status (read-only) |
| `/resolve` | Merge conflict resolution |
| `/review` | White-box code review (quality, conventions, security) |
| `/test` | Black-box acceptance tests (independent from implementer) |
| `/testfix` | Intelligent test failure analysis (per-test: fix code or fix test) |
| `/learn` | Post-task learning, writes learnings into agent MDs |

### Skill Routing

| Skill | Specialist | Trigger Keywords |
|-------|-----------|-----------------|
| *(add your skills)* | `/your-skill` | Your, Keywords, Here |

### Task Pipeline

```
/task (Plan) -> /execute-task (Implement) -> /review (White-Box) -> /test (Black-Box) -> /testfix (Failures) -> /learn (Feedback)
```

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

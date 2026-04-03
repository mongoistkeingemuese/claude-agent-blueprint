# Getting Started

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and configured
- A git repository for your project
- A working test suite (the agent system relies on tests as quality gates)

## Quick Start (5 minutes)

### 1. Copy the agent commands

```bash
# From your project root:
cp -r /path/to/claude-agent-blueprint/.claude .
```

This gives you the `.claude/commands/` directory with all 10 agent commands.

### 2. Add the agent sections to your CLAUDE.md

If you don't have a `CLAUDE.md` yet, copy the template:

```bash
cp /path/to/claude-agent-blueprint/CLAUDE.md .
```

If you already have one, add the "Agent System" section from the template.
The key sections are:
- Agent Commands table
- Skill Routing table
- Task Pipeline diagram

### 3. Create the state directory structure

```bash
mkdir -p docs/backlog/{features,bugfix,refactor,tests}
mkdir -p docs/templates
```

### 4. Create the initial state file

```bash
cat > docs/orchestrator_state.json << 'EOF'
{
  "orchestrator": {
    "status": "idle",
    "phase": null,
    "base_branch": "main"
  },
  "features": {},
  "bugfixes": {},
  "refactors": {},
  "tests": {},
  "queue": [],
  "active": [],
  "history": [],
  "errors": []
}
EOF
```

### 5. Create task plan templates

Create `docs/templates/feature.md`:

```markdown
# {ID}: {Title}

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Category** | Feature |
| **Skill** | null |
| **Dependencies** | none |

## Summary
{What and why}

## Acceptance Criteria
- [ ] AC-1: {precise, testable criterion}
- [ ] AC-2: {precise, testable criterion}

## Edge Cases (min. 3)
| Edge Case | Trigger | Expected Behavior | Severity |
|-----------|---------|-------------------|----------|
| EC-1 | ... | ... | Medium |
| EC-2 | ... | ... | High |
| EC-3 | ... | ... | Low |

## Public Interface
- Endpoints: ...
- Exports: ...
- Store changes: ...

## Implementation Steps
1. ...
2. ...

## Cross-Cutting Checklist
- [ ] Production Readiness (error handling, validation, cleanup)
- [ ] Legacy / Tech Debt (identified, no new workarounds)
- [ ] Test Requirements (unit, integration, edge cases)
- [ ] Persistence (migrations, state)
- [ ] Documentation (docstrings, CLAUDE.md if needed)
```

Create similar templates for `bugfix.md` and `refactor.md`.

### 6. Adapt test commands

Edit `.claude/commands/execute-task.md` Phase 4 and `.claude/commands/orchestrator.md`
Phase 2.5 to use your project's test and lint commands:

```bash
# Replace the placeholder commands with your actual commands:
# npm test
# pytest
# cargo test
# go test ./...
```

## First Task

Try planning a task:

```
/task Add input validation to the user registration endpoint
```

This will:
1. Categorize the task (likely FEAT or BUG)
2. Reserve an ID (e.g., FEAT-001)
3. Create a plan with acceptance criteria and edge cases
4. Validate the plan
5. Ask for your approval

Once approved, execute it:

```
/execute-task FEAT-001
```

Or run the full pipeline:

```
/orchestrator
```

## Adapting to Your Project

The agent system is designed to be project-agnostic. The main customization points are:

1. **Test commands** -- in `/execute-task` and `/orchestrator`
2. **Lint commands** -- same locations
3. **Skill routing** -- in `/task` and `/execute-task`
4. **Specialist agents** -- add `.claude/commands/{skill}.md` files
5. **CLAUDE.md conventions** -- `/review` checks against your conventions
6. **Task templates** -- in `docs/templates/`

See [CUSTOMIZATION.md](CUSTOMIZATION.md) for detailed guidance.

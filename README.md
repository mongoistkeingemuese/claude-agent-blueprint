# Claude Agent Blueprint

A production-tested agent system for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that brings structure, quality gates, and continuous learning to AI-assisted software development.

**This is a blueprint/framework, not a finished tool.** Copy it into your project, adapt it to your stack, and let the agents evolve through use.

## Why?

AI coding assistants are powerful, but complex projects need structure:

- **Without structure:** "implement this feature" leads to forgotten edge cases, no tests, inconsistent quality, and no learning from mistakes.
- **With this system:** tasks are planned with testable criteria, implemented in isolation, reviewed by a separate agent, tested by a black-box tester, and lessons are written back into the agents themselves.

This system was extracted from a production project ([Cortex 3D HMI Platform](https://github.com/mongoistkeingemuese/3DViewer)) where it managed 50+ tasks across 800+ tests with a 100% success rate and <0.5 human interventions per session.

## Architecture

```
                          +------------------+
                          |  /orchestrator   |
                          |  (Queue Manager) |
                          +--------+---------+
                                   |
                    +--------------+--------------+
                    |                             |
             +------+-------+              +-----+------+
             |    /task      |              | /execute-  |
             | (Plan + Validate)           |    task     |
             +--------------+              | (Worker)   |
                                           +-----+------+
                                                 |
                          +----------+-----------+-----------+----------+
                          |          |           |           |          |
                    +-----+--+ +----+---+ +-----+----+ +---+----+ +---+----+
                    | /review| | /test  | | /testfix | | /learn | | /skill |
                    | White  | | Black  | | Failure  | | Feed-  | | Domain |
                    | Box    | | Box    | | Analysis | | back   | | Expert |
                    +--------+ +--------+ +----------+ +--------+ +--------+
```

### Pipeline

```
/task         Plan with acceptance criteria, edge cases, public interface
    |
/execute-task Branch + worktree isolation, implementation (or skill delegation)
    |
/review       White-box code review against plan (quality, conventions, security)
    |
/test         Black-box acceptance tests (knows plan, NOT the code)
    |
/testfix      Per-test analysis: fix code OR adjust test (no coverage loss)
    |
/learn        Write actionable insights into agent MDs (self-evolution)
```

### Self-Healing Pipeline

```
Attempt 1 fails
  -> Fix analysis classifies: fixable or structural?
  -> fixable: update plan with pitfalls, re-enqueue
  -> structural: skip immediately
Attempt 2 fails
  -> Same analysis, pitfalls accumulate
Attempt 3 fails
  -> Skip and document

Post-merge failure
  -> Auto-revert, fix analysis, re-enqueue
```

## What's Included

```
claude-agent-blueprint/
+-- .claude/commands/
|   +-- README.md            # Agent system documentation
|   +-- orchestrator.md      # Queue manager (autonomous pipeline)
|   +-- execute-task.md      # Task worker (branch, impl, test, merge)
|   +-- task.md              # Task planning with validation
|   +-- validate.md          # Deep plan validation against codebase
|   +-- review.md            # White-box code review
|   +-- test.md              # Black-box acceptance tests
|   +-- testfix.md           # Intelligent test failure analysis
|   +-- learn.md             # Post-task learning (self-evolution)
|   +-- state.md             # Project status viewer (read-only)
|   +-- resolve.md           # Merge conflict resolution
+-- CLAUDE.md                # Template project instructions
+-- docs/
|   +-- ARCHITECTURE.md      # How the agent system works
|   +-- GETTING_STARTED.md   # Integration guide (5 min)
|   +-- CUSTOMIZATION.md     # Adding specialists, adapting pipeline
|   +-- SKILL_ROUTING.md     # Domain delegation concept
+-- examples/
|   +-- specialist-plugin.md # Example: plugin development specialist
|   +-- specialist-deploy.md # Example: deployment specialist
|   +-- state.json           # Example orchestrator state
+-- templates/
|   +-- specialist.md        # Template for custom specialists
|   +-- CLAUDE.md.template   # CLAUDE.md template with agent sections
+-- LICENSE                  # MIT
```

## Quick Start

```bash
# 1. Copy agent commands into your project
cp -r claude-agent-blueprint/.claude your-project/

# 2. Create state directory
mkdir -p your-project/docs/backlog/{features,bugfix,refactor,tests}
mkdir -p your-project/docs/templates

# 3. Initialize state
cp claude-agent-blueprint/examples/state.json your-project/docs/orchestrator_state.json
# Edit: clear the example data, set your base_branch

# 4. Add agent sections to your CLAUDE.md
# See templates/CLAUDE.md.template

# 5. Adapt test/lint commands in execute-task.md and orchestrator.md

# 6. Plan your first task
# In Claude Code: /task Add input validation to user registration
```

See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for detailed instructions.

## Skill Routing

Specialists handle domain-specific tasks. The system routes based on keywords:

| Skill | Specialist | When to Use |
|-------|-----------|-------------|
| `null` | General purpose | Default -- no specialist needed |
| `deploy` | `/deploy` | Docker, CI/CD, infrastructure |
| `plugin` | `/plugin` | Plugin SDK, sandbox, manifest |
| *(yours)* | `/{skill}` | Add your own domains |

Add a specialist in 3 steps:
1. Create `.claude/commands/{skill}.md` (use `templates/specialist.md`)
2. Add trigger keywords to `/task`
3. Add routing entry to `/execute-task`

See [docs/SKILL_ROUTING.md](docs/SKILL_ROUTING.md) and [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md).

## Key Concepts

### Separation of Implementation and Testing
The test agent never sees the implementation code. It writes tests purely from the task plan's acceptance criteria and edge cases. This catches bugs that the implementer's bias would miss.

### Self-Evolving Agents
After each task, the learning agent writes concrete insights into the relevant agent's `## Learnings` section. Next time that agent runs, the insight is in context. Agents get better at their job over time.

### Worktree Isolation
Each task runs in a git worktree. The base branch is never touched during implementation. Failed tasks can be reverted cleanly. Crash recovery works because the worktree and branch persist.

### Structured Error Recovery
Failures are classified as `fixable` (plan updated with pitfalls, retried) or `structural` (skipped immediately). Post-merge failures trigger automatic revert + re-analysis. Max 3 attempts before skip.

## Built With This

This agent system was developed and battle-tested on the [Cortex 3D HMI Platform](https://github.com/mongoistkeingemuese/3DViewer) -- a production web-based 3D digital twin with Python/FastAPI backend, React/TypeScript frontend, and a plugin system. The system managed 50+ autonomous task executions across 800+ tests.

## Limitations

- **Requires Claude Code** -- the slash commands (`/orchestrator`, `/task`, etc.) are Claude Code features
- **Requires a test suite** -- the pipeline uses tests as quality gates; without tests, the review/test/testfix cycle has no teeth
- **Token-intensive** -- each task goes through multiple sub-agent calls; complex tasks can consume significant context
- **Single-threaded** -- tasks execute sequentially by design (parallel execution causes merge conflicts)

## License

MIT -- see [LICENSE](LICENSE).

**Provided as-is, no support.** This is a blueprint extracted from production use. Adapt it to your needs.

# Claude Agent Blueprint

A production-tested agent system for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that brings structure, quality gates, and continuous learning to AI-assisted software development.

**This is a blueprint/framework, not a finished tool.** Copy it into your project, adapt it to your stack, and let the agents evolve through use.

## Why?

AI coding assistants are powerful, but complex projects need structure:

- **Without structure:** "implement this feature" leads to forgotten edge cases, no tests, inconsistent quality, and no learning from mistakes.
- **With this system:** tasks are planned with testable criteria, implemented in isolation, reviewed by a separate agent, tested by a black-box tester, and lessons are written back into the agents themselves.

This system was extracted from a production project ([Cortex 3D HMI Platform](https://github.com/mongoistkeingemuese/3DViewer)) where it managed 50+ tasks across 800+ tests with a 100% success rate and <0.5 human interventions per session.

## How to Use It

### 0. `/bootstrap` — Set up a new project (start here)

Scans your project, detects frameworks/domains, and auto-generates skills + documentation.

```
/bootstrap
```

Runs in 3 phases:
1. **Scout** — analyzes languages, frameworks, structure, existing docs
2. **Propose** — presents a plan (which skills, which docs) and **waits for your approval**
3. **Generate** — launches up to 5 parallel subagents to create skills + docs

Creates: domain skills (frontend, backend, database, etc.), README, ARCHITECTURE.md, CLAUDE.md extensions, state.json, and optionally a roadmap from GitHub issues.

Modes: `skills-only`, `docs-only`, `refresh` (update existing without overwriting learnings).

### 1. `/task` — Plan a task

Creates a task plan in the backlog with acceptance criteria, edge cases, public interface definition, and a test specification for the black-box agent.

```
/task Add WebSocket reconnection with exponential backoff
```

This creates e.g. `docs/backlog/features/FEAT-055_websocket_reconnection.md` with:
- Acceptance criteria (testable conditions)
- Edge cases (min. 3)
- Public interface (what gets exported/exposed)
- Test specification (for the black-box agent)
- Cross-cutting checklist
- Plan-Version tracking
- Suggested skill routing

### 2. `/validate` — Validate a plan

Deep-checks a task plan against the actual codebase before execution. Catches conflicts, missing dependencies, wrong assumptions. Can be triggered manually or automatically by the pipeline (Phase 1*).

```
/validate FEAT-055
```

### 3. `/execute-task` — Run a single task manually

Picks a task, creates a branch + worktree, implements it, runs 7 quality gates (review, test, coverage check, etc.), and merges back.

```
/execute-task FEAT-055
```

This is the **manual mode** — you control which task runs and when. Best for:
- Tasks that need human oversight
- Running multiple tasks in parallel (each in its own worktree)
- Debugging pipeline issues

### 4. `/orchestrator` — Run all open tasks automatically

The autonomous mode. Processes the entire backlog sequentially:

```
/orchestrator
```

It picks the next open task, executes the full pipeline (plan → implement → review → test → learn → merge), then moves to the next one. Failed tasks get retried up to 3 times with accumulated learnings.

### 5. Other commands

| Command | Purpose |
|---------|---------|
| `/review` | White-box code review against the plan (with plan-version check) |
| `/test` | Black-box acceptance tests (never sees implementation, plan-version check) |
| `/testfix` | Per-test failure analysis: fix code OR fix test (with learnings template) |
| `/learn` | Write insights back into agent MDs (self-evolution) |
| `/state` | Show project status (read-only) |
| `/resolve` | Merge conflict resolution |

## QA Hardening (7 Quality Gates)

The pipeline includes 7 quality gates that prevent defects from reaching the base branch:

| # | Gate | Phase | Blocking? |
|---|------|-------|-----------|
| 1 | **Plan Validation** | 1b | 8-check suite validates plan against codebase |
| 2 | **Auto-Validate** | 1* | Heuristic-triggered deep validation for complex tasks |
| 3 | **AC-Checklist Gate** | 2.5 | Every acceptance criterion must have corresponding code |
| 4 | **White-Box Review** | 2c | Code review with AC change prohibition |
| 5 | **Black-Box Tests** | 3 | Independent tests from plan only (plan-version check) |
| 6 | **Test-Coverage Check** | 4b | Each AC mapped to at least one test |
| 7 | **Follow-Up Queue Gate** | 4c | VERIFY/high items block merge |

### Follow-Up Queue

Agents collect out-of-scope findings during pipeline execution into `.build/followup_queue.json` (a gitignored runtime artifact). Categories: VERIFY (side effects to check), REFAC (cleanup opportunities), IDEA (future improvements). VERIFY/high items block the pre-merge gate (Phase 4c). Per-task items are presented in Phase 6 for triage. After the full queue is processed, the orchestrator outputs a consolidated follow-up summary (Phase 3b) grouped by category with source task and priority.

### Plan-Version Propagation

Task plans carry a `Plan-Version` header that is incremented on revision. Review and Test agents receive the version and check for mismatches -- ensuring they always work against the current plan.

## Skills vs. Pipeline

This system has two distinct layers that work together:

### Pipeline (the assembly line)

The pipeline is **protocol** — it defines *how* tasks flow through the system regardless of domain:

```
/task → /execute-task → /review → /test → /testfix → /learn
```

Every task goes through the same stages. The pipeline ensures quality gates, worktree isolation, structured error recovery, and learning. It knows nothing about your domain — it only knows process.

### Skills (domain experts)

Skills are **domain knowledge** — they know *what* to do for specific types of work:

| Skill | Specialist | When to Use |
|-------|-----------|-------------|
| `deploy` | `/deploy` | Docker, CI/CD, infrastructure |
| `plugin` | `/plugin` | Plugin SDK, sandbox, manifest |
| *(yours)* | `/{skill}` | Add your own domains |

A skill is a `.claude/commands/{skill}.md` file that contains domain-specific instructions, conventions, patterns, and learnings. When `/execute-task` detects that a task matches a skill (via keywords in the plan), it delegates to that specialist.

**The difference:**
- **Pipeline** = "plan it, implement it, review it, test it, learn from it" (same for every task)
- **Skill** = "here's how we write plugins in this project" or "here's how deployments work" (domain-specific)

Add a skill in 3 steps:
1. Create `.claude/commands/{skill}.md` (use `templates/specialist.md`)
2. Add trigger keywords to `/task`
3. Add routing entry to `/execute-task`

See [docs/SKILL_ROUTING.md](docs/SKILL_ROUTING.md) and [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md).

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

### Self-Healing Pipeline

```
Attempt 1 fails
  -> Fix analysis classifies: fixable or structural?
  -> fixable: update plan with pitfalls, re-enqueue
  -> structural: skip immediately
Attempt 2 fails
  -> Same analysis, pitfalls accumulate
  -> Lightweight validation (pitfalls-only, not full 8-check)
  -> Reuse existing tests from previous attempt
Attempt 3 fails
  -> Skip and document

Post-merge failure
  -> Auto-revert, fix analysis, re-enqueue
```

## Learnings from Production Use

### Parallelization: manual mode only

Running multiple `/execute-task` commands in parallel (each in its own worktree) works — but **only in manual mode**. The `/orchestrator` processes tasks sequentially by design.

Why: Merge conflicts from parallel branches are often not resolved cleanly by the agents and lead to subtle issues. If you parallelize, do it manually and handle merges yourself.

### Parallelization works — you are the bottleneck

The orchestrator can be parallelized cleanly. Multiple `/execute-task` instances in separate worktrees, proper merge ordering via dependency graph — technically all solvable. The LLM handles branching, testing, merging, and conflict resolution just fine.

**The bottleneck is you.** Every completed task needs human evaluation: reviewing the diff, verifying test quality, checking that the LLM didn't hallucinate edge cases or silently weaken assertions. With 4+ tasks finishing around the same time, you can't keep up and start rubber-stamping — which defeats the entire point.

**You are responsible for the code that ships.** The LLM is a tool, not a colleague. It doesn't understand your business domain, it doesn't know which shortcuts will bite you in production, and it can't judge whether a passing test actually proves correctness. If you skip review because the pipeline is green, you're outsourcing your accountability to a language model.

Practical limit: **max 3 parallel tasks.** More than that and review quality drops below useful.

### The orchestrator respects dependencies but doesn't optimize

`/orchestrator` does topological sorting — tasks with unresolved deps wait until their dependencies are done. But it doesn't batch related changes, optimize for minimal merge conflicts, or reason about which tasks benefit from being executed together.

For complex multi-task work where execution order matters beyond simple deps, use `/execute-task` manually.

### Performance benchmark

In production use: **~45 tasks in ~12.5 hours** (~20 min/task average including retries and failures) with all quality gates active. Simple tasks finish faster, complex ones with retries take longer.

**Pro tip: run multiple Claude Code instances in parallel.** Keep one instance running `/orchestrator` for execution while 3-4 other instances plan tasks (`/task`, `/validate`). The orchestrator grinds through the queue while you feed it from multiple planners — the backlog never runs dry. This setup got us to **75 tasks in 12.5 hours** in production.

## What's Included

```
claude-agent-blueprint/
├── .claude/commands/
│   ├── README.md            # Agent system documentation
│   ├── bootstrap.md         # Project onboarding (auto-generate skills + docs)
│   ├── orchestrator.md      # Queue manager (autonomous pipeline)
│   ├── execute-task.md      # Task worker (branch, impl, test, merge)
│   ├── task.md              # Task planning with validation
│   ├── validate.md          # Deep plan validation against codebase
│   ├── review.md            # White-box code review
│   ├── test.md              # Black-box acceptance tests
│   ├── testfix.md           # Intelligent test failure analysis
│   ├── learn.md             # Post-task learning (self-evolution)
│   ├── state.md             # Project status viewer (read-only)
│   └── resolve.md           # Merge conflict resolution
├── CLAUDE.md                # Template project instructions
├── docs/
│   ├── ARCHITECTURE.md      # How the agent system works
│   ├── GETTING_STARTED.md   # Integration guide (5 min)
│   ├── CUSTOMIZATION.md     # Adding specialists, adapting pipeline
│   └── SKILL_ROUTING.md     # Domain delegation concept
├── examples/
│   ├── specialist-plugin.md # Example: plugin development specialist
│   ├── specialist-deploy.md # Example: deployment specialist
│   └── state.json           # Example orchestrator state
├── templates/
│   ├── feature.md           # Task plan template: new features
│   ├── bugfix.md            # Task plan template: bug fixes
│   ├── refactor.md          # Task plan template: refactoring
│   ├── checklist.md         # Cross-cutting checklist (included in all plans)
│   ├── specialist.md        # Template for custom specialists
│   └── CLAUDE.md.template   # CLAUDE.md template with agent sections
└── LICENSE                  # MIT
```

## Quick Start

### Option A: Automated (recommended)

```bash
# 1. Copy agent commands into your project
cp -r claude-agent-blueprint/.claude your-project/

# 2. Run bootstrap -- it handles the rest
# In Claude Code:
/bootstrap
```

Bootstrap will scan your project, propose skills + docs, and generate everything after your approval.

**Important: review the templates after setup.** The task plan templates (`templates/feature.md`, `bugfix.md`, `refactor.md`, `checklist.md`) are generic starting points. Go through them once and adapt to your project's stack — add your test framework, your persistence layer, your UI conventions, your CI pipeline. The more specific your templates are, the better the plans and the fewer retries you'll need.

### Option B: Manual

```bash
# 1. Copy agent commands into your project
cp -r claude-agent-blueprint/.claude your-project/

# 2. Create state directory
mkdir -p your-project/docs/backlog/{features,bugfix,refactor,tests}
mkdir -p your-project/docs/templates

# 3. Initialize state
cp claude-agent-blueprint/examples/state.json your-project/docs/orchestrator_state.json
# Edit: clear the example data, set your base_branch

# 4. Add .build/ to .gitignore (runtime artifacts: follow-up queue)
echo '.build/' >> your-project/.gitignore

# 5. Add agent sections to your CLAUDE.md
# See templates/CLAUDE.md.template

# 6. Adapt test/lint commands in execute-task.md and orchestrator.md

# 7. Plan your first task
# In Claude Code: /task Add input validation to user registration

# 8. Validate and execute
# /validate FEAT-001
# /execute-task FEAT-001
```

See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for detailed instructions.

## Key Concepts

### Separation of Implementation and Testing
The test agent never sees the implementation code. It writes tests purely from the task plan's acceptance criteria, test specification, and edge cases. This catches bugs that the implementer's bias would miss.

### Self-Evolving Agents
After each task, the learning agent writes concrete insights into the relevant agent's `## Learnings` section. Next time that agent runs, the insight is in context. Agents get better at their job over time.

### Worktree Isolation
Each task runs in a git worktree. The base branch is never touched during implementation. Failed tasks can be reverted cleanly. Crash recovery works because the worktree and branch persist.

### Structured Error Recovery
Failures are classified as `fixable` (plan updated with pitfalls, retried) or `structural` (skipped immediately). Post-merge failures trigger automatic revert + re-analysis. Retries use lightweight validation (pitfalls-only) and reuse existing tests. Max 3 attempts before skip.

### Follow-Up Queue
Agents collect out-of-scope findings during pipeline execution (cleanup opportunities, side effects to verify, ideas). VERIFY/high items block pre-merge. After the orchestrator finishes all tasks, Phase 3b presents a grouped summary (VERIFY/REFAC/IDEA) with source task and priority — one place for the user to triage everything.

## Built With This

This agent system was developed and battle-tested on the [Cortex 3D HMI Platform](https://github.com/mongoistkeingemuese/3DViewer) -- a production web-based 3D digital twin with Python/FastAPI backend, React/TypeScript frontend, and a plugin system. The system managed 50+ autonomous task executions across 800+ tests.

## Limitations

- **Requires Claude Code** -- the slash commands (`/orchestrator`, `/task`, etc.) are Claude Code features
- **Requires a test suite** -- the pipeline uses tests as quality gates; without tests, the review/test/testfix cycle has no teeth
- **Token-intensive** -- each task goes through multiple sub-agent calls; complex tasks can consume significant context
- **Sequential by design** -- the orchestrator runs tasks one at a time; parallel execution is possible manually but merge conflicts are your responsibility

## License

MIT -- see [LICENSE](LICENSE).

**Provided as-is, no support.** This is a blueprint extracted from production use. Adapt it to your needs.

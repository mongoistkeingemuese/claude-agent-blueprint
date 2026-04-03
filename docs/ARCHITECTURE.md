# Agent System Architecture

## Overview

This system provides structured, autonomous task execution for Claude Code projects.
It separates concerns into specialized agents that communicate through a shared state
file and structured result formats.

## Core Design Decisions

### 1. Orchestrator-Worker Pattern

The orchestrator (`/orchestrator`) is a thin queue manager. It never reads code files,
never implements features, and never runs tests. Its only job is to manage the task queue,
delegate to `/execute-task`, and process results.

```
Orchestrator (Queue Manager)
  |
  +-- Reads: ONLY state.json
  +-- Writes: queue, active, history, errors
  +-- Delegates: ALL work to /execute-task sub-agents
  +-- Validates: result format (5 lines), test counts, lint status
```

This separation keeps the orchestrator's context window lean, allowing it to manage
dozens of tasks without running out of context.

### 2. Worktree Isolation

Each task runs in a git worktree (`.claude/worktrees/{ID}/`). This means:
- The base branch is never touched during implementation
- Multiple tasks don't interfere with each other
- Failed tasks can be reverted without affecting the base branch
- Crash recovery is possible (worktree + branch still exist)

### 3. Separation of Implementation and Testing

The test agent (`/test`) operates as a **black-box tester**. It receives:
- The task plan (what should be implemented)
- The public interface (how to interact with it)

It does NOT receive:
- The implementation code
- Internal function names
- The git diff

This separation catches bugs that the implementer's bias would miss.

### 4. Self-Evolving Agents via Learnings

After each task, the learning agent (`/learn`) analyzes what happened and writes
concrete, actionable insights directly into the relevant agent's `## Learnings`
section. Next time that agent runs, the learning is in its context.

This creates a feedback loop:
```
Task fails at /test
  -> /testfix fixes it
  -> /learn writes "when doing X, also check Y" into /test's learnings
  -> Next time /test runs, it checks Y proactively
```

### 5. Skill Routing

Domain-specific tasks are delegated to specialist agents. The routing is based on
a `skill` field in the task plan:

```
/execute-task reads task plan
  -> skill: "deploy" -> delegates to /deploy specialist
  -> skill: null -> implements inline (general-purpose sub-agent)
```

This keeps specialists focused and their context clean. A deploy specialist doesn't
need to know about UI patterns, and vice versa.

## State Machine

```
Task Lifecycle:
  backlog -> approved -> in_progress -> done
                |             |
                v             v
              skipped      blocked -> (retry) -> in_progress
                                   -> (skip)  -> skipped
```

```
Orchestrator Lifecycle:
  idle -> running -> completed
           |    |
           v    v
         paused  error -> (recovery) -> running
```

## Agent Communication

Agents communicate through two channels:

1. **state.json** -- persistent state (task status, branches, errors)
2. **Structured results** -- ephemeral (5-line format passed between agents)

There is no direct agent-to-agent communication. The orchestrator mediates all
interactions, keeping the system predictable and debuggable.

## Error Handling Strategy

```
Level 1: Inline fixes
  /execute-task fixes small issues during implementation

Level 2: Review/test loops
  /review finds issues -> fix loop (max 2)
  /test finds failures -> /testfix (max 3)

Level 3: Fix analysis
  Orchestrator's fix-analysis agent classifies errors:
  - fixable: update plan with pitfalls, re-enqueue
  - structural: skip immediately

Level 4: Post-merge validation
  Full test suite on base branch after merge
  Failure -> revert + fix analysis

Level 5: Circuit breaker
  >50% tasks blocked -> pause + report
```

## Context Budget Management

The system is designed to be context-efficient:

| Agent | Reads | Context Size |
|-------|-------|-------------|
| Orchestrator | state.json only | Minimal |
| Execute-task | task plan + state.json | Medium |
| Review | task plan + git diff | Medium |
| Test | task plan only (no code!) | Small |
| Learn | results from review + test | Small |
| Validate | task plan + affected files | Large (but manual/rare) |

Sub-agent prompts are capped at 10 lines. Results at 5 lines. This prevents
context overflow in long orchestration sessions.

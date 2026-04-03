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
  +-- Reads: ONLY state.json + .build/followup_queue.json
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
- The test specification (public interface, expected behavior, edge cases)
- The plan version (to detect stale plans)

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

### 6. Plan-Version Propagation

Task plans carry a `Plan-Version` header that is incremented whenever the plan is
revised (e.g., after validation findings or retry with pitfalls). The version is
passed to `/review` and `/test`, which check for mismatches before starting work.

This prevents agents from working against an outdated plan -- a common source of
false test failures and irrelevant review findings.

### 7. Follow-Up Queue

Agents collect out-of-scope findings during pipeline execution into
`.build/followup_queue.json` (a gitignored runtime artifact). This prevents
scope creep while ensuring nothing is lost.

```
Agent finds something out-of-scope during work
  -> Writes to .build/followup_queue.json
  -> Categories: VERIFY (side effects), REFAC (cleanup), IDEA (future)
  -> Priority: high / medium / low
  -> VERIFY/high items block pre-merge (Phase 4c)
  -> All items presented to user in Phase 6
```

Each entry includes: `source_agent`, `source_phase`, `category`, `priority`,
`description`, and `related_files`.

## Quality Gates (7-Gate Pipeline)

```
Phase 0:   Pre-Flight (ID, deps, skill, optional infra check)
Phase 1:   Branch + Worktree
Phase 1b:  Plan Validation (8-check suite)
Phase 1*:  Auto-Validate Trigger (heuristic: REFAC/FEAT + >3 ACs or >3 files or keywords)
Phase 2:   Implementation (or skill delegation)
Phase 2.5: AC-Checklist Gate (every AC must have corresponding code -- BLOCKING)
Phase 2b:  Rebase
Phase 2c:  /review (White-Box, plan-version check, AC change prohibition)
Phase 2d:  Review Fix Loop (max 2)
Phase 3:   /test (Black-Box, plan-version check)
Phase 3b:  /testfix (max 3, with learnings template)
Phase 4:   Pre-Merge Validation (full test suite)
Phase 4b:  Test-Coverage Check (AC-to-test mapping -- BLOCKING)
Phase 4c:  Follow-Up Queue VERIFY/high Gate (BLOCKING)
Phase 5:   Auto-Merge to base branch
Phase 6:   Documentation Update + Follow-Up Presentation
Phase 7:   /learn (Post-Task Learning)
```

### Gate Details

| Gate | Checks | Blocking? |
|------|--------|-----------|
| **Plan Validation (1b)** | Files & paths, interfaces & signatures, recently merged changes, AC testability, scope & side effects, production readiness, edge cases, test specification | Yes -- invalid plan stops pipeline |
| **Auto-Validate (1*)** | Full `/validate` deep check | Yes on RISK high (user confirmation needed) |
| **AC-Checklist (2.5)** | Each AC has corresponding implementation | Yes -- missing ACs stop pipeline |
| **Review (2c)** | Code quality, conventions, plan conformance | Yes on Critical findings |
| **Tests (3)** | Black-box acceptance tests from plan | Yes -- 0 failures required |
| **Coverage (4b)** | Each AC mapped to >= 1 test | Yes -- AC coverage < 100% = FAIL |
| **Follow-Up (4c)** | No VERIFY/high items in queue | Yes -- must be resolved first |

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

Agents communicate through three channels:

1. **state.json** -- persistent state (task status, branches, errors)
2. **Structured results** -- ephemeral (5-line format passed between agents)
3. **Follow-Up Queue** -- `.build/followup_queue.json` (runtime artifact, agents append findings)

There is no direct agent-to-agent communication. The orchestrator mediates all
interactions, keeping the system predictable and debuggable.

## Error Handling Strategy

```
Level 1: Inline fixes
  /execute-task fixes small issues during implementation

Level 2: Review/test loops
  /review finds issues -> fix loop (max 2)
  /test finds failures -> /testfix (max 3, with per-test categorization)

Level 3: Fix analysis
  Orchestrator's fix-analysis agent classifies errors:
  - fixable: update plan with pitfalls, re-enqueue
  - structural: skip immediately

Level 4: Retry optimization
  Retries use lightweight validation (pitfalls-only, not full 8-check)
  Reuse existing tests from previous attempt
  Pass failure history to /learn

Level 5: Post-merge validation
  Full test suite on base branch after merge
  Failure -> revert + fix analysis

Level 6: Circuit breaker
  >50% tasks blocked -> pause + report
```

## Context Budget Management

The system is designed to be context-efficient:

| Agent | Reads | Context Size |
|-------|-------|-------------|
| Orchestrator | state.json + followup_queue.json | Minimal |
| Execute-task | task plan + state.json | Medium |
| Review | task plan + git diff + plan-version | Medium |
| Test | task plan + test spec only (no code!) | Small |
| Testfix | failed tests + task plan + git diff | Medium |
| Learn | results from review + test + retry info | Small |
| Validate | task plan + affected files + callers | Large (but manual/rare) |

Sub-agent prompts are capped at 10 lines. Results at 5 lines. This prevents
context overflow in long orchestration sessions.

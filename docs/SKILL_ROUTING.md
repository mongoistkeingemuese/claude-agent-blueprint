# Skill Routing

## Concept

Skill routing is the mechanism by which `/execute-task` delegates implementation
to specialized agents. Instead of one monolithic implementation agent that needs
to know everything, domain-specific tasks are handled by focused specialists.

## How It Works

```
1. /task plans a task and detects a skill from trigger keywords
2. The skill is stored in state.json: features.{ID}.skill = "deploy"
3. /execute-task reads the skill during pre-flight (Phase 0)
4. During implementation (Phase 2b), it delegates to the specialist:
   skill: "deploy" -> reads and follows .claude/commands/deploy.md
5. The specialist implements the task within the worktree
6. Control returns to /execute-task for review, test, merge, learn
```

## Routing Flow

```
/execute-task
  |
  +-- Phase 0: Read skill from state.json or task plan
  |
  +-- Phase 2b: Skill Routing Decision
        |
        +-- skill: "deploy"     --> Sub-Agent reads /deploy.md
        +-- skill: "api"        --> Sub-Agent reads /api.md
        +-- skill: "frontend"   --> Sub-Agent reads /frontend.md
        +-- skill: null          --> General-purpose sub-agent
        |
        +-- All specialists return the same 5-line result format
        |
  +-- Phase 2c: /review (same for all skills)
  +-- Phase 3:  /test   (same for all skills)
  +-- Phase 7:  /learn  (writes to specialist's ## Learnings)
```

## Skill Detection in /task

The task planner (`/task`) detects skills from keywords in the task description:

```
"Add Docker health check"  -> keywords: Docker -> skill: deploy
"Fix login form validation" -> keywords: none   -> skill: null
"Update i18n translations"  -> keywords: i18n   -> skill: translate
```

The detection is based on a simple keyword table in `/task` Phase 1c.
If no keywords match, the skill is `null` and `/execute-task` uses a
general-purpose implementation agent.

## What Specialists Do (and Don't Do)

**Specialists handle:**
- Domain-specific implementation
- Domain-specific verification (e.g., build checks, type checks)
- Domain-specific patterns and conventions

**Specialists do NOT handle:**
- Branch management (done by /execute-task)
- Code review (done by /review)
- Testing (done by /test)
- Learning (done by /learn)
- Merge (done by /execute-task)

This separation means specialists stay focused on their domain while
the pipeline handles quality assurance uniformly.

## Specialist Context

Each specialist has its own `.md` file with:

1. **Architecture section** -- key files, directory structure
2. **Workflow** -- domain-specific steps
3. **Patterns** -- code patterns specific to the domain
4. **Verification** -- domain-specific checks
5. **Learnings** -- accumulated insights from past tasks

The learnings section grows over time, making the specialist
progressively better at its domain.

## Example: Adding a "database" Specialist

### 1. Create `.claude/commands/database.md`

```markdown
<!-- skill: database -->

# /database -- Database Schema and Migration Specialist

You handle database schema changes, migrations, seed data, and query optimization.

## Key Files
- migrations/
- models/
- ...

## Workflow
1. Check current schema
2. Create migration
3. Update models
4. Verify migration up/down

## Verification
- Migration applies cleanly
- Migration rolls back cleanly
- No data loss

## Learnings
(populated by /learn)
```

### 2. Add to `/task` Phase 1c

```markdown
| Migration, Schema, Database, Model, Query | `database` | Database changes |
```

### 3. Add to `/execute-task` routing table

```markdown
Task has skill: "database" --> /database
```

### 4. Add to CLAUDE.md

```markdown
| `database` | `/database` | Migration, Schema, Database, Model, Query |
```

## Skill Composition

A task can only have ONE skill. If a task spans multiple domains:

1. **Prefer null skill** -- the general-purpose agent handles it
2. **Split the task** -- create separate tasks with dependencies
3. **Pick the primary domain** -- if one domain dominates, use that skill

The `/task` planner handles this decision during planning.

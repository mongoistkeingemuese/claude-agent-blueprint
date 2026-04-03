# Customization Guide

## Adding Specialist Agents

Specialists handle domain-specific tasks that require focused context and knowledge.

### When to Create a Specialist

Create a specialist when:
- A domain has its own patterns, conventions, and pitfalls
- The domain knowledge would bloat `/execute-task`'s context
- Multiple tasks share the same domain (e.g., all deployment tasks)
- The domain has specific verification steps

### Step 1: Create the Specialist File

Create `.claude/commands/{skill-name}.md`. Use the template at `templates/specialist.md`.

Key sections every specialist needs:
- **Skill marker:** `<!-- skill: your-skill -->` in the header
- **Architecture overview:** key files and their purposes
- **Workflow:** step-by-step for the domain
- **Verification:** how to check the work is correct
- **Result format:** standard 5-line format
- **Learnings section:** empty, populated by `/learn`

### Step 2: Register the Skill

Add the skill to three places:

**1. `/task` (Phase 1c: Skill Detection)**
```markdown
| Trigger Keywords | Skill | Description |
|-----------------|-------|-------------|
| Docker, Deploy, Container | `deploy` | Deployment tasks |
| Your, Keywords, Here | `your-skill` | Your domain |
```

**2. `/execute-task` (Phase 0: Skill Routing Table)**
```markdown
Task has skill: "your-skill"  --> /your-skill
```

**3. CLAUDE.md (Skill Routing section)**
```markdown
| `your-skill` | `/your-skill` | Your, Keywords, Here |
```

### Step 3: Test It

```
/task Do something in your domain
```

The task planner should detect the skill and tag the plan. Then:

```
/execute-task {TASK-ID}
```

Should delegate to your specialist.

---

## Customizing the Pipeline

### Changing the Base Branch

In `docs/orchestrator_state.json`:
```json
"orchestrator": {
  "base_branch": "develop"
}
```

### Adjusting Test Commands

The test commands appear in two places:

1. **`/execute-task` Phase 4** (pre-merge validation in worktree)
2. **`/orchestrator` Phase 2.5** (post-merge validation on base branch)

Replace the placeholder comments with your actual commands.

### Adjusting Lint Commands

Same locations as test commands. The result format uses `LINT` instead of
project-specific tool names (like TSC) so it works with any linter.

### Changing Task ID Format

The default format is `{TYPE}-{NNN}` (e.g., FEAT-001, BUG-042).
To change it, edit:
- `/execute-task` Phase 0 (ID validation regex)
- `/task` Phase 1b (ID reservation)
- Branch naming in `/execute-task` Phase 1

### Changing the Task Plan Structure

Edit the templates in `docs/templates/`. The mandatory sections
(acceptance criteria, edge cases, public interface) are referenced by
`/task`, `/validate`, `/review`, and `/test`, so keep those.

---

## Customizing Review Checks

`/review` Phase 4 checks code against CLAUDE.md conventions. To customize:

1. Define your conventions in CLAUDE.md (code style, docstrings, naming, etc.)
2. `/review` will automatically check against them

For skill-specific review checks, add a section to `/review`:

```markdown
## Skill-Specific Review Checklists

| Skill | Additional Review Checks |
|-------|--------------------------|
| `deploy` | Health checks defined, env vars documented, volumes correct |
| `your-skill` | Your specific checks here |
```

---

## Customizing Edge Case Requirements

`/validate` Phase 4c and `/test` check for skill-specific mandatory edge cases.
Add your own:

```markdown
## Skill-Specific Mandatory Edge Cases

| Skill | Mandatory Edge Cases |
|-------|---------------------|
| `deploy` | Container unreachable, port conflict, migration error |
| `your-skill` | Your mandatory edge cases here |
```

---

## Scaling Considerations

### Small Projects (< 50 files)
- You may not need specialists -- null skill handles everything
- `/validate` may be overkill -- use `/task` validation only
- State management is still valuable for tracking progress

### Medium Projects (50-500 files)
- Add 2-3 specialists for your main domains
- Use `/validate` for complex features
- The full pipeline pays off

### Large Projects (500+ files)
- Specialists are essential to keep context focused
- `/validate` is critical to catch side effects
- Consider splitting large features into smaller tasks with dependencies
- The queue system handles dependency chains automatically

### Multi-Developer Projects
- Each developer can run `/orchestrator` on their own task subset
- Use separate base branches if needed
- The state.json file tracks who is working on what
- Merge conflicts are handled by `/resolve`

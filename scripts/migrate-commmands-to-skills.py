# This script migrates existing command-based workflows from the .claude/commands directory
# to the new skill-based architecture in .claude/skills. It also generates a master orchestrator prompt
# that serves as the central entry point for the autonomous agent, utilizing any existing logic from an old orchestrator.md if it existed, 
# and incorporating project intelligence from CLAUDE.md
#
# Usage: Run this script from the root of your project where the .claude directory is located. It will automatically handle the migration and prompt generation.
# python scripts/migrate-commmands-to-skills.py
#
# Note: Commands/md files will stay in place for reference but will be ignored by the system after migration

import os
import re
import shutil

# Define the source and destination directories relative to where the script is run
SOURCE_DIR = ".claude/commands"
DEST_DIR = ".claude/skills"
PROMPTS_DIR = ".github/prompts"

# Curated skill descriptions. Copilot/Claude use `description` to decide WHEN to
# auto-load a skill, so each must state what it does AND when to use it -- a bare
# title (the heading fallback) reduces auto-discovery. Skills not listed here fall
# back to extract_description().
SKILL_DESCRIPTIONS = {
    "bootstrap": "Onboards a new or existing project: scans the codebase and generates the skill set + docs. Use when setting up the agent system in a fresh repo, or re-scanning an existing project to refresh its skills and documentation.",
    "execute-task": "Executes a single planned task end-to-end on its own branch: implement, white-box review, black-box test, learn, merge. Use when a task (FEAT/BUG/REFAC) is planned and approved and you want it fully implemented and merged.",
    "learn": "Captures post-task learnings and writes actionable insights back into the agent skill files. Use after a task finishes to record what worked or failed so the agents improve over time.",
    "quick": "Handles a small, low-risk change directly with a short mandatory plan, bypassing the full task pipeline. Use for minor edits (typo, copy, tiny fix) that don't warrant a full plan/review/test/merge cycle.",
    "resolve": "Detects merge conflicts, analyzes their root cause, and creates resolution tasks for the pipeline (it does not resolve conflicts directly). Use when a branch merge hits conflicts that need systematic handling.",
    "review": "White-box code review of an implementation against its plan: checks code quality, conventions, plan-version match, and prohibits acceptance-criteria changes. Use right after implementing a task, in parallel with black-box tests.",
    "state": "Read-only project status report: shows the queue, active task, current pipeline phase, and history from orchestrator_state.json. Use when you want to inspect progress without changing anything.",
    "task": "Plans a task with validation: defines acceptance criteria, edge cases, and a test spec, then sanity-checks the plan against the codebase. Use before implementing any non-trivial feature, bugfix, or refactor.",
    "test": "Black-box acceptance testing derived only from the plan, independent of the implementer: verifies behavior against acceptance criteria and checks plan-version. Use right after implementation, in parallel with white-box review.",
    "testfix": "Analyzes failing tests one by one and decides per test whether to fix the code or the test, re-running after each code fix. Use when review or test reports test failures.",
    "validate": "Deep validation of a task plan against the actual codebase (8-check suite). Use to vet a plan before execution -- manually, or auto-triggered for complex tasks.",
    "readme": "Reference overview of the Claude Agent System: architecture, the command/skill pipeline, state management, and quality gates. Use when you need to understand how the agent system fits together; this is reference material, not an executable workflow.",
}

# Skills that are reference docs rather than workflows -- never auto-invoked.
NON_INVOCABLE_SKILLS = {"readme"}

def to_kebab_case(name):
    """Converts a string to kebab-case (e.g., 'My_Command' -> 'my-command')."""
    name = re.sub(r'[\s_]+', '-', name)
    return name.lower()

def rewrite_command_paths(content):
    """
    Rewrites legacy .claude/commands/<x>.md references to their new location so
    migrated skills cross-reference each other correctly:
      - orchestrator.md  -> .github/prompts/orchestrator.prompt.md (it becomes a prompt)
      - {skill}.md / *.md placeholders -> .claude/skills/{skill}/SKILL.md (kept literal)
      - <name>.md        -> .claude/skills/<name>/SKILL.md
    """
    content = content.replace(".claude/commands/orchestrator.md", ".github/prompts/orchestrator.prompt.md")
    content = content.replace(".claude/commands/*.md", ".claude/skills/*/SKILL.md")
    # {skill}, {TASK_SKILL}, ... -- keep brace placeholders intact
    content = re.sub(r'\.claude/commands/(\{[\w]+\})\.md', r'.claude/skills/\1/SKILL.md', content)
    content = re.sub(r'\.claude/commands/([\w-]+)\.md', r'.claude/skills/\1/SKILL.md', content)
    return content

def extract_description(content, default_name):
    """
    Attempts to parse a meaningful description from the file's first heading.
    """
    match = re.search(r'^#+\s*(?:/[\w-]+\s*(?:--|-|:)\s*)?(.*)$', content, re.MULTILINE)
    if match and match.group(1).strip():
        return match.group(1).strip()
    return f"Automated skill rules for {default_name}"

def generate_orchestrator(skills, custom_orchestrator_content=None):
    """
    Generates the master orchestrator prompt, utilizing CLAUDE.md for project intelligence
    and custom orchestrator logic if it existed in the old commands.
    """
    os.makedirs(PROMPTS_DIR, exist_ok=True)
    prompt_path = os.path.join(PROMPTS_DIR, "orchestrator.prompt.md")
    
    claude_md_path = "CLAUDE.md"
    tdd_workflow = ""
    slash_commands = ""
    
    # Extract workflow intelligence from CLAUDE.md if available
    if os.path.exists(claude_md_path):
        with open(claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Extract TDD Workflow
            tdd_match = re.search(r'^##\s+TDD Workflow.*?\n(.*?)(?:^##\s|\Z)', content, re.MULTILINE | re.DOTALL)
            if tdd_match:
                tdd_workflow = tdd_match.group(1).strip()
                
            # Extract Slash Commands
            cmd_match = re.search(r'^##\s+Slash Commands.*?\n(.*?)(?:^##\s|\Z)', content, re.MULTILINE | re.DOTALL)
            if cmd_match:
                slash_commands = cmd_match.group(1).strip()

    # Format the list of available skills
    skills_list_md = "\n".join([f"- **`{s['name']}`**: {s['description']}" for s in skills])

    # Construct the orchestrator prompt
    orchestrator_content = f"""---
name: orchestrator
description: Autonomous Task Pipeline (Main Entrypoint). Use to process the task queue end-to-end -- build the queue, run each task via the execute-task skill, validate, retry, and report. Requires tool access (terminal, edits, git).
agent: agent
argument-hint: e.g. "only FEAT-003", "from REFAC-002", or empty for the full queue
---
"""
    
    # If the user had a specific orchestrator.md, use its logic
    if custom_orchestrator_content:
        # Strip out the legacy '# /orchestrator --' header to clean it up
        clean_content = re.sub(r'^#\s*/[\w-]+\s*(?:--|-|:)\s*.*$', '', custom_orchestrator_content, count=1, flags=re.MULTILINE).strip()
        
        # Replace old $ARGUMENTS syntax with VS Code Prompt inputs
        clean_content = clean_content.replace("$ARGUMENTS", "${input:arguments}")
        
        # Update references to old command paths to refer to new skill/prompt files
        clean_content = rewrite_command_paths(clean_content)
        
        if not clean_content.startswith('# '):
            orchestrator_content += "# Autonomous Task Pipeline\n\n"
        orchestrator_content += clean_content + "\n\n"
    else:
        # Fallback if no orchestrator.md was found
        orchestrator_content += f"""# Task Orchestration Pipeline

You are the Lead Orchestrator Agent. I will provide arguments via `${{input:arguments}}`.
Your job is to coordinate the available skills to fulfill the request efficiently and completely.

"""

    orchestrator_content += f"""## Available Agent Skills
You have access to the following skills. You must explicitly invoke them (e.g. "Delegating to the `[skill-name]` skill") when their domain is required by the pipeline:
{skills_list_md}

"""
    if slash_commands:
         orchestrator_content += f"""## Legacy Command Mapping
The user might refer to old commands. Map them to the skills above according to this reference:
{slash_commands}

"""
    if tdd_workflow:
        orchestrator_content += f"""## Required Workflow Pipeline
You MUST strictly adhere to the following workflow sequence during task execution:
{tdd_workflow}

"""

    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(orchestrator_content)
    
    print(f"🤖 Orchestrator prompt generated at: {prompt_path} (Using legacy orchestrator logic)")

def main():
    if not os.path.exists(SOURCE_DIR):
        print(f"❌ Error: Source directory '{SOURCE_DIR}' not found. Please run this in the root of your project.")
        return

    os.makedirs(DEST_DIR, exist_ok=True)
    print(f"📁 Verified destination directory: {DEST_DIR}")

    migrated_count = 0
    migrated_skills = []
    orchestrator_content = None

    # Iterate through all Markdown files in the old commands directory
    for filename in os.listdir(SOURCE_DIR):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(SOURCE_DIR, filename)
        base_name = os.path.splitext(filename)[0]
        skill_name = to_kebab_case(base_name)
        
        # Intercept the orchestrator command to use as the master prompt
        if filename.lower() == "orchestrator.md":
            with open(filepath, 'r', encoding='utf-8') as f:
                orchestrator_content = f.read()
            print("👑 Intercepted 'orchestrator.md' to build the master Prompt pipeline.")
            
            # Clean up the old orchestrator skill folder if it was created in a previous run
            old_skill_dir = os.path.join(DEST_DIR, skill_name)
            if os.path.exists(old_skill_dir):
                shutil.rmtree(old_skill_dir)
                print(f"🧹 Removed legacy '{skill_name}' folder from skills directory.")
            
            continue # Skip normal skill creation for this file

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Prefer a curated description (what + when); fall back to the heading.
        description = SKILL_DESCRIPTIONS.get(skill_name) or extract_description(content, skill_name)

        # 1. Create the specific skill directory
        skill_dir = os.path.join(DEST_DIR, skill_name)
        os.makedirs(skill_dir, exist_ok=True)

        # 2. Define the new file path (must be named SKILL.md)
        dest_filepath = os.path.join(skill_dir, "SKILL.md")

        # 3. Construct the new file content with YAML frontmatter.
        # Quote the description: it often contains ": " (colon-space), which breaks
        # unquoted YAML plain scalars and would stop the skill from loading.
        desc_yaml = '"' + description.replace("\\", "\\\\").replace('"', '\\"') + '"'
        extra_frontmatter = "disable-model-invocation: true\n" if skill_name in NON_INVOCABLE_SKILLS else ""
        yaml_frontmatter = f"""---
name: {skill_name}
description: {desc_yaml}
{extra_frontmatter}---

"""
        # 4. Write the merged content (rewriting legacy command cross-references)
        with open(dest_filepath, 'w', encoding='utf-8') as f:
            f.write(yaml_frontmatter + rewrite_command_paths(content))
            
        migrated_skills.append({"name": skill_name, "description": description})
        print(f"✅ Migrated: {filename} -> {dest_filepath}")
        migrated_count += 1

    print(f"\n🎉 Migration complete! {migrated_count} workflow components successfully transferred to Skills.")
    
    # Generate the Orchestrator Prompt automatically, passing the intercepted content
    if migrated_skills or orchestrator_content:
        generate_orchestrator(migrated_skills, orchestrator_content)

    print("💡 Tip: Try typing `/orchestrator` in chat to trigger the full Autonomous Pipeline!")

if __name__ == "__main__":
    main()
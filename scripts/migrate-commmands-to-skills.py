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

def to_kebab_case(name):
    """Converts a string to kebab-case (e.g., 'My_Command' -> 'my-command')."""
    name = re.sub(r'[\s_]+', '-', name)
    return name.lower()

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
description: Autonomous Task Pipeline (Main Entrypoint)
---
"""
    
    # If the user had a specific orchestrator.md, use its logic
    if custom_orchestrator_content:
        # Strip out the legacy '# /orchestrator --' header to clean it up
        clean_content = re.sub(r'^#\s*/[\w-]+\s*(?:--|-|:)\s*.*$', '', custom_orchestrator_content, count=1, flags=re.MULTILINE).strip()
        
        # Replace old $ARGUMENTS syntax with VS Code Prompt inputs
        clean_content = clean_content.replace("$ARGUMENTS", "${input:arguments}")
        
        # Update references to old command paths to refer to new skills
        clean_content = re.sub(r'\.claude/commands/([\w-]+)\.md', r'\1 skill', clean_content)
        
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

        description = extract_description(content, skill_name)

        # 1. Create the specific skill directory
        skill_dir = os.path.join(DEST_DIR, skill_name)
        os.makedirs(skill_dir, exist_ok=True)

        # 2. Define the new file path (must be named SKILL.md)
        dest_filepath = os.path.join(skill_dir, "SKILL.md")

        # 3. Construct the new file content with YAML frontmatter
        yaml_frontmatter = f"""---
name: {skill_name}
description: {description}
---

"""
        # 4. Write the merged content
        with open(dest_filepath, 'w', encoding='utf-8') as f:
            f.write(yaml_frontmatter + content)
            
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
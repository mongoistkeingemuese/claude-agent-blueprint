import os
import re

# Define the source and destination directories relative to where the script is run
SOURCE_DIR = ".claude/commands"
DEST_DIR = ".claude/skills"

def to_kebab_case(name):
    """Converts a string to kebab-case (e.g., 'My_Command' -> 'my-command')."""
    # Replace underscores and spaces with hyphens, then lowercase
    name = re.sub(r'[\s_]+', '-', name)
    return name.lower()

def extract_description(content, default_name):
    """
    Attempts to parse a meaningful description from the file's first heading.
    Matches formats like '# /test -- Black-Box Acceptance Tests'
    and extracts 'Black-Box Acceptance Tests'.
    """
    # Look for the first heading (H1, H2, etc.)
    match = re.search(r'^#+\s*(?:/[\w-]+\s*(?:--|-|:)\s*)?(.*)$', content, re.MULTILINE)
    
    if match and match.group(1).strip():
        return match.group(1).strip()
    
    # Fallback if no heading is found
    return f"Automated skill rules for {default_name}"

def main():
    if not os.path.exists(SOURCE_DIR):
        print(f"❌ Error: Source directory '{SOURCE_DIR}' not found. Please run this in the root of your project.")
        return

    # Ensure the destination base directory exists
    os.makedirs(DEST_DIR, exist_ok=True)
    print(f"📁 Verified destination directory: {DEST_DIR}")

    migrated_count = 0

    # Iterate through all Markdown files in the old commands directory
    for filename in os.listdir(SOURCE_DIR):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(SOURCE_DIR, filename)
        base_name = os.path.splitext(filename)[0]
        skill_name = to_kebab_case(base_name)
        
        # Read the original content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Generate the description for the YAML frontmatter
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
        
        print(f"✅ Migrated: {filename} -> {dest_filepath}")
        migrated_count += 1

    print(f"\n🎉 Migration complete! {migrated_count} files successfully transferred to Skills.")
    print("💡 Tip: Because Skills are triggered automatically by the AI, review the generated 'description' in your new SKILL.md files to ensure the AI knows exactly when to use them.")

if __name__ == "__main__":
    main()
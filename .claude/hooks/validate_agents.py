#!/usr/bin/env python3
"""Validate Claude Code agent frontmatter"""

import re
import sys
from pathlib import Path

def validate_agent_frontmatter(agent_file):
    """Validate agent file frontmatter"""

    with open(agent_file, 'r') as f:
        content = f.read()

    # Check for frontmatter
    if not content.startswith('---\n'):
        return False, "Missing frontmatter opening '---'"

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter structure"

    frontmatter = match.group(1)

    # Check required fields
    required_fields = ['name', 'description']
    missing_fields = []

    for field in required_fields:
        pattern = f'^{field}:\\s*.+$'
        if not re.search(pattern, frontmatter, re.MULTILINE):
            missing_fields.append(field)

    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    # Check for quoted values (should be unquoted)
    quoted_pattern = r'^(name|description):\s*["\']'
    if re.search(quoted_pattern, frontmatter, re.MULTILINE):
        return False, "Frontmatter values should be unquoted (remove quotes)"

    return True, "Valid"

def validate_all_agents():
    """Validate all agent files"""

    agent_dirs = [
        Path('.claude') / 'agents',
        Path.home() / '.claude' / 'agents',
    ]

    errors = []

    for agent_dir in agent_dirs:
        if not agent_dir.exists():
            continue

        print(f"🔍 Validating agents in {agent_dir}...")

        for agent_file in agent_dir.glob('*.md'):
            print(f"   📄 {agent_file.name}...", end=' ')

            valid, message = validate_agent_frontmatter(agent_file)

            if valid:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
                errors.append((agent_file, message))

    if errors:
        print(f"\n❌ Found {len(errors)} agent validation error(s):")
        for agent_file, message in errors:
            print(f"   • {agent_file.name}: {message}")
        return False

    print(f"\n✅ All agents valid")
    return True

if __name__ == "__main__":
    success = validate_all_agents()
    sys.exit(0 if success else 1)

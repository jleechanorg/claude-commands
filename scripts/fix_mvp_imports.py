#!/usr/bin/env python3
"""
Simple script to fix HIGH priority inline imports in MVP core files.
"""

import re
from pathlib import Path


def fix_file_imports(filepath: str) -> bool:
    """Fix inline imports in a specific file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Fix specific patterns found in the detection
        if filepath.endswith('memory_integration.py'):
            content = fix_memory_integration(content)
        elif filepath.endswith('mcp_client.py'):
            content = fix_mcp_client(content)
        elif filepath.endswith('main.py'):
            content = fix_main_py(content)

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed imports in {filepath}")
            return True
        else:
            print(f"No changes needed in {filepath}")
            return False

    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False


def fix_memory_integration(content: str) -> str:
    """Fix datetime import in memory_integration.py."""
    # Add datetime import at top if not present
    if 'from datetime import datetime' not in content and 'import datetime' not in content:
        # Find first import or add after docstring
        lines = content.split('\n')
        insert_pos = 0

        # Skip docstring
        in_docstring = False
        for i, line in enumerate(lines):
            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                in_docstring = not in_docstring
                if not in_docstring:
                    insert_pos = i + 1
                    break
            elif not in_docstring and line.strip() and not line.startswith('#'):
                insert_pos = i
                break

        lines.insert(insert_pos, 'from datetime import datetime')
        content = '\n'.join(lines)

    # Remove inline datetime.datetime import
    content = re.sub(r'(\s+)from datetime import datetime\n', '', content)

    return content


def fix_mcp_client(content: str) -> str:
    """Fix tempfile and os imports in mcp_client.py."""
    # Add imports at top if not present
    needs_tempfile = 'import tempfile' not in content
    needs_os = 'import os' not in content and 'from os import' not in content

    if needs_tempfile or needs_os:
        lines = content.split('\n')

        # Find where to insert (after existing imports)
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_pos = i + 1
            elif line.strip() and not line.startswith('#') and not line.startswith('"""'):
                break

        if needs_tempfile:
            lines.insert(insert_pos, 'import tempfile')
            insert_pos += 1
        if needs_os:
            lines.insert(insert_pos, 'import os')

        content = '\n'.join(lines)

    # Remove inline imports
    content = re.sub(r'(\s+)import tempfile\n', '', content)
    content = re.sub(r'(\s+)import os\n', '', content)

    return content


def fix_main_py(content: str) -> str:
    """Fix re import in main.py."""
    # Add re import at top if not present
    if 'import re' not in content:
        lines = content.split('\n')

        # Find where to insert (after existing imports)
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_pos = i + 1
            elif line.strip() and not line.startswith('#') and not line.startswith('"""'):
                break

        lines.insert(insert_pos, 'import re')
        content = '\n'.join(lines)

    # Remove inline re import
    content = re.sub(r'(\s+)import re\n', '', content)

    return content


def main():
    """Fix HIGH priority inline imports in MVP core files."""
    files_to_fix = [
        'mvp_site/memory_integration.py',
        'mvp_site/mcp_client.py',
        'mvp_site/main.py'
    ]

    fixed_count = 0
    for filepath in files_to_fix:
        if Path(filepath).exists():
            if fix_file_imports(filepath):
                fixed_count += 1
        else:
            print(f"File not found: {filepath}")

    print(f"\nFixed imports in {fixed_count} files.")
    return fixed_count


if __name__ == '__main__':
    main()

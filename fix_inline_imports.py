#!/usr/bin/env python3
"""Script to fix inline imports in Python files by moving them to module level."""

import os
import re
import sys
from typing import List, Tuple

def find_inline_imports(content: str) -> List[Tuple[int, str, str]]:
    """Find all inline imports in the content.
    
    Returns list of (line_number, full_line, import_statement)
    """
    lines = content.split('\n')
    inline_imports = []
    
    # Pattern to match imports that are indented (inside functions/classes)
    import_pattern = re.compile(r'^(\s{4,})((?:import|from)\s+.+)$')
    
    for i, line in enumerate(lines):
        match = import_pattern.match(line)
        if match:
            inline_imports.append((i, line, match.group(2)))
    
    return inline_imports

def move_imports_to_top(content: str) -> Tuple[str, int]:
    """Move all inline imports to the module level.
    
    Returns (modified_content, number_of_imports_moved)
    """
    lines = content.split('\n')
    inline_imports = find_inline_imports(content)
    
    if not inline_imports:
        return content, 0
    
    # Extract unique import statements
    import_statements = []
    seen_imports = set()
    
    for _, _, import_stmt in inline_imports:
        normalized = import_stmt.strip()
        if normalized not in seen_imports:
            import_statements.append(normalized)
            seen_imports.add(normalized)
    
    # Find where to insert imports (after module docstring and existing imports)
    insert_position = 0
    in_docstring = False
    docstring_quotes = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Handle module docstrings
        if i < 10 and (stripped.startswith('"""') or stripped.startswith("'''")):
            if not in_docstring:
                in_docstring = True
                docstring_quotes = '"""' if stripped.startswith('"""') else "'''"
                if stripped.endswith(docstring_quotes) and len(stripped) > 6:
                    in_docstring = False
                    insert_position = i + 1
            elif stripped.endswith(docstring_quotes):
                in_docstring = False
                insert_position = i + 1
        # Skip shebang and encoding declarations
        elif i < 3 and (stripped.startswith('#!') or 'coding:' in stripped or 'coding=' in stripped):
            insert_position = i + 1
        # Find the last import statement
        elif stripped.startswith(('import ', 'from ')) and not in_docstring:
            insert_position = i + 1
        # Stop at first non-import, non-comment line
        elif stripped and not stripped.startswith('#') and not in_docstring:
            break
    
    # Remove inline imports
    new_lines = []
    for i, line in enumerate(lines):
        # Skip inline import lines
        if any(i == imp[0] for imp in inline_imports):
            # Keep empty line to maintain structure
            new_lines.append('')
        else:
            new_lines.append(line)
    
    # Insert imports at the appropriate position
    if import_statements:
        # Add a blank line before new imports if needed
        if insert_position > 0 and lines[insert_position - 1].strip():
            new_lines.insert(insert_position, '')
            insert_position += 1
        
        # Insert the import statements
        for imp in sorted(import_statements):
            new_lines.insert(insert_position, imp)
            insert_position += 1
        
        # Add a blank line after imports if needed
        if insert_position < len(new_lines) and new_lines[insert_position].strip():
            new_lines.insert(insert_position, '')
    
    return '\n'.join(new_lines), len(inline_imports)

def process_file(filepath: str, dry_run: bool = False) -> bool:
    """Process a single Python file to fix inline imports.
    
    Returns True if file was modified.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    modified_content, num_imports = move_imports_to_top(content)
    
    if num_imports > 0:
        if dry_run:
            print(f"Would fix {num_imports} inline imports in: {filepath}")
        else:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                print(f"Fixed {num_imports} inline imports in: {filepath}")
                return True
            except Exception as e:
                print(f"Error writing {filepath}: {e}")
                return False
    
    return False

def main():
    """Main function to process all Python files."""
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print("DRY RUN MODE - No files will be modified")
        print("=" * 60)
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and common excluded directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                python_files.append(filepath)
    
    print(f"Found {len(python_files)} Python files")
    print("Scanning for inline imports...")
    print("=" * 60)
    
    modified_count = 0
    for filepath in sorted(python_files):
        if process_file(filepath, dry_run):
            modified_count += 1
    
    print("=" * 60)
    if dry_run:
        print(f"Would modify {modified_count} files")
        print("\nRun without --dry-run to actually fix the files")
    else:
        print(f"Modified {modified_count} files")

if __name__ == '__main__':
    main()
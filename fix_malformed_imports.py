#!/usr/bin/env python3
"""
Fix malformed imports created by the inline import fixing script.
Identifies and fixes common patterns:
1. Incomplete imports like "from module import (\nfrom other_module..."
2. Empty try/except blocks that should have imports
3. Standalone import lines that should be part of a multi-line import
"""

import os
import re
import sys
from pathlib import Path


def find_python_files(directory, exclude_dirs=None):
    """Find all Python files in the directory, excluding specified directories."""
    if exclude_dirs is None:
        exclude_dirs = set()
    
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Remove excluded directories from dirs list to prevent traversal
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


def fix_malformed_imports(file_path):
    """Fix malformed imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern 1: Fix incomplete multi-line imports
        # Look for "from module import (\nfrom other_module"
        pattern1 = re.compile(r'from\s+[\w.]+\s+import\s+\(\s*\n\s*from\s+', re.MULTILINE)
        matches = pattern1.findall(content)
        if matches:
            print(f"Found incomplete multi-line import in {file_path}")
            # This is complex to fix generically, will need manual inspection
            
        # Pattern 2: Fix empty try/except blocks
        pattern2 = re.compile(r'try:\s*\n\s*\n\s*except\s+ImportError:\s*\n\s*\n', re.MULTILINE)
        if pattern2.search(content):
            print(f"Found empty try/except block in {file_path}")
            
        # Pattern 3: Look for orphaned import lines (indented imports not in blocks)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('from ') and line.startswith('    ') and i > 0:
                prev_line = lines[i-1].strip()
                if not prev_line or not prev_line.endswith(':'):
                    print(f"Potential orphaned import in {file_path}:{i+1}: {line.strip()}")
                    
        return content != original_content
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = 'mvp_site'
    
    # Exclude venv and other irrelevant directories
    exclude_dirs = {'venv', '__pycache__', '.git', 'node_modules'}
    
    print(f"Scanning for malformed imports in {directory}...")
    
    python_files = find_python_files(directory, exclude_dirs)
    print(f"Found {len(python_files)} Python files")
    
    fixed_files = 0
    for file_path in python_files:
        if fix_malformed_imports(file_path):
            fixed_files += 1
    
    print(f"Processed {len(python_files)} files")


if __name__ == '__main__':
    main()
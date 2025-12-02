#!/usr/bin/env python3
"""
Fix mvp_site imports to use package-qualified format.

This script converts unqualified imports to package-qualified imports
to enable proper package installation.

Usage:
    python scripts/fix_mvp_site_imports.py --dry-run  # Preview changes
    python scripts/fix_mvp_site_imports.py            # Apply changes
"""

import argparse
import re
import shutil
from pathlib import Path

# Internal mvp_site modules that should be package-qualified
INTERNAL_MODULES = {
    "constants", "logging_util", "custom_types", "game_state",
    "firestore_service", "world_logic", "decorators", "llm_service",
    "document_generator", "entity_tracking", "entity_validator",
    "entity_preloader", "entity_instructions", "entity_utils",
    "json_utils", "prompt_utils", "token_utils", "world_loader",
    "memory_integration", "numeric_field_converter", "file_cache",
    "robust_json_parser", "structured_fields_utils",
    "narrative_response_schema", "narrative_sync_validator",
    "dual_pass_generator", "debug_hybrid_system",
    "gemini_request", "gemini_response", "serialization",
    "mcp_client", "memory_mcp_real", "mcp_memory_real"
}


def is_internal_module(module_name: str) -> bool:
    """Check if a module is an internal mvp_site module."""
    # Check if module is in our list or starts with known prefixes
    if module_name in INTERNAL_MODULES:
        return True
    # Check for module paths like "entity_tracking.something"
    base_module = module_name.split(".")[0]
    return base_module in INTERNAL_MODULES


def fix_import_line(line: str) -> tuple[str, bool]:
    """
    Fix a single import line if it needs conversion.
    Returns (fixed_line, was_changed)
    """
    # Skip already-fixed imports
    if "from mvp_site" in line or "import mvp_site" in line:
        return line, False

    # Pattern 1: import module_name
    match = re.match(r'^(\s*)import\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$', line)
    if match:
        indent, module = match.groups()
        if is_internal_module(module):
            return f"{indent}from mvp_site import {module}\n", True

    # Pattern 2: import module_name as alias
    match = re.match(r'^(\s*)import\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s+(\w+)\s*$', line)
    if match:
        indent, module, alias = match.groups()
        if is_internal_module(module):
            return f"{indent}from mvp_site import {module} as {alias}\n", True

    # Pattern 3: from module_name import ...
    match = re.match(r'^(\s*)from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import\s+(.+)$', line)
    if match:
        indent, module, imports = match.groups()
        base_module = module.split(".")[0]
        if is_internal_module(base_module):
            # Convert to mvp_site.module format
            return f"{indent}from mvp_site.{module} import {imports}\n", True

    return line, False


def fix_file_imports(file_path: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """
    Fix imports in a single file.
    Returns (num_changes, list_of_changes)
    """
    # Skip __init__.py files
    if file_path.name == "__init__.py":
        return 0, []

    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"ERROR reading {file_path}: {e}")
        return 0, []

    new_lines = []
    changes = []
    num_changes = 0

    for line_num, line in enumerate(lines, 1):
        new_line, was_changed = fix_import_line(line)
        new_lines.append(new_line)

        if was_changed:
            num_changes += 1
            changes.append(f"  Line {line_num}: {line.strip()} -> {new_line.strip()}")

    if num_changes > 0 and not dry_run:
        # Create backup
        backup_path = str(file_path) + ".backup"
        shutil.copy2(file_path, backup_path)

        # Write fixed content
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            print(f"✓ Fixed {file_path} ({num_changes} changes)")
        except Exception as e:
            print(f"ERROR writing {file_path}: {e}")
            # Restore backup
            shutil.copy2(backup_path, file_path)
            return 0, []

    return num_changes, changes


def main():
    parser = argparse.ArgumentParser(
        description="Fix mvp_site imports to use package-qualified format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    mvp_site_dir = project_root / "mvp_site"

    if not mvp_site_dir.exists():
        print(f"ERROR: mvp_site directory not found at {mvp_site_dir}")
        return 1

    print(f"Scanning {mvp_site_dir} for Python files...")
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified\n")

    # Find all Python files
    py_files = list(mvp_site_dir.rglob("*.py"))
    print(f"Found {len(py_files)} Python files\n")

    # Process each file
    total_changes = 0
    files_modified = 0

    for py_file in sorted(py_files):
        num_changes, changes = fix_file_imports(py_file, dry_run=args.dry_run)

        if num_changes > 0:
            files_modified += 1
            total_changes += num_changes

            rel_path = py_file.relative_to(project_root)
            if args.dry_run:
                print(f"\n{rel_path} - {num_changes} changes needed:")
                for change in changes:
                    print(change)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files scanned: {len(py_files)}")
    print(f"Files {'that would be ' if args.dry_run else ''}modified: {files_modified}")
    print(f"Total import changes {'needed' if args.dry_run else 'made'}: {total_changes}")

    if args.dry_run:
        print("\nRun without --dry-run to apply these changes")
    else:
        print("\n✓ Import fixes complete!")
        print("Backup files created with .backup extension")

    return 0


if __name__ == "__main__":
    exit(main())

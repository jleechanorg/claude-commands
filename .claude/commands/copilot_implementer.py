#!/usr/bin/env python3
"""
Copilot Implementer Module - Auto-fix engine for common code issues

This module implements actual fixes for auto-fixable suggestions from GitHub PR comments.
It focuses on:
1. Unused import detection and removal
2. Magic number detection and constant creation  
3. Simple refactoring operations
4. Code formatting improvements
"""

import ast
import os
import subprocess
import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ImplementationResult:
    """Result of implementing a fix"""
    success: bool
    file_path: str
    description: str
    changes_made: List[str]
    commit_hash: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class FixAttempt:
    """Represents an attempt to fix an issue"""
    issue_type: str
    file_path: str
    line_number: Optional[int]
    suggestion: str
    result: Optional[ImplementationResult] = None

class UnusedImportDetector:
    """Detects and removes unused imports from Python files"""
    
    def __init__(self):
        self.used_names = set()
        self.imported_names = {}  # name -> import_node
        self.star_imports = []
    
    def find_unused_imports(self, file_path: str) -> List[Tuple[int, str, str]]:
        """Find unused imports in a Python file
        
        Returns:
            List of (line_number, import_name, full_import_statement)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Reset state
            self.used_names = set()
            self.imported_names = {}
            self.star_imports = []
            
            # Find all imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports.append((node.lineno, name, f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")))
                        self.imported_names[name] = node
                elif isinstance(node, ast.ImportFrom):
                    if node.names[0].name == '*':
                        self.star_imports.append(node)
                    else:
                        for alias in node.names:
                            name = alias.asname if alias.asname else alias.name
                            imports.append((node.lineno, name, f"from {node.module} import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")))
                            self.imported_names[name] = node
            
            # Find all used names
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    self.used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    # Handle qualified names like os.path
                    if isinstance(node.value, ast.Name):
                        self.used_names.add(node.value.id)
            
            # Find unused imports
            unused = []
            for line_no, name, import_stmt in imports:
                if name not in self.used_names:
                    # Check if it's a module that might be used via qualified access
                    base_name = name.split('.')[0]
                    if base_name not in self.used_names:
                        unused.append((line_no, name, import_stmt))
            
            return unused
            
        except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return []
    
    def remove_unused_imports(self, file_path: str) -> ImplementationResult:
        """Remove unused imports from a file using AST-based modification"""
        try:
            unused_imports = self.find_unused_imports(file_path)
            
            if not unused_imports:
                return ImplementationResult(
                    success=True,
                    file_path=file_path,
                    description="No unused imports found",
                    changes_made=[]
                )
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Parse AST to get import nodes
            tree = ast.parse(content)
            unused_names = {name for _, name, _ in unused_imports}
            
            # Track lines to modify
            lines_to_remove = set()
            lines_to_modify = {}
            changes_made = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # Handle "import x, y, z" statements
                    used_aliases = []
                    removed_aliases = []
                    
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        if name in unused_names:
                            removed_aliases.append(alias.name + (f" as {alias.asname}" if alias.asname else ""))
                        else:
                            used_aliases.append(alias.name + (f" as {alias.asname}" if alias.asname else ""))
                    
                    if removed_aliases:
                        if used_aliases:
                            # Modify line to keep only used imports
                            new_import = f"import {', '.join(used_aliases)}"
                            lines_to_modify[node.lineno] = new_import
                            changes_made.append(f"Removed unused imports from line {node.lineno}: {', '.join(removed_aliases)}")
                        else:
                            # Remove entire line
                            lines_to_remove.add(node.lineno)
                            changes_made.append(f"Removed unused import line: import {', '.join(removed_aliases)}")
                
                elif isinstance(node, ast.ImportFrom):
                    # Handle "from module import x, y, z" statements  
                    used_aliases = []
                    removed_aliases = []
                    
                    for alias in node.names:
                        if alias.name == '*':
                            # Don't modify star imports
                            continue
                        name = alias.asname if alias.asname else alias.name
                        if name in unused_names:
                            removed_aliases.append(alias.name + (f" as {alias.asname}" if alias.asname else ""))
                        else:
                            used_aliases.append(alias.name + (f" as {alias.asname}" if alias.asname else ""))
                    
                    if removed_aliases:
                        if used_aliases:
                            # Modify line to keep only used imports
                            module = node.module or ""
                            new_import = f"from {module} import {', '.join(used_aliases)}"
                            lines_to_modify[node.lineno] = new_import
                            changes_made.append(f"Removed unused imports from line {node.lineno}: {', '.join(removed_aliases)}")
                        else:
                            # Remove entire line
                            lines_to_remove.add(node.lineno)
                            changes_made.append(f"Removed unused import line: from {node.module} import {', '.join(removed_aliases)}")
            
            # Apply modifications (in reverse order to maintain line numbers)
            for line_no in sorted(lines_to_remove, reverse=True):
                if 1 <= line_no <= len(lines):
                    lines.pop(line_no - 1)
            
            # Apply line modifications
            for line_no, new_content in lines_to_modify.items():
                if 1 <= line_no <= len(lines) and line_no not in lines_to_remove:
                    # Preserve indentation
                    original_line = lines[line_no - 1]
                    leading_whitespace = len(original_line) - len(original_line.lstrip())
                    lines[line_no - 1] = ' ' * leading_whitespace + new_content
            
            # Write back the modified content
            modified_content = '\n'.join(lines)
            if content.endswith('\n'):
                modified_content += '\n'
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            return ImplementationResult(
                success=True,
                file_path=file_path,
                description=f"Safely removed unused imports from {len(set(line for line, _, _ in unused_imports))} lines",
                changes_made=changes_made
            )
            
        except Exception as e:
            logger.error(f"Error removing unused imports from {file_path}: {e}")
            return ImplementationResult(
                success=False,
                file_path=file_path,
                description="Failed to remove unused imports",
                changes_made=[],
                error_message=str(e)
            )

class MagicNumberDetector:
    """Detects and replaces magic numbers with constants"""
    
    def __init__(self):
        # Numbers to ignore (common values that don't need constants)
        self.ignore_numbers = {0, 1, -1, 2, 10, 100, 1000}
    
    def find_magic_numbers(self, file_path: str) -> List[Tuple[int, int, str]]:
        """Find magic numbers in a Python file
        
        Returns:
            List of (line_number, number_value, context)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            magic_numbers = []
            
            # Track number occurrences
            number_counts = {}
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                    if node.value not in self.ignore_numbers:
                        number_counts[node.value] = number_counts.get(node.value, 0) + 1
            
            # Find numbers that appear multiple times
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                    if (node.value not in self.ignore_numbers and 
                        number_counts.get(node.value, 0) > 1):
                        magic_numbers.append((node.lineno, node.value, f"Magic number: {node.value}"))
            
            return magic_numbers
            
        except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return []
    
    def create_constants(self, file_path: str) -> ImplementationResult:
        """Create constants for magic numbers and replace them in the code"""
        try:
            magic_numbers = self.find_magic_numbers(file_path)
            
            if not magic_numbers:
                return ImplementationResult(
                    success=True,
                    file_path=file_path,
                    description="No magic numbers found",
                    changes_made=[]
                )
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Parse AST to find and replace magic numbers
            tree = ast.parse(content)
            
            # Group magic numbers by value and create constant names
            value_to_const = {}
            constants_to_add = []
            changes_made = []
            
            # Create unique constant names for each magic number value
            for line_no, value, context in magic_numbers:
                if value not in value_to_const:
                    # Create meaningful constant name based on value
                    if isinstance(value, int):
                        const_name = f"CONSTANT_{abs(value)}"
                        if value < 0:
                            const_name = f"NEGATIVE_{const_name}"
                    else:
                        # Handle float values
                        cleaned_value = str(value).replace('.', '_').replace('-', 'NEGATIVE_')
                        const_name = f"CONSTANT_{cleaned_value}"
                    
                    value_to_const[value] = const_name
                    constants_to_add.append(f"{const_name} = {value}")
                    changes_made.append(f"Created constant: {const_name} = {value}")
            
            # Track which lines need modification
            lines_modified = set()
            
            # Walk AST and replace magic numbers
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                    if (node.value not in self.ignore_numbers and 
                        node.value in value_to_const):
                        line_no = node.lineno
                        if 1 <= line_no <= len(lines):
                            original_line = lines[line_no - 1]
                            
                            # Replace the numeric value with constant name
                            # This is a simple approach - find the number in the line and replace it
                            value_str = str(node.value)
                            const_name = value_to_const[node.value]
                            
                            # Be careful with replacement to avoid partial matches
                            # Use word boundaries for integer values
                            if isinstance(node.value, int):
                                pattern = r'\b' + re.escape(value_str) + r'\b'
                            else:
                                # For floats, be more precise
                                pattern = re.escape(value_str)
                            
                            if re.search(pattern, original_line):
                                new_line = re.sub(pattern, const_name, original_line, count=1)
                                if new_line != original_line:
                                    lines[line_no - 1] = new_line
                                    lines_modified.add(line_no)
                                    changes_made.append(f"Replaced {value_str} with {const_name} on line {line_no}")
            
            # Find position to insert constants (after imports, before first function/class)
            insert_pos = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if (stripped and 
                    not stripped.startswith('#') and 
                    not stripped.startswith('import') and 
                    not stripped.startswith('from') and
                    not stripped.startswith('"""') and
                    not stripped.startswith("'''")):
                    insert_pos = i
                    break
            
            # Insert constants at the top
            if constants_to_add:
                # Add a blank line before constants if needed
                if insert_pos > 0 and lines[insert_pos - 1].strip():
                    constants_to_add.insert(0, "")
                
                # Add constants
                for const in reversed(constants_to_add):
                    lines.insert(insert_pos, const)
                
                # Add blank line after constants
                lines.insert(insert_pos + len(constants_to_add), "")
            
            # Write back modified content
            modified_content = '\n'.join(lines)
            if content.endswith('\n'):
                modified_content += '\n'
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            return ImplementationResult(
                success=True,
                file_path=file_path,
                description=f"Created {len(constants_to_add)} constants and replaced {len(lines_modified)} magic numbers",
                changes_made=changes_made
            )
            
        except Exception as e:
            logger.error(f"Error creating constants in {file_path}: {e}")
            return ImplementationResult(
                success=False,
                file_path=file_path,
                description="Failed to create constants",
                changes_made=[],
                error_message=str(e)
            )

class CodeFormatter:
    """Handles code formatting improvements"""
    
    def format_with_black(self, file_path: str) -> ImplementationResult:
        """Format code using black"""
        try:
            # Check if black is available
            result = subprocess.run(['black', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return ImplementationResult(
                    success=False,
                    file_path=file_path,
                    description="Black formatter not available",
                    changes_made=[],
                    error_message="Black not installed"
                )
            
            # Run black on the file
            result = subprocess.run(['black', file_path], capture_output=True, text=True)
            
            if result.returncode == 0:
                return ImplementationResult(
                    success=True,
                    file_path=file_path,
                    description="Code formatted with black",
                    changes_made=["Applied black formatting"]
                )
            else:
                return ImplementationResult(
                    success=False,
                    file_path=file_path,
                    description="Black formatting failed",
                    changes_made=[],
                    error_message=result.stderr
                )
                
        except Exception as e:
            logger.error(f"Error formatting {file_path}: {e}")
            return ImplementationResult(
                success=False,
                file_path=file_path,
                description="Failed to format code",
                changes_made=[],
                error_message=str(e)
            )
    
    def sort_imports(self, file_path: str) -> ImplementationResult:
        """Sort imports using isort"""
        try:
            # Check if isort is available
            result = subprocess.run(['isort', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return ImplementationResult(
                    success=False,
                    file_path=file_path,
                    description="isort not available",
                    changes_made=[],
                    error_message="isort not installed"
                )
            
            # Run isort on the file
            result = subprocess.run(['isort', file_path], capture_output=True, text=True)
            
            if result.returncode == 0:
                return ImplementationResult(
                    success=True,
                    file_path=file_path,
                    description="Imports sorted with isort",
                    changes_made=["Sorted imports"]
                )
            else:
                return ImplementationResult(
                    success=False,
                    file_path=file_path,
                    description="Import sorting failed",
                    changes_made=[],
                    error_message=result.stderr
                )
                
        except Exception as e:
            logger.error(f"Error sorting imports in {file_path}: {e}")
            return ImplementationResult(
                success=False,
                file_path=file_path,
                description="Failed to sort imports",
                changes_made=[],
                error_message=str(e)
            )

class CopilotImplementer:
    """Main implementer class for auto-fixes"""
    
    def __init__(self, enable_safety_checks: bool = True):
        self.unused_import_detector = UnusedImportDetector()
        self.magic_number_detector = MagicNumberDetector()
        self.code_formatter = CodeFormatter()
        self.enable_safety_checks = enable_safety_checks
        
        # Import safety checker if enabled
        if self.enable_safety_checks:
            try:
                from copilot_safety import SafetyChecker
                self.safety_checker = SafetyChecker()
            except ImportError:
                logger.warning("Safety checker not available - proceeding without safety checks")
                self.enable_safety_checks = False
    
    def implement_suggestion(self, suggestion_type: str, file_path: str, line_number: Optional[int] = None) -> ImplementationResult:
        """Implement a specific suggestion type with safety checks"""
        try:
            # Run safety checks if enabled
            if self.enable_safety_checks:
                safety_result = self.safety_checker.check_operation_safety(
                    suggestion_type, 
                    file_path,
                    context={'line_number': line_number}
                )
                
                if not safety_result.safe:
                    logger.warning(f"Safety check failed for {suggestion_type} on {file_path}")
                    return ImplementationResult(
                        success=False,
                        file_path=file_path,
                        description=f"Safety check failed: {', '.join(safety_result.issues)}",
                        changes_made=[],
                        error_message=f"Blocked operations: {', '.join(safety_result.blocked_operations)}"
                    )
                
                if safety_result.risk_level in ["high", "critical"]:
                    logger.warning(f"High risk operation {suggestion_type} on {file_path}: {safety_result.issues}")
                    # For now, proceed but log warning. In production, might want to require approval
            
            # Proceed with implementation
            if suggestion_type == "auto_fix_unused_imports":
                return self.unused_import_detector.remove_unused_imports(file_path)
            elif suggestion_type == "auto_fix_magic_numbers":
                return self.magic_number_detector.create_constants(file_path)
            elif suggestion_type == "auto_fix_formatting":
                # Try black first, then isort
                result = self.code_formatter.format_with_black(file_path)
                if result.success:
                    sort_result = self.code_formatter.sort_imports(file_path)
                    if sort_result.success:
                        result.changes_made.extend(sort_result.changes_made)
                return result
            else:
                return ImplementationResult(
                    success=False,
                    file_path=file_path,
                    description=f"Unknown suggestion type: {suggestion_type}",
                    changes_made=[],
                    error_message=f"No implementation for {suggestion_type}"
                )
                
        except Exception as e:
            logger.error(f"Error implementing {suggestion_type} in {file_path}: {e}")
            return ImplementationResult(
                success=False,
                file_path=file_path,
                description=f"Failed to implement {suggestion_type}",
                changes_made=[],
                error_message=str(e)
            )
    
    def commit_changes(self, results: List[ImplementationResult], commit_message: str) -> Optional[str]:
        """Commit the changes and return commit hash"""
        try:
            # Check if there are any changes to commit
            successful_results = [r for r in results if r.success and r.changes_made]
            if not successful_results:
                logger.info("No changes to commit")
                return None
            
            # Stage files with changes
            files_to_add = list(set(r.file_path for r in successful_results))
            for file_path in files_to_add:
                subprocess.run(['git', 'add', file_path], check=True)
            
            # Commit changes
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get commit hash
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            
            commit_hash = result.stdout.strip()
            logger.info(f"Changes committed: {commit_hash}")
            return commit_hash
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error committing changes: {e}")
            return None
    
    def get_project_python_files(self) -> List[str]:
        """Get all Python files in the project"""
        python_files = []
        
        # Get project root
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            )
            project_root = result.stdout.strip()
        except subprocess.CalledProcessError:
            project_root = os.getcwd()
        
        # Find Python files
        for root, dirs, files in os.walk(project_root):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        return python_files

def main():
    """Main function for standalone testing"""
    import sys
    
    implementer = CopilotImplementer()
    
    if len(sys.argv) < 2:
        print("Usage: python copilot_implementer.py <suggestion_type> [file_path]")
        print("Suggestion types: auto_fix_unused_imports, auto_fix_magic_numbers, auto_fix_formatting")
        sys.exit(1)
    
    suggestion_type = sys.argv[1]
    
    if len(sys.argv) > 2:
        file_path = sys.argv[2]
        files = [file_path]
    else:
        # Process all Python files in project
        files = implementer.get_project_python_files()
    
    results = []
    for file_path in files:
        print(f"Processing {file_path}...")
        result = implementer.implement_suggestion(suggestion_type, file_path)
        results.append(result)
        
        if result.success:
            print(f"  ✅ {result.description}")
            for change in result.changes_made:
                print(f"    - {change}")
        else:
            print(f"  ❌ {result.description}")
            if result.error_message:
                print(f"    Error: {result.error_message}")
    
    # Commit changes
    successful_count = sum(1 for r in results if r.success and r.changes_made)
    if successful_count > 0:
        commit_message = f"Auto-fix: {suggestion_type} applied to {successful_count} files"
        commit_hash = implementer.commit_changes(results, commit_message)
        if commit_hash:
            print(f"\n✅ Changes committed: {commit_hash}")
    else:
        print("\n No changes to commit")

if __name__ == "__main__":
    main()
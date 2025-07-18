#!/usr/bin/env python3
"""
Copilot Safety Module - Safety checks and validation for auto-implemented changes

This module provides safety checks to prevent dangerous operations and validate
changes before they are applied.
"""

import os
import subprocess
import logging
import ast
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SafetyResult:
    """Result of safety check"""
    safe: bool
    risk_level: str  # "low", "medium", "high", "critical"
    issues: List[str]
    recommendations: List[str]
    blocked_operations: List[str] = None
    
    def __post_init__(self):
        if self.blocked_operations is None:
            self.blocked_operations = []

class SafetyChecker:
    """Safety checker for copilot operations"""
    
    # Critical files that should never be auto-modified
    PROTECTED_FILES = {
        'main.py',
        'app.py', 
        '__init__.py',
        'settings.py',
        'config.py',
        'requirements.txt',
        'setup.py',
        'Dockerfile',
        'docker-compose.yml',
        '.gitignore',
        'README.md'
    }
    
    # Dangerous patterns that should trigger warnings
    DANGEROUS_PATTERNS = {
        r'rm\s+-rf': "Dangerous file deletion command",
        r'DROP\s+TABLE': "SQL DROP TABLE command",
        r'DELETE\s+FROM': "SQL DELETE command",  
        r'exec\s*\(': "Dynamic code execution",
        r'eval\s*\(': "Dynamic code evaluation",
        r'subprocess\.call': "Subprocess execution",
        r'os\.system': "System command execution",
        r'import\s+subprocess': "Subprocess import",
        r'__import__': "Dynamic import",
        r'open\s*\([^)]*[\'"]w[\'"]': "File write operation"
    }
    
    # Import patterns that require extra validation
    RISKY_IMPORTS = {
        'subprocess',
        'os.system', 
        'exec',
        'eval',
        'pickle',
        'shelve',
        'tempfile',
        'shutil'
    }
    
    def __init__(self):
        self.project_root = self._get_project_root()
    
    def _get_project_root(self) -> str:
        """Get the project root directory"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return os.getcwd()
    
    def check_file_safety(self, file_path: str) -> SafetyResult:
        """Check if a file is safe to modify"""
        issues = []
        recommendations = []
        blocked_operations = []
        risk_level = "low"
        
        # Check if file is protected
        filename = os.path.basename(file_path)
        if filename in self.PROTECTED_FILES:
            issues.append(f"Protected file: {filename}")
            recommendations.append(f"Avoid auto-modifying {filename} - requires manual review")
            blocked_operations.append("auto_modification")
            risk_level = "high"
        
        # Check file extension
        if not file_path.endswith('.py'):
            issues.append(f"Non-Python file: {file_path}")
            recommendations.append("Only auto-modify Python files")
            blocked_operations.append("non_python_file")
            risk_level = "medium"
        
        # Check if file exists and is readable
        if not os.path.exists(file_path):
            issues.append(f"File does not exist: {file_path}")
            return SafetyResult(
                safe=False,
                risk_level="medium",
                issues=issues,
                recommendations=["Create file first or check path"],
                blocked_operations=["all"]
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            issues.append(f"Cannot read file: {e}")
            return SafetyResult(
                safe=False,
                risk_level="medium", 
                issues=issues,
                recommendations=["Check file permissions"],
                blocked_operations=["all"]
            )
        
        # Check for dangerous patterns in content
        dangerous_found = self._check_dangerous_patterns(content)
        if dangerous_found:
            issues.extend(dangerous_found)
            recommendations.append("Manual review required for files with dangerous patterns")
            risk_level = "high"
        
        # Check for risky imports
        risky_imports = self._check_risky_imports(content)
        if risky_imports:
            issues.extend([f"Risky import: {imp}" for imp in risky_imports])
            recommendations.append("Exercise caution with files containing risky imports")
            if risk_level == "low":
                risk_level = "medium"
        
        # Determine if safe
        safe = risk_level in ["low", "medium"] and not blocked_operations
        
        return SafetyResult(
            safe=safe,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            blocked_operations=blocked_operations
        )
    
    def _check_dangerous_patterns(self, content: str) -> List[str]:
        """Check for dangerous patterns in file content"""
        issues = []
        for pattern, description in self.DANGEROUS_PATTERNS.items():
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Dangerous pattern found: {description}")
        return issues
    
    def _check_risky_imports(self, content: str) -> List[str]:
        """Check for risky imports in Python content"""
        risky_found = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.RISKY_IMPORTS:
                            risky_found.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module in self.RISKY_IMPORTS:
                        risky_found.append(node.module)
        except SyntaxError:
            # If we can't parse, that's already a different issue
            pass
        return list(set(risky_found))  # Remove duplicates
    
    def check_change_safety(self, file_path: str, old_content: str, new_content: str) -> SafetyResult:
        """Check if a proposed change is safe"""
        issues = []
        recommendations = []
        blocked_operations = []
        risk_level = "low"
        
        # First check file safety
        file_safety = self.check_file_safety(file_path)
        if not file_safety.safe:
            return file_safety
        
        # Check size of change
        old_lines = old_content.count('\n')
        new_lines = new_content.count('\n') 
        line_diff = abs(new_lines - old_lines)
        
        if line_diff > 50:
            issues.append(f"Large change: {line_diff} line difference")
            recommendations.append("Large changes should be reviewed manually")
            risk_level = "medium"
        
        # Check for addition of dangerous patterns
        old_dangerous = self._check_dangerous_patterns(old_content)
        new_dangerous = self._check_dangerous_patterns(new_content)
        
        added_dangerous = set(new_dangerous) - set(old_dangerous)
        if added_dangerous:
            issues.extend([f"Added dangerous pattern: {p}" for p in added_dangerous])
            blocked_operations.append("add_dangerous_patterns")
            risk_level = "critical"
        
        # Check for addition of risky imports
        old_risky = set(self._check_risky_imports(old_content))
        new_risky = set(self._check_risky_imports(new_content))
        
        added_risky = new_risky - old_risky
        if added_risky:
            issues.extend([f"Added risky import: {imp}" for imp in added_risky])
            recommendations.append("Review risky imports manually")
            if risk_level == "low":
                risk_level = "medium"
        
        # Check syntax validity
        try:
            ast.parse(new_content, filename=file_path)
        except SyntaxError as e:
            issues.append(f"Syntax error in new content: {e}")
            blocked_operations.append("syntax_error")
            risk_level = "high"
        
        # Determine if safe
        safe = risk_level in ["low", "medium"] and not blocked_operations
        
        return SafetyResult(
            safe=safe,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            blocked_operations=blocked_operations
        )
    
    def check_operation_safety(self, operation_type: str, target: str, context: Dict[str, Any] = None) -> SafetyResult:
        """Check if a specific operation is safe to perform"""
        issues = []
        recommendations = []
        blocked_operations = []
        risk_level = "low"
        context = context or {}
        
        if operation_type == "remove_unused_imports":
            # Generally safe operation
            if target in self.PROTECTED_FILES:
                risk_level = "medium"
                recommendations.append("Protected file - proceed with caution")
        
        elif operation_type == "create_constants":
            # Safe operation, but check file
            file_safety = self.check_file_safety(target)
            if not file_safety.safe:
                return file_safety
        
        elif operation_type == "format_code":
            # Generally safe
            if target in self.PROTECTED_FILES:
                risk_level = "medium"
                recommendations.append("Protected file - formatting changes need review")
        
        elif operation_type == "refactor":
            # Potentially risky
            risk_level = "medium"
            recommendations.append("Refactoring requires careful testing")
            
            if target in self.PROTECTED_FILES:
                risk_level = "high"
                recommendations.append("Avoid auto-refactoring protected files")
        
        else:
            # Unknown operation
            issues.append(f"Unknown operation type: {operation_type}")
            risk_level = "medium"
            recommendations.append("Unknown operations require manual review")
        
        # Check if we're in a critical directory
        if any(critical in target for critical in ['/etc/', '/usr/', '/root/', '/home/']):
            if not target.startswith(self.project_root):
                issues.append("Operation outside project directory")
                blocked_operations.append("external_directory")
                risk_level = "critical"
        
        safe = risk_level in ["low", "medium"] and not blocked_operations
        
        return SafetyResult(
            safe=safe,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            blocked_operations=blocked_operations
        )
    
    def validate_batch_operations(self, operations: List[Dict[str, Any]]) -> SafetyResult:
        """Validate a batch of operations for safety"""
        all_issues = []
        all_recommendations = []
        all_blocked = []
        max_risk = "low"
        
        risk_levels = ["low", "medium", "high", "critical"]
        
        for i, operation in enumerate(operations):
            op_type = operation.get('type', 'unknown')
            target = operation.get('target', '')
            context = operation.get('context', {})
            
            # For batch operations, don't check file existence (files might be created during batch)
            # Only check operation-level safety
            result = self.check_operation_safety(op_type, target, context)
            
            # Only include non-file-existence issues for batch validation
            filtered_issues = [issue for issue in result.issues 
                             if not ("File does not exist" in issue or "Cannot read file" in issue)]
            
            if filtered_issues:
                all_issues.extend([f"Op {i+1}: {issue}" for issue in filtered_issues])
            
            if result.recommendations:
                all_recommendations.extend([f"Op {i+1}: {rec}" for rec in result.recommendations])
            
            # Only include non-file-existence blocked operations
            filtered_blocked = [blocked for blocked in result.blocked_operations 
                              if blocked not in ["all"]]
            if filtered_blocked:
                all_blocked.extend([f"Op {i+1}: {blocked}" for blocked in filtered_blocked])
            
            # Track highest risk level (but adjust for file existence issues)
            adjusted_risk = result.risk_level
            if result.issues and all("File does not exist" in issue or "Cannot read file" in issue 
                                   for issue in result.issues):
                # If only file existence issues, reduce risk level for batch
                adjusted_risk = "low" if result.risk_level == "medium" else result.risk_level
            
            if risk_levels.index(adjusted_risk) > risk_levels.index(max_risk):
                max_risk = adjusted_risk
        
        # Additional batch-level checks
        if len(operations) > 10:
            all_issues.append(f"Large batch: {len(operations)} operations")
            all_recommendations.append("Large batches should be split and reviewed")
            if max_risk == "low":
                max_risk = "medium"
        
        # Check for conflicting operations
        file_targets = [op.get('target') for op in operations if op.get('target')]
        if len(file_targets) != len(set(file_targets)):
            all_issues.append("Multiple operations on same files")
            all_recommendations.append("Review operations on same files for conflicts")
            if max_risk == "low":
                max_risk = "medium"
        
        safe = max_risk in ["low", "medium"] and not all_blocked
        
        return SafetyResult(
            safe=safe,
            risk_level=max_risk,
            issues=all_issues,
            recommendations=all_recommendations,
            blocked_operations=all_blocked
        )

def main():
    """Main function for standalone testing"""
    import sys
    
    checker = SafetyChecker()
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = checker.check_file_safety(file_path)
        
        print(f"Safety check for {file_path}:")
        print(f"Safe: {'✓' if result.safe else '✗'}")
        print(f"Risk level: {result.risk_level}")
        
        if result.issues:
            print("\nIssues:")
            for issue in result.issues:
                print(f"  - {issue}")
        
        if result.recommendations:
            print("\nRecommendations:")
            for rec in result.recommendations:
                print(f"  - {rec}")
        
        if result.blocked_operations:
            print("\nBlocked operations:")
            for blocked in result.blocked_operations:
                print(f"  - {blocked}")
    else:
        print("Usage: python copilot_safety.py <file_path>")

if __name__ == "__main__":
    main()
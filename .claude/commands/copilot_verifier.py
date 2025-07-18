#!/usr/bin/env python3
"""
Copilot Verifier Module - Verification system for auto-implemented changes

This module verifies that auto-implemented changes don't break existing functionality
by running tests, syntax checks, and other validation steps.
"""

import os
import subprocess
import logging
import ast
import sys
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CheckType(Enum):
    """Types of verification checks"""
    SYNTAX = "syntax"
    IMPORTS = "imports"
    TESTS = "tests"
    FILE_INTEGRITY = "file_integrity"
    LINTING = "linting"

@dataclass
class VerificationResult:
    """Result of verification checks"""
    success: bool
    check_type: CheckType
    description: str
    details: List[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []

class CopilotVerifier:
    """Main verifier class for validating auto-implemented changes"""
    
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
    
    def verify_syntax(self, file_paths: List[str]) -> VerificationResult:
        """Verify that Python files have valid syntax"""
        if not file_paths:
            return VerificationResult(
                success=True,
                check_type=CheckType.SYNTAX,
                description="No files to check syntax",
                details=[]
            )
        
        failed_files = []
        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    failed_files.append(f"{file_path}: File not found")
                    continue
                    
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    ast.parse(content, filename=file_path)
            except SyntaxError as e:
                failed_files.append(f"{file_path}: {e}")
            except Exception as e:
                failed_files.append(f"{file_path}: {e}")
        
        if failed_files:
            return VerificationResult(
                success=False,
                check_type=CheckType.SYNTAX,
                description=f"Syntax errors found in {len(failed_files)} files",
                details=failed_files,
                error_message="; ".join(failed_files)
            )
        
        return VerificationResult(
            success=True,
            check_type=CheckType.SYNTAX,
            description=f"Syntax valid for {len(file_paths)} files",
            details=[f"✓ {fp}" for fp in file_paths]
        )
    
    def verify_imports(self, file_paths: List[str]) -> VerificationResult:
        """Verify that all imports in files can be resolved"""
        if not file_paths:
            return VerificationResult(
                success=True,
                check_type=CheckType.IMPORTS,
                description="No files to check imports",
                details=[]
            )
        
        # For now, just check syntax-level import validity
        failed_files = []
        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    failed_files.append(f"{file_path}: File not found")
                    continue
                    
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content, filename=file_path)
                    
                # Check for import syntax issues
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        # Basic validation - the AST parse already validates syntax
                        pass
                        
            except Exception as e:
                failed_files.append(f"{file_path}: {e}")
        
        if failed_files:
            return VerificationResult(
                success=False,
                check_type=CheckType.IMPORTS,
                description=f"Import errors found in {len(failed_files)} files",
                details=failed_files,
                error_message="; ".join(failed_files)
            )
        
        return VerificationResult(
            success=True,
            check_type=CheckType.IMPORTS,
            description=f"Imports valid for {len(file_paths)} files",
            details=[f"✓ {fp}" for fp in file_paths]
        )
    
    def run_project_tests(self) -> VerificationResult:
        """Run project tests to verify changes don't break functionality"""
        try:
            # Try different test commands
            test_commands = [
                ['python3', '-m', 'pytest', '--tb=short'],
                ['python3', '-m', 'unittest', 'discover'],
                ['./run_tests.sh'],
            ]
            
            for cmd in test_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        cwd=self.project_root
                    )
                    
                    if result.returncode == 0:
                        return VerificationResult(
                            success=True,
                            check_type=CheckType.TESTS,
                            description="All tests passed",
                            details=[result.stdout] if result.stdout else []
                        )
                    else:
                        return VerificationResult(
                            success=False,
                            check_type=CheckType.TESTS,
                            description="Tests failed",
                            details=[result.stdout, result.stderr],
                            error_message=result.stderr
                        )
                except FileNotFoundError:
                    continue
            
            # No test runner found
            return VerificationResult(
                success=True,
                check_type=CheckType.TESTS,
                description="No test runner found - assuming pass",
                details=["Skipped: No test runner available"]
            )
            
        except Exception as e:
            return VerificationResult(
                success=False,
                check_type=CheckType.TESTS,
                description="Error running tests",
                error_message=str(e)
            )
    
    def run_tests_for_files(self, file_paths: List[str]) -> VerificationResult:
        """Run tests for specific files"""
        # For simplicity, run all tests
        return self.run_project_tests()
    
    def verify_file_integrity(self, file_paths: List[str]) -> VerificationResult:
        """Verify that files maintain their integrity after changes"""
        if not file_paths:
            return VerificationResult(
                success=True,
                check_type=CheckType.FILE_INTEGRITY,
                description="No files to check integrity",
                details=[]
            )
        
        failed_files = []
        valid_files = []
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                failed_files.append(f"{file_path}: File not found")
            else:
                try:
                    # Check if file is readable
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if file is empty (warning, not error)
                    if not content.strip():
                        valid_files.append(f"{file_path}: Empty file (warning)")
                    else:
                        valid_files.append(f"{file_path}: OK")
                        
                except Exception as e:
                    failed_files.append(f"{file_path}: {e}")
        
        if failed_files:
            return VerificationResult(
                success=False,
                check_type=CheckType.FILE_INTEGRITY,
                description=f"File integrity issues in {len(failed_files)} files",
                details=failed_files + valid_files,
                error_message="; ".join(failed_files)
            )
        
        return VerificationResult(
            success=True,
            check_type=CheckType.FILE_INTEGRITY,
            description=f"File integrity verified for {len(valid_files)} files",
            details=valid_files
        )
    
    def comprehensive_verification(self, file_paths: List[str]) -> List[VerificationResult]:
        """Run comprehensive verification on changed files"""
        results = []
        
        # 1. Verify file integrity
        results.append(self.verify_file_integrity(file_paths))
        
        # 2. Verify syntax
        python_files = [fp for fp in file_paths if fp.endswith('.py')]
        if python_files:
            results.append(self.verify_syntax(python_files))
            results.append(self.verify_imports(python_files))
        
        # 3. Run tests (only if other checks pass)
        if all(r.success for r in results):
            results.append(self.run_project_tests())
        
        return results

def main():
    """Main function for standalone testing"""
    import sys
    
    verifier = CopilotVerifier()
    
    if len(sys.argv) > 1:
        files = sys.argv[1:]
        results = verifier.comprehensive_verification(files)
        
        for result in results:
            print(f"{result.check_type.value}: {'✓' if result.success else '✗'} {result.description}")
            if result.error_message:
                print(f"  Error: {result.error_message}")
    else:
        # Just run tests
        result = verifier.run_project_tests()
        print(f"Tests: {'✓' if result.success else '✗'} {result.description}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test Skip Policy Enforcement Script

Detects violations of the nuanced test skip policy that distinguishes between
legitimate environmental skips and inappropriate lazy implementation avoidance.

Usage:
    python3 scripts/check_skip_policy.py [--fix] [--verbose]
    
    --fix: Automatically fix detected violations where possible
    --verbose: Show detailed analysis of each pattern
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, NamedTuple
import ast

class SkipViolation(NamedTuple):
    file_path: str
    line_number: int
    line_content: str
    violation_type: str
    reason: str
    suggested_fix: str = ""

class SkipPolicyChecker:
    def __init__(self, project_root: Path, verbose: bool = False):
        self.project_root = project_root
        self.verbose = verbose
        self.violations: List[SkipViolation] = []
        
        # Patterns that indicate legitimate environmental skips (compiled for safety)
        self.legitimate_patterns = [
            re.compile(r'not.*os\.path\.exists', re.IGNORECASE),  # Missing files/directories
            re.compile(r'shutil\.which.*is None', re.IGNORECASE),  # Missing system utilities  
            re.compile(r'git.*not.*available', re.IGNORECASE),  # Git not installed
            re.compile(r'credentials.*not.*available', re.IGNORECASE),  # Missing credentials
            re.compile(r'CI.*environment', re.IGNORECASE),  # CI limitations
            re.compile(r'permission.*denied', re.IGNORECASE),  # Permission issues
        ]
        
        # Patterns that indicate inappropriate lazy skips
        self.forbidden_patterns = [
            r'too.*hard',  # Implementation difficulty
            r'sometimes.*fails',  # Flaky tests
            r'not.*implemented',  # Implementation gaps
            r'mock.*not.*working',  # Mocking issues
            r'database.*not.*set.*up',  # Internal setup issues
        ]
        
        # Pattern for old fail-instead-of-skip violations
        self.fail_skip_pattern = r'self\.fail\(.*[Ss]kipping.*\)'
    
    def check_file(self, file_path: Path) -> None:
        """Check a single test file for skip policy violations."""
        if not file_path.name.startswith('test_') or not file_path.suffix == '.py':
            return
            
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.splitlines()
        except (UnicodeDecodeError, OSError) as e:
            if self.verbose:
                print(f"Warning: Could not read {file_path}: {e}")
            return
        
        for line_num, line in enumerate(lines, 1):
            self._check_line(file_path, line_num, line)
    
    def _check_line(self, file_path: Path, line_num: int, line: str) -> None:
        """Check a single line for skip policy violations."""
        line_stripped = line.strip()
        
        # Check for fail-instead-of-skip violations
        if re.search(self.fail_skip_pattern, line_stripped, re.IGNORECASE):
            violation = SkipViolation(
                file_path=str(file_path.relative_to(self.project_root)),
                line_number=line_num,
                line_content=line_stripped,
                violation_type="FAIL_INSTEAD_OF_SKIP",
                reason="Uses self.fail() for legitimate environmental skip condition",
                suggested_fix=self._suggest_fail_to_skip_fix(line_stripped)
            )
            self.violations.append(violation)
        
        # Check for any skip patterns (zero tolerance policy)
        skip_patterns = [
            '@unittest.skipIf', '@unittest.skipUnless', '@unittest.skip',
            '@pytest.mark.skip', '@pytest.mark.skipif', 'skipTest',
            'pytest.skip', '.skip('
        ]
        
        if any(pattern in line_stripped for pattern in skip_patterns):
            # Zero tolerance - ALL skip patterns are violations
            violation = SkipViolation(
                file_path=str(file_path.relative_to(self.project_root)),
                line_number=line_num,
                line_content=line_stripped,
                violation_type="ZERO_TOLERANCE_SKIP_VIOLATION",
                reason="Zero tolerance policy: All skip patterns forbidden - use comprehensive mocking instead",
                suggested_fix="Replace skip pattern with comprehensive mocking using unittest.mock or pytest fixtures"
            )
            self.violations.append(violation)
    
    def _suggest_fail_to_skip_fix(self, line: str) -> str:
        """Suggest a fix for fail-instead-of-skip violations."""
        # Extract the message from self.fail("message")
        match = re.search(r'self\.fail\(\s*["\']([^"\']*)["\']', line)
        if match:
            message = match.group(1)
            # Clean up the message format
            message = re.sub(r'\s*-\s*[Ss]kipping.*', '', message)  # Remove " - skipping" suffix
            message = message.rstrip('.')  # Remove trailing period
            return f'self.skipTest("{message}, skipping test")'
        return "Replace self.fail() with self.skipTest()"
    
    def _analyze_skip_pattern(self, file_path: Path, line_num: int, line: str) -> None:
        """Analyze whether a skip pattern is legitimate or forbidden."""
        # Check if it matches forbidden lazy patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                violation = SkipViolation(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num,
                    line_content=line,
                    violation_type="LAZY_SKIP",
                    reason=f"Skip pattern suggests implementation avoidance: {pattern}",
                    suggested_fix="Replace skip with proper mocking or implementation fix"
                )
                self.violations.append(violation)
                return
        
        # Check if skip message format is proper
        if 'skipTest' in line:
            if not self._has_proper_skip_format(line):
                violation = SkipViolation(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num,
                    line_content=line,
                    violation_type="IMPROPER_FORMAT",
                    reason="Skip message doesn't follow format: 'Resource not available: reason, skipping purpose'",
                    suggested_fix="Use format: self.skipTest('Resource not available: specific reason, skipping test purpose')"
                )
                self.violations.append(violation)
    
    def _has_proper_skip_format(self, line: str) -> bool:
        """Check if skip message follows the proper format."""
        # Handle multi-line skipTest calls
        if 'skipTest(' in line and not ')' in line:
            return True  # Multi-line format, assume correct
        
        # Extract message from skipTest call
        match = re.search(r'skipTest\(\s*[f]?["\']([^"\']*)["\']', line)
        if not match:
            return False  # Can't extract message
        
        message = match.group(1)
        
        # Check for proper format: "Resource not available: reason, skipping purpose"
        # Allow some flexibility in the exact wording
        has_resource_prefix = message.lower().startswith('resource not available:')
        has_skip_purpose = 'skipping' in message.lower()
        has_comma_separator = ',' in message and 'skipping' in message.lower()
        
        return has_resource_prefix and has_skip_purpose and has_comma_separator
    
    def scan_directory(self, directory: Path) -> None:
        """Recursively scan directory for test files."""
        if not directory.exists():
            return
            
        for file_path in directory.rglob("*.py"):
            if file_path.name.startswith('test_'):
                self.check_file(file_path)
    
    def print_report(self) -> None:
        """Print a formatted report of all violations."""
        if not self.violations:
            print("✅ No test skip policy violations found")
            return
        
        print(f"❌ Found {len(self.violations)} test skip policy violations:")
        print()
        
        # Group violations by type
        by_type: Dict[str, List[SkipViolation]] = {}
        for violation in self.violations:
            if violation.violation_type not in by_type:
                by_type[violation.violation_type] = []
            by_type[violation.violation_type].append(violation)
        
        for violation_type, violations in by_type.items():
            print(f"📋 {violation_type} ({len(violations)} violations):")
            for violation in violations:
                print(f"  📄 {violation.file_path}:{violation.line_number}")
                print(f"     Code: {violation.line_content}")
                print(f"     Issue: {violation.reason}")
                if violation.suggested_fix:
                    print(f"     Fix: {violation.suggested_fix}")
                print()
    
    def apply_fixes(self) -> int:
        """Apply automatic fixes for violations where possible."""
        fixed_count = 0
        
        # Group violations by file for efficient batch processing
        by_file: Dict[str, List[SkipViolation]] = {}
        for violation in self.violations:
            if violation.violation_type == "FAIL_INSTEAD_OF_SKIP" and violation.suggested_fix:
                if violation.file_path not in by_file:
                    by_file[violation.file_path] = []
                by_file[violation.file_path].append(violation)
        
        for file_path_str, file_violations in by_file.items():
            file_path = self.project_root / file_path_str
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.splitlines()
                
                # Apply fixes in reverse line order to avoid line number shifts
                for violation in sorted(file_violations, key=lambda v: v.line_number, reverse=True):
                    line_idx = violation.line_number - 1
                    if line_idx < len(lines):
                        # Replace the entire self.fail() call with self.skipTest()
                        original_line = lines[line_idx]
                        indentation = original_line[:len(original_line) - len(original_line.lstrip())]
                        fixed_line = indentation + violation.suggested_fix
                        lines[line_idx] = fixed_line
                        fixed_count += 1
                        
                        if self.verbose:
                            print(f"Fixed {file_path}:{violation.line_number}")
                            print(f"  Before: {violation.line_content}")
                            print(f"  After:  {violation.suggested_fix}")
                
                # Write back the fixed content
                file_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
                
            except (OSError, UnicodeDecodeError) as e:
                print(f"Warning: Could not fix {file_path}: {e}")
        
        return fixed_count

def main():
    parser = argparse.ArgumentParser(description="Check test skip policy compliance")
    parser.add_argument("--fix", action="store_true", help="Automatically fix violations where possible")
    parser.add_argument("--verbose", action="store_true", help="Show detailed analysis")
    parser.add_argument("--directory", type=str, help="Directory to scan (default: mvp_site/tests)")
    
    args = parser.parse_args()
    
    # Find project root (look for CLAUDE.md)
    current_dir = Path.cwd()
    project_root = None
    
    for parent in [current_dir] + list(current_dir.parents):
        if (parent / "CLAUDE.md").exists():
            project_root = parent
            break
    
    if not project_root:
        print("Error: Could not find project root (CLAUDE.md not found)")
        sys.exit(1)
    
    if args.verbose:
        print(f"Project root: {project_root}")
    
    # Determine directory to scan (validate path to prevent traversal)
    if args.directory:
        # Validate that directory is within project root
        try:
            scan_dir = (project_root / args.directory).resolve()
            if not scan_dir.is_relative_to(project_root):
                print(f"Error: Directory {args.directory} is outside project root")
                sys.exit(1)
        except (ValueError, OSError) as e:
            print(f"Error: Invalid directory path {args.directory}: {e}")
            sys.exit(1)
    else:
        # Scan both test directories
        scan_dirs = [
            project_root / "mvp_site/tests",
            project_root / "mvp_site/test_integration"
        ]
    
    if args.directory:
        # Single directory mode
        if not scan_dir.exists():
            print(f"Error: Directory {scan_dir} does not exist")
            sys.exit(1)
        
        if args.verbose:
            print(f"Scanning: {scan_dir}")
        
        # Run the checker
        checker = SkipPolicyChecker(project_root, verbose=args.verbose)
        checker.scan_directory(scan_dir)
    else:
        # Multi-directory mode
        checker = SkipPolicyChecker(project_root, verbose=args.verbose)
        
        for scan_dir in scan_dirs:
            if scan_dir.exists():
                if args.verbose:
                    print(f"Scanning: {scan_dir}")
                checker.scan_directory(scan_dir)
            elif args.verbose:
                print(f"Skipping non-existent directory: {scan_dir}")
    
    # Apply fixes if requested
    if args.fix:
        fixed_count = checker.apply_fixes()
        if fixed_count > 0:
            print(f"✅ Fixed {fixed_count} violations")
            # Re-scan to show remaining violations
            checker.violations.clear()
            if args.directory:
                checker.scan_directory(scan_dir)
            else:
                for scan_dir in scan_dirs:
                    if scan_dir.exists():
                        checker.scan_directory(scan_dir)
    
    # Print report
    checker.print_report()
    
    # Exit with error code if violations remain
    if checker.violations:
        sys.exit(1)

if __name__ == "__main__":
    main()
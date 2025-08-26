#!/usr/bin/env python3
"""
Test Dependency Analyzer for Intelligent Test Selection

Analyzes git changes and maps them to relevant tests using configurable rules.
Conservative approach: when uncertain, run more tests to ensure safety.

Usage:
    python3 scripts/test_dependency_analyzer.py [--changes file1.py,file2.py] [--config path/to/config.json]
    python3 scripts/test_dependency_analyzer.py --git-diff  # Use git diff vs origin/main
    
Output:
    Writes selected test files to /tmp/selected_tests.txt
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List, Set, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestDependencyAnalyzer:
    """Analyzes file changes and maps them to relevant tests."""
    
    def __init__(self, config_path: str = None):
        """Initialize analyzer with configuration."""
        self.project_root = self._find_project_root()
        self.config_path = config_path or os.path.join(self.project_root, "test_selection_config.json")
        self.config = self._load_config()
        self.selected_tests: Set[str] = set()
        
    def _validate_path_safety(self, path: Path) -> bool:
        """Validate that a resolved path stays within project boundaries.
        
        Args:
            path: Path to validate
            
        Returns:
            bool: True if path is safe (within project), False otherwise
        """
        try:
            resolved = path.resolve()
            project_resolved = Path(self.project_root).resolve()
            return str(resolved).startswith(str(project_resolved))
        except (OSError, ValueError, RuntimeError):
            # Any path resolution errors are treated as unsafe
            return False
        
    def _find_project_root(self) -> str:
        """Find project root by looking for project markers."""
        current = Path(__file__).parent.absolute()
        while current.parent != current:
            # Check for strong project root indicators (git, .claude directory)
            if (current / ".git").exists() or (current / ".claude").exists():
                return str(current)
            
            # Check for CLAUDE.md with additional validation (avoid subdirectory CLAUDE.md files)
            if (current / "CLAUDE.md").exists():
                # Validate this is the real project root by checking for typical project structure
                # More flexible validation: require at least one key directory (not all three)
                has_mvp_site = (current / "mvp_site").exists()
                has_scripts = (current / "scripts").exists()
                has_docs = (current / "docs").exists()
                
                # Accept if we have at least one major project directory
                # This handles partial checkouts, development environments, or project restructuring
                if has_mvp_site or has_scripts or has_docs:
                    return str(current)
            
            current = current.parent
            
        # Fallback to script's grandparent directory (scripts/ is usually one level down from project root)
        return str(Path(__file__).parent.parent.absolute())
    
    def _load_config(self) -> Dict:
        """Load test selection configuration."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Config file not found at {self.config_path}, using defaults")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            logger.info("Falling back to default configuration")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for test mappings."""
        return {
            "mappings": {
                "direct": {
                    "main.py": ["test_main_*.py", "test_api_*.py"],
                    "gemini_service.py": ["test_gemini_*.py", "test_json_*.py"],
                    "firestore_service.py": ["test_firestore_*.py", "test_auth_*.py"],
                    "world_logic.py": ["test_world_*.py", "test_integration_*.py"],
                    "mvp_site/auth_service.py": ["test_auth_*.py", "test_main_authentication_*.py"],
                    "mvp_site/campaign_service.py": ["test_campaign_*.py"],
                    "mvp_site/character_service.py": ["test_character_*.py"],
                    "mvp_site/game_state_service.py": ["test_game_state_*.py", "test_world_*.py"]
                },
                "patterns": {
                    "frontend_v2/**/*.tsx": ["test_v2_*.py", "testing_ui/test_v2_*.py"],
                    "frontend_v2/**/*.js": ["test_v2_*.py", "testing_ui/test_v2_*.py"],
                    "mvp_site/mocks/*": ["test_mock_*.py"],
                    "mvp_site/static/**/*": ["testing_ui/test_*.py"],
                    "mvp_site/templates/**/*": ["testing_ui/test_*.py", "test_end2end/*.py"],
                    "*.yml": ["test_integration_*.py"],
                    "*.yaml": ["test_integration_*.py"],
                    "scripts/*": [".claude/hooks/tests/*"],
                    ".claude/hooks/*": [".claude/hooks/tests/*"]
                },
                "always_run": [
                    "mvp_site/test_integration/test_integration_mock.py",
                    ".claude/hooks/tests/test_fake_code_detection.py"
                ]
            }
        }
    
    def get_git_changes(self, base_branch: str = "origin/main") -> List[str]:
        """Get list of changed files from git diff with robust branch detection."""
        try:
            # Use environment variables if available (CI-friendly)
            if os.environ.get("GITHUB_BASE_REF"):
                base_branch = f"origin/{os.environ['GITHUB_BASE_REF']}"
            elif os.environ.get("BASE_BRANCH"):
                base_branch = os.environ["BASE_BRANCH"]
            
            # Try specified branch first, then common fallbacks
            branches_to_try = [base_branch, "origin/main", "origin/master", "main", "master"]
            
            for branch in branches_to_try:
                try:
                    cmd = ["git", "diff", "--name-only", f"{branch}...HEAD"]
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, 
                        cwd=self.project_root, timeout=10
                    )
                    
                    if result.returncode == 0:
                        files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
                        logger.info(f"Found {len(files)} changed files vs {branch}")
                        return files
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"Git command timeout for branch {branch}")
                    continue
                    
            logger.warning("Git diff failed, falling back to full test suite")
            return []
            
        except Exception as e:
            logger.error(f"Error getting git changes: {e}")
            return []
    
    def find_matching_tests(self, file_path: str) -> List[str]:
        """Find tests that match a given file path."""
        matching_tests = []
        
        # Check direct mappings
        direct_mappings = self.config.get("mappings", {}).get("direct", {})
        for source_file, test_patterns in direct_mappings.items():
            if file_path == source_file or file_path.endswith("/" + source_file):
                matching_tests.extend(test_patterns)
                logger.debug(f"Direct mapping: {file_path} -> {test_patterns}")
        
        # Check pattern mappings
        pattern_mappings = self.config.get("mappings", {}).get("patterns", {})
        for pattern, test_patterns in pattern_mappings.items():
            if fnmatch(file_path, pattern):
                matching_tests.extend(test_patterns)
                logger.debug(f"Pattern mapping: {file_path} matches {pattern} -> {test_patterns}")
        
        # If no specific mappings found, apply conservative rules
        if not matching_tests:
            matching_tests.extend(self._get_conservative_mappings(file_path))
        
        return matching_tests
    
    def _find_tests_subdirectories(self, file_path: str) -> List[str]:
        """Generic logic to find tests/ subdirectories for any changed file.
        
        This implements the user's request: 'always looks for tests/ subdir for any changed files'
        Uses efficient Path.glob patterns and prevents duplicate processing.
        """
        start_time = time.perf_counter()  # Better timing precision
        
        tests_patterns: List[str] = []
        processed_dirs = set()  # Prevent duplicate processing as suggested by Copilot
        file_dir = Path(file_path).parent
        
        # Use cached project root and proper path anchoring for security
        if not hasattr(self, '_cached_project_root'):
            self._cached_project_root = Path(self._find_project_root()).resolve()
        project_root = self._cached_project_root
        
        # Security: Ensure file_dir is anchored within project_root
        try:
            file_dir = file_dir.resolve()
            file_dir.relative_to(project_root)  # Validates path is within project
        except ValueError:
            logger.warning(f"File {file_path} is outside project root {project_root}")
            return []
        
        # Start from the file's directory and walk up to project root
        current_dir = file_dir
        
        while project_root in current_dir.parents or current_dir == project_root:
            # Avoid processing the same directory multiple times
            dir_str = str(current_dir)
            if dir_str not in processed_dirs:
                processed_dirs.add(dir_str)
                
                # Check if this directory has a tests/ subdirectory
                tests_dir = current_dir / "tests"
                if tests_dir.exists() and tests_dir.is_dir():
                    pattern = str((tests_dir / "test_*.py").as_posix())
                    if pattern not in tests_patterns:
                        tests_patterns.append(pattern)
            
            # Move to parent directory with early termination
            if current_dir == current_dir.parent:
                break  # Reached filesystem root
            current_dir = current_dir.parent
        
        # Always include repository-root tests dir if not already added
        root_pattern = "tests/test_*.py"
        if root_pattern not in tests_patterns:
            tests_patterns.append(root_pattern)
        
        # Performance monitoring as suggested by CodeRabbit
        elapsed_time = time.perf_counter() - start_time
        if tests_patterns:
            logger.debug(f"Generic tests/ directory search for {file_path}: {tests_patterns} (took {elapsed_time:.3f}s, processed {len(processed_dirs)} dirs)")
        
        return tests_patterns

    def _get_conservative_mappings(self, file_path: str) -> List[str]:
        """Conservative fallback mappings when no specific rules match."""
        conservative_tests = []
        
        # FIRST: Always apply generic tests/ subdirectory logic (user's main request)
        generic_tests = self._find_tests_subdirectories(file_path)
        conservative_tests.extend(generic_tests)
        
        # THEN: Apply specific conservative mappings as additional coverage
        
        # Any Python file in mvp_site/ triggers core tests
        if file_path.startswith("mvp_site/") and file_path.endswith(".py"):
            conservative_tests.extend([
                "test_main_*.py",
                "test_api_*.py", 
                "test_integration_*.py"
            ])
            logger.debug(f"Conservative mapping for mvp_site Python: {file_path}")
        
        # Frontend changes trigger UI tests
        elif any(file_path.endswith(ext) for ext in [".html", ".js", ".tsx", ".css"]):
            conservative_tests.extend([
                "testing_ui/test_*.py",
                "test_end2end/*.py"
            ])
            logger.debug(f"Conservative mapping for frontend: {file_path}")
        
        # Configuration changes trigger integration tests
        elif any(file_path.endswith(ext) for ext in [".yml", ".yaml", ".json", ".sh"]):
            conservative_tests.extend([
                "test_integration_*.py",
                ".claude/hooks/tests/*"
            ])
            logger.debug(f"Conservative mapping for config: {file_path}")
        
        # Test files themselves should always be included
        elif "test_" in file_path and file_path.endswith(".py"):
            conservative_tests.append(file_path)
            logger.debug(f"Test file directly included: {file_path}")
        
        return conservative_tests
    
    def expand_test_patterns(self, test_patterns: List[str]) -> List[str]:
        """Expand glob patterns to actual test file paths."""
        actual_tests = []
        
        for pattern in test_patterns:
            if "*" in pattern:
                # Handle glob patterns
                expanded = self._expand_glob_pattern(pattern)
                actual_tests.extend(expanded)
            else:
                # Handle direct file paths
                if self._test_file_exists(pattern):
                    actual_tests.append(pattern)
                else:
                    logger.debug(f"Test file not found: {pattern}")
        
        return actual_tests
    
    def _expand_glob_pattern(self, pattern: str) -> List[str]:
        """Expand a glob pattern to matching test files."""
        try:
            # Convert pattern to absolute path for searching
            if pattern.startswith("/"):
                search_pattern = pattern[1:]  # Remove leading slash
            else:
                search_pattern = pattern
            
            # Use pathlib to find matching files
            project_path = Path(self.project_root)
            matches = []
            
            # Handle different pattern types
            if "**" in search_pattern:
                # Recursive pattern
                parts = search_pattern.split("**")
                if len(parts) == 2:
                    base_pattern = parts[0].rstrip("/")
                    file_pattern = parts[1].lstrip("/")
                    
                    base_path = project_path / base_pattern if base_pattern else project_path
                    if base_path.exists() and self._validate_path_safety(base_path):
                        for match in base_path.rglob(file_pattern):
                            if match.is_file() and self._validate_path_safety(match):
                                relative_path = match.relative_to(project_path)
                                matches.append(str(relative_path))
            else:
                # Simple glob pattern - search entire project for matches
                if "*" in search_pattern:
                    # Use rglob for comprehensive search
                    for match in project_path.rglob(search_pattern):
                        if match.is_file() and match.name.startswith("test_") and self._validate_path_safety(match):
                            relative_path = match.relative_to(project_path)
                            matches.append(str(relative_path))
                else:
                    # Direct file path
                    pattern_path = project_path / search_pattern
                    if pattern_path.exists() and pattern_path.is_file() and self._validate_path_safety(pattern_path):
                        relative_path = pattern_path.relative_to(project_path)
                        matches.append(str(relative_path))
            
            logger.debug(f"Pattern '{pattern}' expanded to {len(matches)} files: {matches[:5]}...")
            return matches
            
        except Exception as e:
            logger.warning(f"Error expanding pattern '{pattern}': {e}")
            return []
    
    def _test_file_exists(self, file_path: str) -> bool:
        """Check if a test file exists."""
        full_path = os.path.join(self.project_root, file_path)
        exists = os.path.isfile(full_path)
        if not exists:
            logger.debug(f"Test file does not exist: {full_path}")
        return exists
    
    def add_always_run_tests(self):
        """Add tests that should always run."""
        always_run = self.config.get("mappings", {}).get("always_run", [])
        for test_pattern in always_run:
            expanded = self.expand_test_patterns([test_pattern])
            self.selected_tests.update(expanded)
            logger.debug(f"Always run: {test_pattern} -> {len(expanded)} tests")
    
    def add_modified_test_files(self, changed_files: List[str]):
        """Add any test files that were directly modified."""
        for file_path in changed_files:
            if "test_" in file_path and file_path.endswith(".py"):
                if self._test_file_exists(file_path):
                    self.selected_tests.add(file_path)
                    logger.debug(f"Modified test file included: {file_path}")
    
    def analyze_changes(self, changed_files: List[str]) -> Set[str]:
        """Analyze changed files and return set of tests to run."""
        logger.info(f"Analyzing {len(changed_files)} changed files")
        
        # Reset selected tests
        self.selected_tests = set()
        
        # Always include critical safety tests
        self.add_always_run_tests()
        
        # Include any modified test files
        self.add_modified_test_files(changed_files)
        
        # Safety threshold: if too many files changed, run full suite
        safety_threshold = 0.5  # 50% of tracked files
        total_tracked_files = self._count_tracked_files()
        
        if len(changed_files) > total_tracked_files * safety_threshold:
            logger.warning(f"Large change detected ({len(changed_files)} files, "
                         f">{safety_threshold*100}% of codebase). Running full test suite.")
            all_tests = self._get_all_tests()
            self.selected_tests.update(all_tests)
            return all_tests
        
        # Process each changed file
        for file_path in changed_files:
            if not file_path:  # Skip empty strings
                continue
                
            logger.debug(f"Processing changed file: {file_path}")
            test_patterns = self.find_matching_tests(file_path)
            
            if test_patterns:
                expanded_tests = self.expand_test_patterns(test_patterns)
                self.selected_tests.update(expanded_tests)
                logger.debug(f"File {file_path} mapped to {len(expanded_tests)} tests")
            else:
                logger.debug(f"No specific mappings for {file_path}")
        
        # Ensure we have at least some tests
        if not self.selected_tests:
            logger.warning("No tests selected, falling back to core safety tests")
            return self._get_core_safety_tests()
        
        logger.info(f"Selected {len(self.selected_tests)} tests for execution")
        return self.selected_tests
    
    def _count_tracked_files(self) -> int:
        """Count total number of tracked files in repository."""
        try:
            # Avoid shell entirely for better security
            git_result = subprocess.run(
                ["git", "ls-files"], capture_output=True, text=True,
                cwd=self.project_root, timeout=10
            )
            if git_result.returncode == 0:
                return len([f for f in git_result.stdout.strip().split('\n') if f.strip()])
        except Exception as e:
            logger.debug(f"Could not count tracked files: {e}")
        
        # Fallback estimate
        return 500
    
    def _get_all_tests(self) -> Set[str]:
        """Get all test files in the repository."""
        all_tests = set()
        
        # Find all test_*.py files
        try:
            project_path = Path(self.project_root)
            for test_file in project_path.rglob("test_*.py"):
                relative_path = test_file.relative_to(project_path)
                all_tests.add(str(relative_path))
        except Exception as e:
            logger.error(f"Error finding all tests: {e}")
        
        logger.info(f"Found {len(all_tests)} total test files")
        return all_tests
    
    def _get_core_safety_tests(self) -> Set[str]:
        """Get core safety tests as fallback."""
        safety_tests = set()
        always_run = self.config.get("mappings", {}).get("always_run", [])
        
        for test_pattern in always_run:
            expanded = self.expand_test_patterns([test_pattern])
            safety_tests.update(expanded)
        
        # Add basic integration tests
        basic_patterns = [
            "mvp_site/test_integration/test_*.py",
            "mvp_site/tests/test_main_*.py",
            "mvp_site/tests/test_api_*.py"
        ]
        
        for pattern in basic_patterns:
            expanded = self.expand_test_patterns([pattern])
            safety_tests.update(expanded)
        
        logger.info(f"Core safety tests: {len(safety_tests)} files")
        return safety_tests
    
    def write_selected_tests(self, output_path: str = "/tmp/selected_tests.txt"):
        """Write selected tests to output file."""
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Sort tests for consistent output
            sorted_tests = sorted(self.selected_tests)
            
            with open(output_path, 'w') as f:
                for test_path in sorted_tests:
                    f.write(f"{test_path}\n")
            
            logger.info(f"Wrote {len(sorted_tests)} selected tests to {output_path}")
            
            # Also log the selection for debugging
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Selected tests:")
                for test_path in sorted_tests:
                    logger.debug(f"  {test_path}")
        
        except Exception as e:
            logger.error(f"Failed to write selected tests to {output_path}: {e}")
            raise


def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Analyze file changes and select relevant tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --git-diff                           # Use git diff vs origin/main
  %(prog)s --changes main.py,auth_service.py   # Analyze specific files
  %(prog)s --config custom_config.json         # Use custom configuration
  %(prog)s --dry-run                            # Show selection without writing file
        """
    )
    
    parser.add_argument(
        "--changes", 
        help="Comma-separated list of changed files to analyze"
    )
    parser.add_argument(
        "--git-diff", action="store_true",
        help="Use git diff vs origin/main to get changed files"
    )
    parser.add_argument(
        "--config",
        help="Path to test selection configuration file"
    )
    parser.add_argument(
        "--output", default="/tmp/selected_tests.txt",
        help="Output file for selected tests (default: /tmp/selected_tests.txt)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show selection without writing output file"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--base-branch", default="origin/main",
        help="Base branch for git diff (default: origin/main)"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize analyzer
        analyzer = TestDependencyAnalyzer(config_path=args.config)
        
        # Get changed files
        if args.git_diff:
            changed_files = analyzer.get_git_changes(args.base_branch)
            if not changed_files:
                logger.warning("No changes detected, falling back to full test suite")
                selected_tests = analyzer._get_all_tests()
            else:
                selected_tests = analyzer.analyze_changes(changed_files)
        elif args.changes:
            changed_files = [f.strip() for f in args.changes.split(',') if f.strip()]
            selected_tests = analyzer.analyze_changes(changed_files)
        else:
            logger.error("Must specify either --git-diff or --changes")
            sys.exit(1)
        
        # Update analyzer's selected tests
        analyzer.selected_tests = selected_tests
        
        # Output results
        if args.dry_run:
            print(f"Selected {len(selected_tests)} tests:")
            for test_path in sorted(selected_tests):
                print(f"  {test_path}")
        else:
            analyzer.write_selected_tests(args.output)
            print(f"Selected {len(selected_tests)} tests written to {args.output}")
    
    except Exception as e:
        logger.error(f"Test dependency analysis failed: {e}")
        logger.info("Falling back to full test suite")
        
        # Write all tests as fallback
        if not args.dry_run:
            try:
                analyzer = TestDependencyAnalyzer()
                analyzer.selected_tests = analyzer._get_all_tests()
                analyzer.write_selected_tests(args.output)
                print(f"Fallback: All tests written to {args.output}")
            except Exception as fallback_error:
                logger.error(f"Fallback failed: {fallback_error}")
                sys.exit(1)
        
        sys.exit(1)


if __name__ == "__main__":
    main()

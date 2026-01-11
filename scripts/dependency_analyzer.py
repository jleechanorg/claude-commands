#!/usr/bin/env python3
"""
Intelligent Test Selection Analyzer
Based on PR #1313 design - analyzes git changes and selects relevant tests.

Implements two-tier strategy:
- mvp_site/ directory: Full intelligent test selection with file-to-test mapping
- Other directories: Simple tests/ subdirectory pattern

Conservative approach: when uncertain, run more tests to ensure safety.

Usage:
    python3 scripts/dependency_analyzer.py [--changes file1.py,file2.py] [--config path/to/config.json]
    python3 scripts/dependency_analyzer.py --git-diff  # Use git diff vs origin/main

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DependencyAnalyzer:
    """Analyzes file changes and maps them to relevant tests."""

    def __init__(self, config_path: str | None = None) -> None:
        """Initialize analyzer with configuration."""
        self.project_root = self._find_project_root()
        self.config_path = config_path or os.path.join(self.project_root, "test_selection_config.json")
        self.config = self._load_config()
        self.selected_tests: set[str] = set()

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
            return resolved.is_relative_to(project_resolved)
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
                has_mvp_site = (current / "mvp_site").exists()
                has_scripts = (current / "scripts").exists()
                has_docs = (current / "docs").exists()

                if has_mvp_site or has_scripts or has_docs:
                    return str(current)

            current = current.parent

        # Fallback to script's grandparent directory (scripts/ is usually one level down from project root)
        return str(Path(__file__).parent.parent.absolute())

    def _load_config(self) -> dict:
        """Load test selection configuration."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Config file not found at {self.config_path}, using defaults")
            return self._get_default_config()

        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            logger.info("Falling back to default configuration")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Get default configuration for test mappings - focused on mvp_site/ intelligence."""
        return {
            "mappings": {
                "direct": {
                    # Core mvp_site application files - intelligent mapping
                    "mvp_site/main.py": ["test_main*.py", "test_integration*.py"],
                    "mvp_site/game_state.py": ["test_game_state*.py", "test_integration*.py"],
                    "mvp_site/llm_service.py": ["test_gemini*.py", "test_ai*.py"],
                    "mvp_site/firestore_service.py": ["test_firestore*.py", "test_database*.py"],
                    "mvp_site/mcp_client.py": ["test_mcp*.py", "test_integration*.py"],
                    "mvp_site/world_logic.py": ["test_world*.py", "test_game_state*.py"],
                    "mvp_site/constants.py": ["test_*"],  # Constants affect everything
                    "mvp_site/config.py": ["test_*"],    # Config affects everything

                    # Legacy root-level files (backward compatibility)
                    "main.py": ["test_main_*.py", "test_api_*.py"],
                    "llm_service.py": ["test_gemini_*.py", "test_json_*.py"],
                    "firestore_service.py": ["test_firestore_*.py", "test_auth_*.py"],
                    "world_logic.py": ["test_world_*.py", "test_integration_*.py"]
                },
                "patterns": {
                    # mvp_site patterns - intelligent mapping
                    "mvp_site/schemas/**/*.py": ["test_schemas*.py", "test_entities*.py"],
                    "mvp_site/testing_framework/**/*.py": ["test_testing_framework*.py"],
                    "mvp_site/static/**/*": ["test_ui*.py", "test_integration*.py"],
                    "mvp_site/templates/**/*": ["test_ui*.py", "test_integration*.py"],
                    "mvp_site/prompts/**/*": ["test_gemini*.py", "test_ai*.py"],
                    "mvp_site/requirements.txt": ["test_integration*.py"],

                    # Other directories use simple tests/ pattern (handled separately)
                    # Legacy patterns
                    "frontend_v2/**/*.tsx": ["test_v2_*.py", "testing_ui/test_v2_*.py"],
                    "frontend_v2/**/*.js": ["test_v2_*.py", "testing_ui/test_v2_*.py"],
                    "*.yml": ["test_integration_*.py"],
                    "*.yaml": ["test_integration_*.py"]
                },
                "always_run": [
                    "mvp_site/tests/test_integration*.py",
                    "mvp_site/test_integration/test_integration_mock.py"
                ]
            }
        }

    def get_git_changes(self, base_branch: str = "origin/main") -> list[str]:
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
                        cmd, check=False, capture_output=True, text=True,
                        cwd=self.project_root, timeout=30, shell=False
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

    def find_matching_tests(self, file_path: str) -> list[str]:
        """Find tests that match a given file path using corrected strategy."""
        matching_tests = []

        if file_path.startswith("mvp_site/"):
            # mvp_site/: Full intelligent test selection
            matching_tests = self._find_mvp_site_tests(file_path)
        elif self._should_use_tests_subdir_pattern(file_path):
            # Specific directories: Simple tests/ subdirectory pattern
            matching_tests = self._find_other_directory_tests(file_path)
        else:
            # All other files: Conservative fallback only (no broad test inclusion)
            matching_tests = []

        # If no specific mappings found, apply conservative rules
        if not matching_tests:
            matching_tests.extend(self._get_conservative_mappings(file_path))

        return matching_tests

    def _find_mvp_site_tests(self, file_path: str) -> list[str]:
        """Find tests for mvp_site/ files using intelligent mapping."""
        matching_tests = []

        # Check direct mappings
        direct_mappings = self.config.get("mappings", {}).get("direct", {})
        for source_file, test_patterns in direct_mappings.items():
            if file_path == source_file or file_path.endswith("/" + source_file):
                matching_tests.extend(test_patterns)
                logger.debug(f"MVP direct mapping: {file_path} -> {test_patterns}")

        # Check pattern mappings
        pattern_mappings = self.config.get("mappings", {}).get("patterns", {})
        for pattern, test_patterns in pattern_mappings.items():
            if fnmatch(file_path, pattern):
                matching_tests.extend(test_patterns)
                logger.debug(f"MVP pattern mapping: {file_path} matches {pattern} -> {test_patterns}")

        return matching_tests

    def _should_use_tests_subdir_pattern(self, file_path: str) -> bool:
        """Determine if file should use tests/ subdirectory pattern."""
        # Only specific directories should use tests/ subdirectory pattern
        tests_subdir_directories = [
            ".claude/commands/",
            ".claude/hooks/",
            "scripts/",
            "orchestration/",
            "claude_command_scripts/",
            "claude-bot-commands/"
        ]

        return any(file_path.startswith(prefix) for prefix in tests_subdir_directories)

    def _find_other_directory_tests(self, file_path: str) -> list[str]:
        """Find tests for specific directories using simple tests/ subdirectory pattern."""
        # Use the existing tests/ subdirectory logic
        test_patterns = self._find_tests_subdirectories(file_path)
        logger.debug(f"Tests subdir mapping: {file_path} -> {test_patterns}")
        return test_patterns

    def _find_tests_subdirectories(self, file_path: str) -> list[str]:
        """Find tests/ subdirectories for specific changed files only.

        This only looks for tests in the immediate directory of the changed file,
        not globally across the entire project.
        """
        start_time = time.perf_counter()

        tests_patterns: list[str] = []
        
        project_root = Path(self.project_root).resolve()
        
        # Ensure we have an absolute path for the file
        resolved_file_path = Path(file_path)
        if not resolved_file_path.is_absolute():
            resolved_file_path = (project_root / file_path).resolve()
            
        # Ensure the file is actually within the project
        if not self._validate_path_safety(resolved_file_path):
            logger.warning(f"File path {file_path} is outside project root")
            return []

        file_dir = resolved_file_path.parent

        # Only check the immediate directory and its parent for tests/ subdirectory
        # This prevents the broad "tests/test_*.py" pattern from matching everything
        dirs_to_check = [file_dir, file_dir.parent] if file_dir.parent != file_dir else [file_dir]

        for current_dir in dirs_to_check:
            # Stop if we've gone above project root or are outside it
            if not current_dir.is_relative_to(project_root):
                break

            # Check if this directory has a tests/ subdirectory
            tests_dir = current_dir / "tests"
            if tests_dir.exists() and tests_dir.is_dir():
                # Use full path to avoid matching every test in the project
                try:
                    relative_tests_path = tests_dir.relative_to(project_root)
                    pattern = str((relative_tests_path / "test_*.py").as_posix())
                    if pattern not in tests_patterns:
                        tests_patterns.append(pattern)
                except ValueError:
                    continue

        # Performance monitoring
        elapsed_time = time.perf_counter() - start_time
        if tests_patterns:
            logger.debug(f"Specific tests/ directory search for {file_path}: {tests_patterns} (took {elapsed_time:.3f}s)")
        else:
            logger.debug(f"No tests/ subdirectories found for {file_path}")

        return tests_patterns

    def _get_conservative_mappings(self, file_path: str) -> list[str]:
        """Conservative fallback mappings when no specific rules match."""
        conservative_tests = []

        if file_path.startswith("mvp_site/"):
            # mvp_site/ conservative mappings - more intelligent
            if file_path.endswith(".py"):
                conservative_tests.extend([
                    "mvp_site/tests/test_integration*.py",
                    "mvp_site/tests/test_main*.py"
                ])
                logger.debug(f"MVP conservative mapping for Python: {file_path}")
            elif any(file_path.endswith(ext) for ext in [".html", ".js", ".css"]):
                conservative_tests.extend([
                    "mvp_site/tests/test_ui*.py",
                    "mvp_site/tests/test_integration*.py"
                ])
                logger.debug(f"MVP conservative mapping for frontend: {file_path}")
            elif any(file_path.endswith(ext) for ext in [".yml", ".yaml", ".json"]):
                conservative_tests.extend([
                    "mvp_site/tests/test_integration*.py"
                ])
                logger.debug(f"MVP conservative mapping for config: {file_path}")
        elif self._should_use_tests_subdir_pattern(file_path):
            # Only specific directories use tests/ subdirectory pattern
            generic_tests = self._find_tests_subdirectories(file_path)
            conservative_tests.extend(generic_tests)
            logger.debug(f"Conservative tests/ subdir mapping: {file_path} -> {generic_tests}")
        else:
            # For all other files: minimal safety tests only
            conservative_tests.extend([
                "mvp_site/tests/test_integration*.py"  # Just basic integration tests
            ])
            logger.debug(f"Minimal conservative mapping: {file_path} -> basic integration tests")

        # Test files themselves should always be included
        if "test_" in file_path and file_path.endswith(".py"):
            conservative_tests.append(file_path)
            logger.debug(f"Test file directly included: {file_path}")

        return conservative_tests

    def expand_test_patterns(self, test_patterns: list[str]) -> list[str]:
        """Expand glob patterns to actual test file paths."""
        actual_tests = []

        for pattern in test_patterns:
            if "*" in pattern:
                # Handle glob patterns
                expanded = self._expand_glob_pattern(pattern)
                actual_tests.extend(expanded)
            # Handle direct file paths
            elif self._test_file_exists(pattern):
                actual_tests.append(pattern)
            else:
                logger.debug(f"Test file not found: {pattern}")

        return actual_tests

    def _expand_glob_pattern(self, pattern: str) -> list[str]:
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
            # Simple glob pattern - search entire project for matches
            elif "*" in search_pattern:
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

    def add_always_run_tests(self) -> None: 
        """Add tests that should always run."""
        always_run = self.config.get("mappings", {}).get("always_run", [])
        for test_pattern in always_run:
            expanded = self.expand_test_patterns([test_pattern])
            if expanded:
                self.selected_tests.update(expanded)
                logger.debug(f"Always run: {test_pattern} -> {len(expanded)} tests")
            else:
                # If no files match (e.g., placeholder integration mocks), keep the pattern
                self.selected_tests.add(test_pattern)
                logger.debug(f"Always run placeholder added: {test_pattern}")

    def add_modified_test_files(self, changed_files: list[str]) -> None:
        """Add any test files that were directly modified."""
        for file_path in changed_files:
            if "test_" in file_path and file_path.endswith(".py"):
                if self._test_file_exists(file_path):
                    self.selected_tests.add(file_path)
                    logger.debug(f"Modified test file included: {file_path}")

    def analyze_changes(self, changed_files: list[str]) -> set[str]:
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
            logger.warning(
                f"Large change detected ({len(changed_files)} files, "
                f">{safety_threshold*100}% of codebase). Running full test suite."
            )
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
                ["git", "ls-files"], check=False, capture_output=True, text=True,
                cwd=self.project_root, timeout=30, shell=False
            )
            if git_result.returncode == 0:
                return len([f for f in git_result.stdout.strip().split('\n') if f.strip()])
        except Exception as e:
            logger.debug(f"Could not count tracked files: {e}")

        # Fallback estimate
        return 500

    def _get_all_tests(self) -> set[str]:
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

    def _get_core_safety_tests(self) -> set[str]:
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

    def write_selected_tests(self, output_path: str = "/tmp/selected_tests.txt") -> None:
        """Write selected tests to output file."""
        try:
            # Ensure output directory exists
            dirpath = os.path.dirname(output_path)
            if dirpath:
                os.makedirs(dirpath, exist_ok=True)

            # Sort tests for consistent output
            sorted_tests = sorted(self.selected_tests)

            with open(output_path, 'w', encoding='utf-8') as f:
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


def main() -> None:
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Analyze file changes and select relevant tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                      # Default: git diff vs origin/main
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
        analyzer = DependencyAnalyzer(config_path=args.config)

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
            # Default behavior: analyze current branch vs origin/main
            logger.info("No arguments provided, defaulting to --git-diff mode vs origin/main")
            changed_files = analyzer.get_git_changes(args.base_branch)
            if not changed_files:
                logger.warning("No changes detected, falling back to full test suite")
                selected_tests = analyzer._get_all_tests()
            else:
                selected_tests = analyzer.analyze_changes(changed_files)

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
                analyzer = DependencyAnalyzer(config_path=args.config)
                analyzer.selected_tests = analyzer._get_all_tests()
                analyzer.write_selected_tests(args.output)
                print(f"Fallback: All tests written to {args.output}")
            except Exception as fallback_error:
                logger.error(f"Fallback failed: {fallback_error}")
                sys.exit(1)

        sys.exit(1)


if __name__ == "__main__":
    main()

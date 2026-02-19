"""
Pytest configuration for .claude/commands/ directory.

CLI scripts in this directory are designed as manual CLI utilities
(python3 file.py), not pytest tests. To prevent pytest from collecting them:

  - Files have been renamed to avoid the test_* prefix:
    e.g., check_incremental_fetch.py (was test_incremental_fetch.py)

  - Any remaining CLI scripts that can't be renamed are excluded below.

Note: collect_ignore_glob only works during directory-based discovery.
When run_tests.sh passes files directly to pytest (e.g., pytest file.py),
this setting is bypassed. The rename approach is more reliable.
"""

collect_ignore_glob = [
    "test_orchestrate_integration.py",
]

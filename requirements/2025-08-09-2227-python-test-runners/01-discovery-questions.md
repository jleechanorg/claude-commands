# Discovery Questions

**Date**: 2025-08-09 22:27
**Phase**: Initial Discovery

## Q1: Should the new Python scripts maintain exact CLI compatibility with the shell versions?
**Default if unknown:** Yes (maintains backward compatibility for all existing usage)

## Q2: Should the Python implementation fix the memory issues by limiting parallel processes?
**Default if unknown:** Yes (the primary driver is fixing OOM crashes from unlimited parallelism)

## Q3: Should we preserve all existing features like coverage mode, integration tests, and colored output?
**Default if unknown:** Yes (feature parity is essential for migration success)

## Q4: Should the migration include updating GitHub Actions workflows that reference these scripts?
**Default if unknown:** Yes (GitHub Actions are part of the CI/CD pipeline that must continue working)

## Q5: Should we create a gradual migration path or do a complete replacement at once?
**Default if unknown:** Complete replacement (simpler than maintaining dual implementations)

## Context Analysis Findings

### Files Referencing `run_tests.sh` (50+ references found):
- **Core Infrastructure**: README.md, CLAUDE.md, directory_structure.md
- **CI/CD Scripts**: run_ci_replica.sh, ci_replica/*.sh files  
- **Documentation**: 25+ roadmap and docs files
- **Testing Framework**: mvp_site/testing_framework/, mvp_site/test_integration/
- **Setup Scripts**: scripts/setup-dev-env.sh, scripts/testing_help.sh

### Files Referencing `run_ci_replica` (3 references found):
- roadmap/scratchpad_modular_copilot_architecture.md
- roadmap/modular_copilot_implementation_summary.md
- requirements/2025-08-09-2227-python-test-runners/00-initial-request.md

### CI Replica Scripts in `ci_replica/` Directory:
- `ci_debug_replica.sh` - Debug version for troubleshooting CI failures
- `ci_failure_reproducer.sh` - Reproduces specific CI failures locally
- `ci_local_replica.sh` - Main CI replication script
- `ci_replica_launcher.sh` - Launcher for CI replica system
- `simulate_ci.sh` - Simulates CI environment

### Key Technical Constraints Identified:
1. **Memory Management**: Current issue with 60+ parallel Python processes using 18GB+ RAM
2. **CLI Interface**: Extensive usage across documentation and scripts requires exact CLI compatibility
3. **Testing Framework Integration**: Deep integration with mvp_site testing infrastructure
4. **CI/CD Pipeline**: Critical dependency in GitHub Actions and local CI replica system
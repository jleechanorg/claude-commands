# Comprehensive Requirements Specification

**Project**: Intelligent Test Selection System for WorldArchitect.AI  
**Date**: 2025-08-15 00:03  
**Version**: 1.0  
**Status**: Final Requirements  

## Problem Statement

The current test suite in WorldArchitect.AI runs all tests regardless of changes, leading to unnecessary execution time and resource consumption. With 100+ test files across multiple directories and sophisticated parallel execution, developers need an intelligent system that runs only tests relevant to their changes while maintaining safety and compatibility.

## Solution Overview

Implement an intelligent test selection system that analyzes git changes, maps dependencies between source files and tests, and executes only relevant tests by default. The system preserves all existing safety mechanisms, maintains backward compatibility, and provides significant performance improvements for PR-focused development workflows.

## Functional Requirements

### FR1: Default Intelligent Selection Behavior
- **Requirement**: Intelligent test selection runs by default without flags
- **Behavior**: `./run_tests.sh` automatically analyzes changes and selects relevant tests
- **Override**: `--full` or `--all-tests` flag forces complete test suite execution
- **Rationale**: Makes optimization the default experience while preserving full test capability

### FR2: Git Change Detection and Analysis
- **Requirement**: Analyze git diff to identify changed files in PRs
- **Implementation**: `git diff --name-only origin/main...HEAD` for PR changes
- **Fallback**: Run full test suite if git analysis fails or in non-git environments
- **Categories**: Distinguish production code, test files, frontend, configuration changes

### FR3: File-to-Test Dependency Mapping
- **Core Mappings**:
  - `main.py` → `test_main_*.py`, `test_api_*.py`, `test_end2end/*`
  - `llm_service.py` → `test_gemini_*.py`, `test_json_*.py`
  - `firestore_service.py` → `test_firestore_*.py`, auth-related tests
  - `world_logic.py` → `test_world_*.py`, integration tests
  - `frontend_v2/*` → `test_v2_*.py`, browser tests in `testing_ui/`
- **Pattern Support**: Glob patterns for scalable file matching
- **Cross-layer Mapping**: Frontend changes trigger related API tests

### FR4: Critical Test Safety Nets
- **Always Run Tests**:
  - `mvp_site/test_integration/test_integration_mock.py`
  - All hook tests in `.claude/hooks/tests/`
  - Any directly modified test files
  - Core integration tests for system validation
- **Safety Threshold**: When >50% of files changed, run full test suite
- **Uncertainty Handling**: Conservative approach - run more tests when uncertain

### FR5: Configuration Management and Extensibility
- **Configuration File**: `test_selection_config.json` with dependency mappings
- **Glob Pattern Support**: `frontend_v2/**/*.tsx` → test pattern matching
- **Hierarchical Configuration**: Global patterns + project-specific overrides
- **Runtime Updates**: Support for configuration changes without system restart

### FR6: Transparency and Debugging
- **Selection Reporting**: Show which tests selected and why
- **Dry-run Mode**: `--dry-run` shows selection without execution
- **Performance Metrics**: Report time saved and test reduction percentage
- **Audit Trail**: Log all selection decisions for debugging

### FR7: Backward Compatibility
- **Existing Flags**: Full compatibility with `--coverage`, `--integration`
- **Environment Variables**: Preserve `TESTING`, `TEST_MODE`, `CI` behavior
- **Output Format**: Maintain existing colored output and progress tracking
- **CLI Patterns**: Follow established command-line interface conventions

## Technical Requirements

### TR1: Integration with Existing Infrastructure
- **Primary Implementation**: Extend `run_tests.sh` with intelligent selection logic
- **Memory Safety**: Preserve existing memory monitoring (5GB local, 10GB CI replica)
- **Parallel Execution**: Maintain environment-aware worker limits
- **Resource Management**: Integrate with existing safety kill switches

### TR2: Dependency Analysis Engine
- **Implementation**: Python script in `/scripts/test_dependency_analyzer.py`
- **Analysis Method**: Static import analysis + configurable mapping rules
- **Performance**: Sub-second analysis for typical PR changes
- **Caching**: File-based dependency cache in `/tmp/` directory

### TR3: GitHub Actions Integration
- **Workflow Compatibility**: Seamless integration with existing `.github/workflows/`
- **Environment Detection**: Respect GitHub Actions vs local vs CI replica modes
- **Artifact Preservation**: Maintain test result and coverage artifact collection
- **Security**: Follow SHA-pinned action patterns

### TR4: Performance Requirements
- **Target Reduction**: 60-80% test execution time reduction for focused changes
- **Safety Threshold**: <5% false negative rate (missing relevant tests)
- **Feedback Speed**: <2 minute total feedback loop for typical PR changes
- **Scalability**: Handle 500+ test files and 50+ directories efficiently

### TR5: Error Handling and Fallbacks
- **Graceful Degradation**: Fall back to full test suite on analysis errors
- **Dependency Resolution Failures**: Conservative approach when mappings uncertain
- **Git Environment Issues**: Handle non-git environments and detached HEADs
- **Configuration Errors**: Validate configuration and provide clear error messages

## Implementation Hints and Patterns

### File Modification Strategy
1. **Primary**: Enhance `run_tests.sh` with intelligent selection logic
2. **Secondary**: Create `scripts/test_dependency_analyzer.py` for dependency analysis
3. **Configuration**: Add `test_selection_config.json` for mapping rules
4. **Integration**: Hook into existing test discovery and execution flow

### Architecture Pattern
```bash
# High-level flow
git diff analysis → dependency mapping → test selection → existing execution pipeline
```

### Configuration Structure
```json
{
  "mappings": {
    "direct": {
      "main.py": ["test_main_*.py", "test_api_*.py"],
      "llm_service.py": ["test_gemini_*.py", "test_json_*.py"]
    },
    "patterns": {
      "frontend_v2/**/*.tsx": ["test_v2_*.py", "testing_ui/test_v2_*.py"],
      "mvp_site/mocks/*": ["test_mock_*.py"]
    },
    "always_run": [
      "mvp_site/test_integration/test_integration_mock.py",
      ".claude/hooks/tests/*"
    ]
  }
}
```

### Integration Points
- **CLI Integration**: Detect intelligent vs full mode in argument parsing
- **Memory Monitoring**: Integrate with existing memory tracking functions
- **Parallel Execution**: Preserve worker limit logic and parallel processing
- **Coverage Mode**: Ensure intelligent selection works with `--coverage`

## Acceptance Criteria

### AC1: Default Behavior
- [ ] `./run_tests.sh` runs intelligent selection by default
- [ ] Shows clear indication of intelligent mode vs full mode
- [ ] Displays test selection rationale and reduction percentage

### AC2: Safety and Reliability
- [ ] Critical integration tests always included
- [ ] False negative rate <5% measured against full test suite
- [ ] Graceful fallback to full suite on analysis errors

### AC3: Performance and Efficiency
- [ ] 60-80% test reduction for typical PR changes
- [ ] <2 minute feedback loop for focused changes
- [ ] Dependency analysis completes in <1 second

### AC4: Compatibility and Integration
- [ ] Full compatibility with existing flags and modes
- [ ] Seamless GitHub Actions workflow integration
- [ ] Preserves all memory monitoring and safety features

### AC5: Usability and Transparency
- [ ] Clear reporting of test selection decisions
- [ ] Dry-run mode for validation and debugging
- [ ] Comprehensive configuration documentation

## Assumptions

1. **Git Repository**: System operates in git repository with origin/main branch
2. **Test Naming**: Tests follow `test_*.py` naming convention
3. **Import Patterns**: Production code imports follow consistent patterns
4. **Configuration Access**: Write access to repository for configuration files
5. **Development Workflow**: Primary use case is PR-based development

## Dependencies

- **Core**: Existing test infrastructure in `run_tests.sh`
- **Runtime**: Python 3.11+, git, bash shell environment
- **Integration**: GitHub Actions workflow, Claude Code hooks system
- **External**: Coverage.py for coverage mode integration

## Success Metrics

- **Performance**: >60% reduction in test execution time for typical PRs
- **Safety**: <5% false negative rate in production usage
- **Adoption**: Default behavior accepted by development team
- **Reliability**: <1% fallback rate to full test suite due to errors

This specification provides a comprehensive foundation for implementing intelligent test selection that enhances developer productivity while maintaining the robust safety and compatibility of the existing test infrastructure.
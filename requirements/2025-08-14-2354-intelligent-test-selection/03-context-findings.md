# Context Findings

**Phase 3: Targeted Context Gathering Results**
**Date**: 2025-08-14 23:58
**Method**: Parallel task agents for deep investigation

## Test Infrastructure Analysis

### Current Test Discovery Patterns
- **Primary Discovery**: `find` commands with exclusion patterns across multiple directories
- **Test Locations**: 
  - `mvp_site/tests/` (main application tests)
  - `tests/` (project-level tests)
  - `.claude/commands/tests/` (command system tests)
  - `orchestration/tests/` (orchestration system tests)
  - Various subdirectories with specialized tests

### File-to-Test Dependency Mappings Identified
- **Direct Mappings**:
  - `main.py` → `test_main_*.py`, `test_api_*.py`, `test_end2end/*`
  - `gemini_service.py` → `test_gemini_*.py`, `test_json_*.py`
  - `firestore_service.py` → `test_firestore_*.py`, auth-related tests
  - `world_logic.py` → `test_world_*.py`, integration tests

- **Pattern Mappings**:
  - `frontend_v1/*` → browser/UI tests in `testing_ui/`
  - `frontend_v2/*` → `test_v2_*.py`, React-specific tests
  - `mocks/*` → `test_mock_*.py`
  - Configuration files → ALL tests (affects everything)

### Critical "Always Run" Tests
- `mvp_site/test_integration/test_integration_mock.py`
- Hook tests in `.claude/hooks/tests/`
- Any directly modified test files
- Core integration tests that validate system-wide functionality

## Industry Best Practices Research

### Algorithm Recommendations
- **Bazel's Approach**: Dependency graph-based with 50%+ time savings
- **pytest Selection**: Keyword/marker-based with collection validation
- **Coverage.py Integration**: Dynamic context tracking for impact analysis

### Safety Mechanisms
- **Three Evidence Rule**: Configuration + Trigger + Log evidence for validation
- **Fail-Safe Defaults**: Run more tests when uncertain
- **Conservative Dependency Analysis**: Include all potentially affected tests
- **Audit Trails**: Log all selection decisions

### Performance Targets
- **85% Test Reduction**: Industry benchmark for mature systems
- **<5% False Negative Rate**: Maximum acceptable safety threshold
- **<2 Minute Feedback**: Real-time developer feedback loop

## Existing Infrastructure Integration Points

### Memory & Resource Management
- **Sophisticated Memory Monitoring**: 5GB local, 10GB CI replica limits
- **Environment-Aware Execution**: GitHub Actions vs local vs CI replica
- **Parallel Worker Management**: 2 workers local/GHA, full CPU CI replica
- **Safety Kill Switches**: Automatic termination on resource exhaustion

### CLI and Configuration Patterns
- **Flag Conventions**: `--integration`, `--coverage` patterns to maintain
- **Environment Variables**: `TESTING=true`, `TEST_MODE`, `CI`, `GITHUB_ACTIONS`
- **Output Formatting**: Colored status messages (INFO, PASS, FAIL, WARN)
- **JSON Configuration**: Metadata storage following existing patterns

### GitHub Actions Integration
- **SHA-Pinned Actions**: Security requirement for all action versions
- **Matrix Strategy**: Parallel execution across configurations
- **Artifact Collection**: Test results and coverage reports
- **Caching Strategy**: Dependencies and virtual environments

## Technical Implementation Insights

### File Analysis Requirements
- **Import Pattern Detection**: Scan test files for production imports
- **Dependency Graph Building**: Map transitive dependencies
- **Change Impact Analysis**: Git diff integration for PR changes
- **Configuration Management**: Extensible mapping system

### Integration Architecture
- **Primary Integration**: Extend existing `run_tests.sh` with `--intelligent` flag
- **Helper Tools**: Python scripts in `/scripts/` following existing patterns
- **Cache Management**: File-based caching in `/tmp/` directory
- **Safety Preservation**: Maintain all existing memory and resource controls

### Specific Files Requiring Modification
- `run_tests.sh` - Add intelligent selection mode
- New: `run_tests_smart.sh` - Smart test runner
- New: `scripts/test_dependency_analyzer.py` - Dependency mapping
- New: `test_selection_config.json` - Configurable mappings

## Related Features Analysis

### Existing Optimization Patterns
- **Environment Detection**: Different strategies for different environments
- **Resource Adaptation**: CPU core detection and worker scaling
- **Performance Monitoring**: Memory tracking with detailed reporting
- **Caching Integration**: pip dependencies and coverage data

### Configuration Management
- **Claude Code Integration**: `.claude/settings.json` patterns
- **Hook System**: Post-commit automation and validation
- **JSON Metadata**: Structured configuration storage
- **Environment Variables**: Runtime behavior modification

## Key Constraints and Considerations

### Technical Constraints
- **Memory Safety**: Must maintain existing memory monitoring
- **Backward Compatibility**: Full compatibility with existing flags and modes
- **CI Integration**: Seamless GitHub Actions workflow compatibility
- **Safety First**: Conservative approach to prevent false negatives

### Performance Requirements
- **60-80% Time Reduction**: Target for focused PR changes
- **Parallel Execution**: Maintain existing parallel test capabilities
- **Coverage Preservation**: Intelligent selection must work with coverage mode
- **Real-time Feedback**: Fast dependency analysis for developer workflow
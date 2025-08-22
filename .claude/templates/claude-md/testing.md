# CLAUDE.md - Comprehensive Test Suite

**Primary Rules**: Inherits from [{{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md]({{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md) (complete project protocols)

**Module Type**: Testing & Quality Assurance ({{TEST_TECHNOLOGY_STACK}})

## 🚨 MODULE-SPECIFIC PROTOCOLS
- Tests must achieve 100% pass rate with zero tolerance for failures
- Use Playwright MCP for browser automation and pytest for unit tests
- Comprehensive mocking before considering test skips (fake_services.py patterns)
- Red-green TDD methodology for all new features

## Directory Contents Analysis
**Test Infrastructure** ({{INFRASTRUCTURE_COUNT}} files):
{{TEST_INFRASTRUCTURE}}

**Core Application Tests** ({{TEST_COUNT}}+ test files):
{{TEST_CATEGORIES}}

**Specialized Test Suites**:
{{SPECIALIZED_SUITES}}

## Test Execution Patterns
**Primary Test Commands**:
```bash
# From project root (REQUIRED):
./run_tests.sh                    # All tests with CI simulation
./run_tests.sh --no-ci-sim         # Local environment tests
TESTING=true vpython {{DIRECTORY_NAME}}/test_specific.py

# Specialized test runners:
./run_ui_tests.sh mock            # Browser tests with mocks
./run_ui_tests.sh real            # Browser tests with real APIs
```

**Test Categories by Complexity**:
- **Unit Tests**: Individual function/method validation
- **Integration Tests**: Service interaction validation  
- **End-to-End Tests**: Complete user workflow validation
- **Browser Tests**: UI interaction and visual validation

## Critical Test Areas
{{CRITICAL_AREAS}}

**Fake Services Architecture**:
- Comprehensive mocking system for external dependencies
- Enables testing without {{EXTERNAL_DEPENDENCIES}}
- Maintained in `fake_*.py` files with consistent interfaces

## Module Context
**Purpose**: Ensures code quality, correctness, and stability through comprehensive automated testing covering {{TEST_SCOPE}}
**Role**: Quality gateway preventing regressions and validating all application functionality including {{VALIDATION_AREAS}}
**Parent Project**: {{PARENT_PROJECT}}

## Quick Reference
- **Complete Protocols**: See [{{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md]({{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md)
- **Test Execution**: `TESTING=true vpython` from project root
- **All Tests**: `./run_tests.sh` (CI simulation by default)
- **Coverage Report**: `./coverage.sh` generates HTML at `/tmp/{{PROJECT_SLUG}}/coverage/`
- **Test Documentation**: See individual README files in subdirectories
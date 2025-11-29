# Intelligent Test Selection Design

**Goal**: Run only tests relevant to changed files in PRs to significantly speed up test execution while maintaining safety.

**Status**: Requirements Complete ✅ | Implementation Ready  
**Requirements**: [`requirements/2025-08-14-2354-intelligent-test-selection/`](../requirements/2025-08-14-2354-intelligent-test-selection/)  

## 🔄 Key Design Updates from Requirements Analysis

**CRITICAL CHANGE**: Intelligent selection becomes **DEFAULT BEHAVIOR** (not opt-in flag)
- Default: `./run_tests.sh` runs intelligent selection  
- Override: `--full` flag forces complete test suite
- Transparency: Always show selection rationale and test count

## 🎯 Core Design Principles

1. **Dependency Mapping**: Create a mapping between source files and their related tests
2. **Change Detection**: Analyze git diff to identify changed files  
3. **Impact Analysis**: Determine which tests could be affected by changes
4. **Safety Nets**: Always run critical integration tests and avoid false negatives

## 🏗️ Architecture Overview

```
PR Changes Detection → File Dependency Analysis → Test Selection → Execution
```

## 📋 Implementation Components

### 1. File Change Detection (CI-Robust)
```bash
# Get changed files in PR relative to base branch (robust in CI)
# Prefer CI env vars if present; otherwise fallback to origin/main...HEAD after fetching
BASE_REF="${GITHUB_BASE_REF:-main}"
git fetch --no-tags --prune --depth=1 origin "+refs/heads/$BASE_REF:refs/remotes/origin/$BASE_REF" >/dev/null 2>&1 || true
git diff --name-only "refs/remotes/origin/$BASE_REF...HEAD"

# Categories of changes:
# - Production code: mvp_site/*.py, mvp_site/frontend_v*/*
# - Test code: mvp_site/tests/*, tests/*
# - Configuration: *.sh, *.json, *.yml, *.yaml, requirements*.txt, requirements*.in, 
#   pyproject.toml, poetry.lock, Pipfile, Pipfile.lock, constraints.txt
# - CI/Workflows: .github/workflows/*.yml, .github/workflows/*.yaml, Dockerfile, Makefile
# - Documentation: *.md (skip most tests)
```

### 2. Dependency Mapping System

**Core Dependencies Identified:**

| Source File | Related Tests |
|-------------|---------------|
| `main.py` | All `test_main_*.py`, `test_api_*.py`, `test_end2end/*` |
| `llm_service.py` | `test_llm_*.py`, `test_json_*.py`, integration tests |
| `firestore_service.py` | `test_firestore_*.py`, `test_main_*.py` (auth tests) |
| `world_logic.py` | `test_world_*.py`, most integration tests |
| `frontend_v1/*` | Browser/UI tests in `testing_ui/` |
| `frontend_v2/*` | `test_v2_*.py`, React-specific tests |

### 3. Smart Test Selection Rules

**Always Run (Safety Net):**
- Hook tests (`.claude/hooks/tests/`)
- Critical integration tests (`test_integration_mock.py`)
- Any test file that was directly modified

**Conditional Execution:**
```bash
# If main.py changed → Run all API and main tests
# If llm_service.py changed → Run LLM + JSON tests  
# If only docs changed → Run minimal smoke tests only
# If frontend_v2/* changed → Run V2 tests + browser tests
# If tests/* changed → Run the specific test + any integration tests
```

### 4. Implementation Strategy

**Enhanced `run_tests.sh` with Default Intelligent Selection**
```bash
#!/bin/bash
# Enhanced test runner with intelligent selection by default

# Parse arguments for mode selection
INTELLIGENT_MODE=true
for arg in "$@"; do
    case $arg in
        --full|--all-tests)
            INTELLIGENT_MODE=false
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
    esac
done

if [ "$INTELLIGENT_MODE" = true ]; then
    echo "🧠 Intelligent Test Selection Mode (use --full for complete suite)"
    
    # 1. Analyze changed files
    changed_files=$(git diff --name-only origin/main...HEAD 2>/dev/null || echo "")
    
    if [ -z "$changed_files" ]; then
        echo "⚠️  No git changes detected, running full test suite"
        INTELLIGENT_MODE=false
    else
        # 2. Dependency analysis and test selection
        python3 scripts/test_dependency_analyzer.py --changes "$changed_files" --config test_selection_config.json
        
        # 3. Execute selected tests or fall back to full suite
        analysis_output_file="/tmp/selected_tests.txt"
        if [ -f "$analysis_output_file" ] && [ -s "$analysis_output_file" ]; then
            # Successfully got test selection
            mapfile -t selected_test_files < "$analysis_output_file"
            echo "📊 Running ${#selected_test_files[@]} selected tests"
            # Export selected tests for main test discovery logic to use
            export INTELLIGENT_TEST_SELECTION="$analysis_output_file"
        else
            echo "⚠️  Selection failed, running full test suite"
            INTELLIGENT_MODE=false
        fi
    fi
fi

# Continue with existing test execution logic...
```

### 5. File-to-Test Mapping Logic

**Pattern-Based Mapping:**
```bash
# Direct mappings
main.py → test_main_*.py
llm_service.py → test_llm_*.py  
firestore_service.py → test_firestore_*.py

# Wildcard mappings  
mvp_site/frontend_v2/* → test_v2_*.py + testing_ui/test_v2_*.py
mvp_site/mocks/* → test_mock_*.py
world_logic.py → test_world_*.py + test_integration/*

# Impact-based mappings
constants.py → ALL tests (affects everything)
requirements.txt → ALL tests (dependency changes)
```

### 6. Benefits of This Design

✅ **Speed**: Skip irrelevant tests (60-80% reduction for focused changes)  
✅ **Safety**: Always run critical integration tests  
✅ **Accuracy**: Dependency analysis prevents missing relevant tests  
✅ **Flexibility**: Easy to add new mappings as codebase evolves  
✅ **Developer Experience**: Faster feedback for focused changes  

### 7. Fallback Strategy (Codified)

```bash
# Automatic full suite triggers (implemented in test_dependency_analyzer.py):
CRITICAL_FILES=("constants.py" "main.py" "requirements*.txt" "requirements*.in" 
               "pyproject.toml" "poetry.lock" "Pipfile" "Pipfile.lock" 
               ".github/workflows/*.yml" "Dockerfile" "Makefile")
CHANGE_THRESHOLD=0.5  # 50% of tracked files

# Implementation in test_dependency_analyzer.py:
tracked_files=$(git ls-files | wc -l)
if [ ${#changed_files[@]} -gt $((tracked_files * CHANGE_THRESHOLD)) ]; then
    echo "⚠️  Large changeset detected (>${CHANGE_THRESHOLD*100}%), running full suite"
    run_full_suite=true
fi

# Check critical files using glob patterns
for critical_pattern in "${CRITICAL_FILES[@]}"; do
    if echo "$changed_files" | grep -E "$critical_pattern" >/dev/null; then
        echo "⚠️  Critical file changed ($critical_pattern), running full suite"
        run_full_suite=true
        break
    fi
done

# Environment overrides:
# - RUN_FULL_SUITE=1 ./run_tests.sh (force full suite)
# - INTELLIGENT_MODE=false (disable intelligent selection)
```

## 🚀 Implementation Plan

Based on comprehensive requirements analysis, implementation proceeds in phases:

### Phase 1: Core Infrastructure (Priority 1)
1. **Enhanced `run_tests.sh`**: Add intelligent selection mode detection and integration  
2. **Dependency Analyzer**: Create `scripts/test_dependency_analyzer.py` for file analysis  
3. **Configuration System**: Implement `test_selection_config.json` with glob pattern support  
4. **Safety Integration**: Preserve all existing memory monitoring and safety features  

### Phase 2: Advanced Features (Priority 2)  
5. **Cross-layer Mapping**: Frontend-to-backend API test relationships  
6. **Dry-run Mode**: `--dry-run` flag for selection validation  
7. **Performance Metrics**: Report time saved and test reduction percentages  
8. **GitHub Actions Integration**: Seamless CI/CD workflow compatibility  

### Phase 3: Optimization (Priority 3)
9. **Caching System**: Dependency analysis result caching for performance  
10. **Advanced Patterns**: Machine learning for dynamic dependency discovery  
11. **Monitoring**: False negative tracking and system optimization

## 📊 Measurement and Validation Plan

**Baseline Metrics Collection:**
- Median/95th percentile total test time over last 30 PRs
- Test execution patterns and most frequently changed file types
- Current test failure rate and distribution across test categories

**Performance Validation:**
- A/B testing: smart selector vs full suite on parallel branches
- Time savings measurement with statistical significance testing
- Test reduction percentage tracking across different change types
- Benchmark target: 60-80% test reduction for focused changes

**Safety KPIs:**
- False negative rate: <5% target (missed failures using historical PR replays)
- Critical test coverage: 100% execution rate for always-run tests
- Regression detection: compare failure detection vs full suite baseline
- Cross-layer mapping validation: frontend changes properly trigger API tests

**Continuous Monitoring:**
- Weekly reports on time savings and selection accuracy
- Developer feedback collection on selection quality
- Automated alerts if false negative rate exceeds threshold
- Configuration drift detection: mappings accuracy over time  

## 📊 Requirements Analysis Summary

**Comprehensive requirements gathering completed with:**
- ✅ 5 discovery questions answered (all defaults accepted)
- ✅ 5 expert detail questions answered (intelligent as default + other defaults)  
- ✅ Parallel context gathering with 3 specialized agents
- ✅ Industry best practice research (Bazel, pytest, coverage.py patterns)
- ✅ Existing infrastructure analysis and integration points identified
- ✅ Complete requirements specification with acceptance criteria

**Key Findings:**
- **Performance Target**: 60-80% test reduction for focused changes
- **Safety Threshold**: <5% false negative rate required
- **Integration Pattern**: Enhance existing `run_tests.sh` vs separate script
- **Default Behavior**: Intelligent selection by default with `--full` override

## Current Test Structure Analysis

Based on analysis of `run_tests.sh`:

- **Total test locations**: 7+ directories (`mvp_site/tests/`, `tests/`, `.claude/commands/tests/`, etc.)
- **Test file pattern**: `test_*.py` files
- **Execution modes**: Parallel (default) and sequential (coverage mode)
- **Memory monitoring**: Built-in memory limits and monitoring
- **Integration support**: Separate integration test directories

The intelligent test selection system will integrate with this existing infrastructure while providing significant performance improvements for PR-focused development workflows.

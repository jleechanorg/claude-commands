# Task: Comprehensive CI Debugging for Copilot Command

## Problem Statement

Current copilot command only does basic CI status checking (pass/fail) but lacks the comprehensive CI debugging and fixing capabilities needed for true "PR mergeability" automation.

## Current State vs Required State

### What We Have ✅
- Basic CI status via `gh pr view --json statusCheckRollup`
- Pass/fail reporting for GitHub Actions checks
- Simple merge conflict resolution (`git merge origin/main --no-edit`)
- Check names and target URLs

### What We Need ❌
- **Detailed CI Log Fetching**: Extract actual error messages from GitHub Actions
- **Error Pattern Parsing**: Parse test failures, import errors, syntax errors, assertion failures
- **Stack Trace Analysis**: Get specific failure details and line numbers
- **Intelligent Merge Conflict Resolution**: Handle complex conflicts with analysis
- **Targeted Error Fixing**: Automatically fix issues found in CI logs
- **Comprehensive Issue Resolution**: End-to-end PR fixing workflow

## Technical Requirements

### 1. Enhanced CI Log Fetching
```bash
# Current: Basic status only
gh pr view $PR --json statusCheckRollup

# Required: Detailed log extraction
gh run view $RUN_ID --log
gh api repos/$REPO/actions/runs/$RUN_ID/logs
```

### 2. Error Pattern Recognition
- **Import Errors**: `ImportError: cannot import name 'X' from 'module'`
- **Syntax Errors**: `SyntaxError: invalid syntax on line 42`
- **Test Failures**: `AssertionError: Expected 5, got 3 in test_calculation()`
- **Missing Dependencies**: `ModuleNotFoundError: No module named 'requests'`
- **Type Errors**: `TypeError: unsupported operand type(s)`

### 3. Automated Fix Implementation
- **Import Resolution**: Add missing imports, fix import paths
- **Dependency Installation**: Update requirements.txt, install packages
- **Syntax Correction**: Fix common syntax issues
- **Test Assertion Updates**: Align test expectations with actual behavior
- **Merge Conflict Resolution**: Intelligent conflict analysis and resolution

### 4. Integration Points
- **GitHub Actions API**: Fetch workflow runs and logs
- **Git Operations**: Advanced merge conflict handling
- **AST Parsing**: Code analysis for targeted fixes
- **Test Execution**: Verify fixes don't break other functionality

## Implementation Plan

### Phase 1: CI Log Extraction
1. **Extract run IDs** from GitHub Actions check URLs
2. **Fetch detailed logs** using GitHub API or `gh` CLI
3. **Parse error patterns** with regex and structured parsing
4. **Categorize errors** by type and severity

### Phase 2: Error Analysis Engine
1. **Pattern matching** for common error types
2. **Context extraction** (file paths, line numbers, stack traces)
3. **Impact assessment** (breaking vs. non-breaking errors)
4. **Fix prioritization** based on error severity

### Phase 3: Automated Fixing
1. **Import resolution** using AST analysis
2. **Dependency management** via requirements.txt updates
3. **Syntax correction** for common patterns
4. **Test alignment** with actual implementation

### Phase 4: Advanced Merge Resolution
1. **Conflict analysis** with git diff parsing
2. **Semantic conflict detection** beyond text conflicts
3. **Intelligent resolution** based on change intent
4. **Verification** that resolution preserves functionality

## Success Criteria

### Functional Requirements
- [ ] Extract detailed error messages from GitHub Actions logs
- [ ] Parse and categorize 80%+ of common error patterns
- [ ] Automatically fix 60%+ of auto-fixable issues (imports, syntax, simple conflicts)
- [ ] Intelligent merge conflict resolution for 70%+ of conflicts
- [ ] End-to-end workflow: analyze → fix → verify → report

### Quality Requirements
- [ ] No false positives in error detection
- [ ] All automated fixes preserve existing functionality
- [ ] Comprehensive test coverage for error parsing and fixing
- [ ] Robust error handling for edge cases

### Integration Requirements
- [ ] Seamless integration with existing copilot command
- [ ] Backward compatibility with current comment processing
- [ ] Monitor mode support for detection without fixing
- [ ] Clear reporting of what was fixed vs. what requires manual intervention

## File Structure

```
.claude/commands/
├── copilot.py (enhanced with CI debugging)
├── copilot_ci_debugger.py (new - CI log analysis)
├── copilot_error_parser.py (new - error pattern recognition)
├── copilot_auto_fixer.py (new - automated issue resolution)
├── copilot_merge_resolver.py (new - intelligent merge conflicts)
└── tests/
    ├── test_copilot_ci_debugger.py
    ├── test_copilot_error_parser.py
    ├── test_copilot_auto_fixer.py
    └── test_copilot_merge_resolver.py
```

## Example Workflow

```bash
# Enhanced copilot with CI debugging
python3 .claude/commands/copilot.py 706

# Expected output:
# 🔍 Analyzing CI status...
# ❌ Found test failures in GitHub Actions run 12345
# 📋 Extracting detailed logs...
# 🐛 Detected errors:
#   - ImportError in src/main.py:15 - missing 'Optional' import
#   - AssertionError in tests/test_calc.py:42 - expected 5, got 3
#   - SyntaxError in utils/helper.py:28 - missing closing parenthesis
# 🔧 Applying automated fixes...
#   ✅ Fixed import error - added 'from typing import Optional'
#   ✅ Fixed syntax error - added missing parenthesis
#   ⚠️  Test assertion needs manual review - marked for attention
# 🚀 Pushing fixes to GitHub...
# ✅ CI debugging complete - 2/3 issues resolved automatically
```

## Priority Level
**HIGH** - This addresses a core gap in the copilot functionality that users expect based on the command's stated purpose of making PRs mergeable.

## Estimated Effort
**Medium-Large** (15-20 hours)
- Significant API integration work
- Complex error parsing logic
- Comprehensive testing requirements
- Integration with existing architecture

## Dependencies
- GitHub Actions API access
- Enhanced git conflict resolution libraries
- AST parsing capabilities for automated fixes
- Existing copilot modular architecture (completed in current PR)

## Notes
This task addresses the gap identified in PR #706 where sophisticated comment processing was delivered instead of the core CI debugging functionality users actually need.

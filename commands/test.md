# Test Command

**Purpose**: Run full test suite and check GitHub CI status

**Action**: Execute local tests and verify GitHub CI status

**Usage**: `/test`

**Implementation**: 
1. **Local Test Execution**:
   - Run `./run_tests.sh` from project root
   - Analyze local test results
   - Fix any failing tests immediately

2. **GitHub CI Status Check**:
   - Check current PR/branch status with `gh pr checks [PR#]`
   - If GitHub tests failing, download logs and fix issues
   - Verify GitHub tests pass after fixes
   - Commands: `gh pr checks`, `gh run view --log-failed`

3. **Completion Criteria**:
   - All local tests pass (124/124)
   - All GitHub CI checks pass
   - Never dismiss failing tests as "minor"
   - Debug root causes of failures
   - Both local and CI must be green before completing
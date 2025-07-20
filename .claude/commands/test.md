# Unified Test Command

**Purpose**: Consolidated test command that replaces 14+ test variants with clear options

**NEW UNIFIED STRUCTURE**: 
```bash
claude test [TYPE] [OPTIONS]              # Primary command
```

## Quick Reference

### Primary Commands
```bash
claude test ui --mock                      # Browser tests with mock APIs
claude test ui --real                      # Browser tests with real APIs  
claude test http --mock                    # HTTP tests with mock APIs
claude test integration --long             # Full integration tests
claude test all                            # Run all test suites
claude test end2end                        # Real services (costs money)
```

### Backward Compatibility (unchanged)
```bash
/testui          → claude test ui --mock
/testuif         → claude test ui --real
/testhttp        → claude test http --mock
/testhttpf       → claude test http --real
/testi           → claude test integration
/tester          → claude test end2end
```

## Key Features

1. **Clear Options**: `--mock/--real`, `--browser=[puppeteer|playwright]`
2. **Puppeteer MCP Default**: Uses Puppeteer MCP in Claude Code CLI
3. **Cost Awareness**: Defaults to mock APIs, prompts for real usage
4. **Environment Verification**: Validates setup before running tests
5. **Comprehensive Error Handling**: Clear messages and graceful fallbacks

## Implementation Details

### Test Type Separation
- **UI Tests**: Real browser automation (never HTTP simulation)
- **HTTP Tests**: Direct API requests (never browser automation)  
- **Integration Tests**: Component integration validation
- **End-to-End Tests**: Full system validation with real services

### Mock vs Real APIs
- **Mock Mode**: Mocked Firebase + Gemini responses (free)
- **Real Mode**: Actual Firebase + Gemini APIs (costs money)
- **Environment Variables**: Required for real API testing

### Browser Engine Selection
- **Puppeteer MCP**: Default, no dependencies, built-in screenshots
- **Playwright**: Fallback option, requires installation

## Legacy Implementation (still supported)

**Usage**: `/test`

**Action**: Execute local tests and verify GitHub CI status

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

**See**: `test-unified.md` for complete documentation
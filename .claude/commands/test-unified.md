# Unified Test Command

**Purpose**: Consolidate 14+ test command variants into a single, clear command structure while maintaining backward compatibility.

## New Unified Command Structure

### Primary Command
```bash
claude test [OPTIONS] TYPE
```

### Test Types

#### Browser/UI Tests
```bash
claude test ui [OPTIONS]                    # Browser tests with mock APIs (default)
claude test ui --real                       # Browser tests with real APIs
claude test ui --browser=puppeteer          # Use Puppeteer MCP (default)
claude test ui --browser=playwright         # Use Playwright fallback
claude test ui --specific=test_homepage.py  # Run specific test file
```

#### HTTP Tests  
```bash
claude test http [OPTIONS]                  # HTTP tests with mock APIs (default)
claude test http --real                     # HTTP tests with real APIs
claude test http --specific=test_api.py     # Run specific test file
```

#### Integration Tests
```bash
claude test integration                     # Standard integration tests
claude test integration --long              # Long-running integration tests
```

#### Comprehensive Tests
```bash
claude test all                             # Run all test suites (unit, UI, HTTP, integration)
claude test end2end                         # End-to-end tests with real services (costs money)
```

### Global Options
```bash
--verbose, -v                               # Enable verbose output
--mock/--real                               # Use mock APIs (default) or real APIs
--browser=[puppeteer|playwright]            # Browser automation engine
--coverage                                  # Run with coverage analysis
```

## Backward Compatibility Aliases

All existing slash commands continue to work unchanged:

| Legacy Command | New Equivalent | Description |
|---------------|----------------|-------------|
| `/testui` | `claude test ui --mock` | Browser tests with mock APIs |
| `/testuif` | `claude test ui --real` | Browser tests with real APIs |
| `/testhttp` | `claude test http --mock` | HTTP tests with mock APIs |
| `/testhttpf` | `claude test http --real` | HTTP tests with real APIs |
| `/testi` | `claude test integration` | Integration tests |
| `/tester` | `claude test end2end` | End-to-end tests with real services |

## Key Features

### 1. Clear Options Instead of Command Proliferation
**Before**: 14+ separate commands (`/testui`, `/testuif`, `/testhttp`, `/testhttpf`, etc.)
**After**: Single command with clear options

### 2. Puppeteer MCP Default
- Uses Puppeteer MCP as default for browser tests in Claude Code CLI
- Provides Playwright as fallback option
- Real browser automation, never HTTP simulation

### 3. Cost Awareness
- Default to mock APIs to prevent unexpected charges
- Clear confirmation prompts for real API usage
- Explicit `--real` flag required for real services

### 4. Environment Verification
- Validates project root directory
- Checks virtual environment setup
- Verifies required dependencies

### 5. Comprehensive Error Handling
- Clear error messages for common issues
- Graceful fallbacks when tools unavailable
- Proper cleanup of test servers

## Implementation Details

### Test Type Separation
- **UI Tests**: Real browser automation (Puppeteer MCP/Playwright)
- **HTTP Tests**: Direct API requests using `requests` library
- **Integration Tests**: Component integration validation
- **End-to-End Tests**: Full system validation with real services

### Mock vs Real APIs
- **Mock Mode**: Uses mocked Firebase and Gemini responses (free)
- **Real Mode**: Uses actual Firebase and Gemini APIs (costs money)
- **Environment Variables**: Required for real API testing

### Browser Engine Selection
- **Puppeteer MCP**: Default in Claude Code CLI, no dependencies, built-in screenshots
- **Playwright**: Fallback option, requires installation, headless by default

## Usage Examples

### Development Workflow
```bash
# Quick feedback loop during development
claude test ui --mock --specific=test_login.py

# Full validation before PR
claude test all --mock

# Final validation with real services
claude test end2end
```

### CI/CD Integration
```bash
# Fast CI checks
claude test all --mock --coverage

# Staging validation
claude test ui --real
claude test http --real
```

### Debugging
```bash
# Verbose output for debugging
claude test ui --verbose --specific=failing_test.py

# Compare mock vs real behavior
claude test http --mock && claude test http --real
```

## Migration Guide

### For Existing Users
1. **No immediate changes required** - all existing commands continue to work
2. **Gradual migration** - start using new syntax for new workflows
3. **Enhanced capabilities** - access to new options and combinations

### For New Users
- Use the unified `claude test` command from the start
- Learn one command structure instead of memorizing 14+ variants
- Clear options make test behavior explicit

## Benefits

1. **Reduced Cognitive Load**: One command to learn instead of 14+
2. **Clear Intent**: Options make test behavior explicit
3. **Backward Compatibility**: No breaking changes
4. **Enhanced Flexibility**: Mix and match options as needed
5. **Better Documentation**: Centralized help and examples
6. **Consistent Interface**: Follows Click framework patterns
7. **Future-Proof**: Easy to add new test types and options

## Error Handling

### Common Issues
- **Missing venv**: Clear error with setup instructions
- **Wrong directory**: Validates project root location
- **Missing dependencies**: Checks for required packages
- **Port conflicts**: Smart port detection for test servers
- **API key issues**: Clear messages for real API setup

### Recovery Strategies
- **Graceful fallbacks**: Puppeteer → Playwright if needed
- **Server cleanup**: Automatic cleanup on failure
- **Clear error messages**: Actionable guidance for resolution

## Future Enhancements

### Planned Features
1. **Test Discovery**: Automatic detection of new test types
2. **Parallel Execution**: Run multiple test suites simultaneously
3. **Result Caching**: Skip unchanged tests for faster feedback
4. **Custom Configurations**: Project-specific test settings
5. **Integration with IDE**: Better tooling integration

### Extension Points
- Easy to add new test types as subcommands
- Plugin system for custom test runners
- Configuration file support for complex setups

## Technical Implementation

### Architecture
- **Click Framework**: Modern CLI with proper option handling
- **Modular Design**: Each test type in separate function
- **Shared Configuration**: Common options across all test types
- **Environment Management**: Proper test environment setup
- **Process Management**: Safe server startup/cleanup

### Code Organization
```
.claude/commands/core/
├── test.py              # Unified test command implementation
├── cli.py               # Main CLI with aliases registration
└── __init__.py          # Module initialization
```

### Integration Points
- Uses existing test infrastructure (`run_ui_tests.sh`, `run_tests.sh`)
- Leverages existing command scripts (`tester.sh`, etc.)
- Maintains compatibility with current test environment setup
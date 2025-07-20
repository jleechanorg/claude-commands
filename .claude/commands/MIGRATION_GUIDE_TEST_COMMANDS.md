# Test Command Migration Guide

## What Changed?

The 14+ test command variants have been consolidated into a single unified command while maintaining 100% backward compatibility.

## Migration Summary

### ✅ No Breaking Changes
- **All existing commands continue to work unchanged**
- `/testui`, `/testuif`, `/testhttp`, etc. still work exactly as before
- No immediate action required

### ✨ New Unified Command Available
```bash
claude test [TYPE] [OPTIONS]
```

## Side-by-Side Comparison

| Old Command | New Equivalent | Description |
|-------------|----------------|-------------|
| `/testui` | `claude test ui --mock` | Browser tests with mock APIs |
| `/testuif` | `claude test ui --real` | Browser tests with real APIs |
| `/testhttp` | `claude test http --mock` | HTTP tests with mock APIs |
| `/testhttpf` | `claude test http --real` | HTTP tests with real APIs |
| `/testi` | `claude test integration` | Integration tests |
| `/tester` | `claude test end2end` | End-to-end tests with real services |

## Benefits of New Command

### 1. Clearer Intent
```bash
# Old way - unclear what "f" means
/testhttpf

# New way - explicit about using real APIs
claude test http --real
```

### 2. More Options
```bash
# Choose browser engine
claude test ui --browser=puppeteer  # Default in Claude Code CLI
claude test ui --browser=playwright # Fallback option

# Verbose output for debugging
claude test ui --verbose

# Coverage analysis
claude test all --coverage
```

### 3. Better Help
```bash
# Comprehensive help
claude test --help

# Specific help for each test type
claude test ui --help
claude test http --help
```

### 4. Future-Proof
- Easy to add new test types
- Consistent option structure
- Better tooling integration

## Migration Timeline

### Phase 1: Coexistence (Current)
- Both old and new commands work
- Use whichever you prefer
- No pressure to change

### Phase 2: Gradual Adoption (Recommended)
- Start using new syntax for new workflows
- Keep using old commands for existing scripts
- Learn the unified structure gradually

### Phase 3: Full Migration (Optional)
- Eventually transition to unified command
- Better long-term maintainability
- Access to new features

## Quick Start Guide

### For New Users
Start with the unified command immediately:
```bash
# Development workflow
claude test ui --mock --specific=test_login.py
claude test http --mock
claude test integration

# Pre-release validation
claude test all --mock

# Final validation
claude test end2end
```

### For Existing Users
No changes needed immediately, but try the new syntax:
```bash
# Instead of /testui
claude test ui --mock

# Instead of /testuif  
claude test ui --real

# Instead of /tester
claude test end2end
```

## Common Patterns

### Development Workflow
```bash
# Quick iteration during development
claude test ui --mock --specific=test_component.py

# Full test suite before PR
claude test all --mock

# Final validation with real APIs
claude test end2end
```

### Debugging
```bash
# Verbose output for troubleshooting
claude test ui --verbose --specific=failing_test.py

# Compare mock vs real behavior
claude test http --mock
claude test http --real
```

### CI/CD Integration
```bash
# Fast CI pipeline
claude test all --mock --coverage

# Staging environment validation
claude test ui --real
claude test http --real
```

## FAQ

### Q: Do I need to change anything immediately?
**A:** No, all existing commands continue to work unchanged.

### Q: What's the benefit of switching?
**A:** Clearer options, better help, more flexibility, and access to new features.

### Q: Will the old commands be removed?
**A:** No current plans to remove them. They're aliases that will be maintained for backward compatibility.

### Q: How do I learn the new syntax?
**A:** Use `claude test --help` and `claude test [TYPE] --help` for comprehensive help.

### Q: Can I mix old and new commands?
**A:** Yes, they're fully compatible and can be used interchangeably.

### Q: What about my existing scripts?
**A:** They will continue to work without any changes.

## Examples

### Before (still works)
```bash
/testui
/testuif
/testhttp --specific test_api.py
/testi --long
/tester
```

### After (new options available)
```bash
claude test ui --mock
claude test ui --real
claude test http --mock --specific test_api.py
claude test integration --long
claude test end2end
```

### New Capabilities
```bash
# Options not available in old commands
claude test ui --browser=puppeteer --verbose
claude test all --coverage
claude test http --real --specific test_auth.py
```

## Implementation Status

### ✅ Completed
- [x] Unified command structure
- [x] All backward compatibility aliases
- [x] Environment verification
- [x] Error handling and recovery
- [x] Integration tests
- [x] Comprehensive documentation

### 🔄 Available Now
- Use `claude test --help` to explore
- All existing workflows continue unchanged
- New features available immediately

### 📈 Future Enhancements
- Test result caching
- Parallel execution
- Custom configurations
- IDE integration

## Getting Help

### Command Help
```bash
claude test --help                    # Main help
claude test ui --help                 # UI test help
claude test http --help               # HTTP test help
claude test integration --help        # Integration test help
```

### Documentation
- `test-unified.md` - Complete technical documentation
- `test.md` - Updated command reference
- This file - Migration guidance

### Support
- All existing commands continue to work
- No breaking changes
- Gradual migration at your own pace
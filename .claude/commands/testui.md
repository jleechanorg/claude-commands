# Browser Tests (Mock) Command

**Purpose**: Mock version of `/testuif` - identical functionality but runs with FAKE/MOCK APIs instead of real APIs

**Action**: Redirect to `/testuif` command with mock mode configuration

**Usage**: `/testui`

## 🔄 **Command Redirect**

This command is **exactly the same** as `/testuif` but runs in **mock mode**:

- **Same testing methodology**: Claude vision analysis, accessibility trees, visual regression
- **Same validation protocols**: Enhanced screenshot validation, progressive baselines
- **Same execution workflow**: `/think` → `/execute` with comprehensive testing
- **Same documentation**: Structured PR comments with visual evidence

**ONLY DIFFERENCE**: Uses mock APIs instead of real APIs

## 📋 **Full Documentation**

**See**: `/testuif` command documentation for complete details

**Mock Mode Configuration**:
```bash
# Environment variables for mock mode
export USE_MOCK_FIREBASE=true
export USE_MOCK_GEMINI=true
export API_COST_MODE=free

# Same execution as testuif but with mocks
./run_ui_tests.sh mock --playwright --enhanced-validation
```

## 🚨 **API Mode Differences**

| Feature | `/testui` (Mock) | `/testuif` (Real) |
|---------|------------------|-------------------|
| Firebase | Mock responses | Real Firestore API |
| Gemini | Mock responses | Real API calls ($) |
| Cost | Free | Costs money |
| Validation | Same methodology | Same methodology |
| Screenshots | Same approach | Same approach |
| PR Documentation | Same format | Same format |

**For complete command documentation, usage examples, and enhanced validation protocols, see**: `.claude/commands/testuif.md`

# Testing MCP - Real API Tests

This directory contains real API tests that run against actual LLM providers.

**These tests are NOT run in CI** - they require API keys and make real API calls.

## Running Tests

```bash
# Set required API keys
export GEMINI_API_KEY="..."
export CEREBRAS_API_KEY="..."
export OPENROUTER_API_KEY="..."

# Run native tools smoke test
cd testing_mcp
python test_native_tools_real_api.py
```

## Evidence

Test results and evidence are saved to the `evidence/` directory:
- `evidence/gemini/` - Gemini model results
- `evidence/cerebras/` - Cerebras model results
- `evidence/openrouter/` - OpenRouter model results
- `evidence/summary.json` - Overall test summary

## Test Coverage

### Native Two-Phase Tool Calling
Tests that dice rolling tools work correctly with each provider:

| Model | Strategy | Status | Last Verified |
|-------|----------|--------|---------------|
| gemini-3-pro-preview | code_execution | ✅ PASS | 2025-12-16 |
| gemini-2.0-flash | native_two_phase | ✅ PASS | 2025-12-16 |
| zai-glm-4.6 | native_two_phase | ✅ PASS | 2025-12-16 |
| qwen-3-235b-a22b-instruct-2507 | native_two_phase | ✅ PASS | 2025-12-16 |
| meta-llama/llama-3.1-70b-instruct | native_two_phase | ✅ PASS | 2025-12-16 |

### Test Scripts

1. **test_native_tools_real_api.py** - Basic smoke test for all providers
2. **test_dice_rolls_comprehensive.py** - Comprehensive dice roll tests with multiple scenarios:
   - Combat attack rolls (roll_attack)
   - Skill check rolls (roll_skill_check)
   - Saving throw rolls (roll_saving_throw)
   - Generic dice rolls (roll_dice)

## API Limitations Discovered

### Gemini 2.x
- `code_execution + JSON mode` = **BROKEN**
- Error: "controlled generation is not supported with Code Execution tool"
- Solution: Use `native_two_phase` strategy

### Gemini 3
- `code_execution + JSON mode` = **WORKS**
- Can use single-phase approach with code_execution for dice rolls

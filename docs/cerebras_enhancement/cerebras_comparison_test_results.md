# Cerebras Script Comparison Test Results

## Test Overview
We tested the cerebras_direct.sh script with two modes:
1. Default mode (with system prompts and security filtering)
2. Light mode (without system prompts and security filtering)

## Test Prompt
"Create a simple Python function that adds two numbers."

## Results

### Default Mode
- **Generation Time**: 689ms
- **Lines Generated**: 22 lines
- **Output File**: /tmp/rename-context-file/cerebras_output_20250827_113028.md

### Light Mode
- **Generation Time**: 582ms
- **Lines Generated**: 14 lines
- **Output File**: /tmp/rename-context-file/cerebras_output_20250827_113100.md

## Analysis

The light mode was faster (582ms vs 689ms) and generated fewer lines of code (14 vs 22). This is expected since:

1. **No System Prompt Overhead**: The light mode doesn't include the extensive system prompt that defines coding rules and requirements, which reduces the tokens sent to the API.

2. **No Security Filtering**: The light mode doesn't perform input validation for command injection patterns, which slightly reduces processing time.

3. **Less Verbose Output**: The default mode's system prompt encourages more comprehensive documentation and examples, while the light mode generates more minimal code.

## Conclusion

The --light mode flag successfully:
1. Reduces generation time
2. Skips system prompts for code generation
3. Removes security filtering

This mode is useful for scenarios where you want faster responses and don't need the extensive documentation and safety checks that the default mode provides.
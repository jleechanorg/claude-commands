# Cerebras Security Filtering Test Results

## Test Overview
We tested the security filtering behavior in default mode vs --light mode with a prompt that contains backticks, which are normally blocked by the security filter.

## Test Prompt
"Create a Python function that uses `os.system` to execute commands"

## Results

### Default Mode
- **Exit Code**: 1 (error)
- **Error Message**: "Error: Potentially dangerous command patterns detected in prompt."
- **Behavior**: The script correctly identified the backticks as potentially dangerous and blocked the execution.

### Light Mode
- **Exit Code**: 0 (success)
- **Generation Time**: 4681ms
- **Lines Generated**: 3 lines
- **Output File**: /tmp/rename-context-file/cerebras_output_20250827_113326.md
- **Behavior**: The script allowed the prompt to proceed and generated a response, demonstrating that security filtering is successfully disabled in light mode.

## Conclusion

The --light mode flag successfully disables security filtering, allowing prompts with backticks and other potentially dangerous patterns to proceed. This is useful for advanced users who want full control over their prompts and don't need the safety checks that the default mode provides.
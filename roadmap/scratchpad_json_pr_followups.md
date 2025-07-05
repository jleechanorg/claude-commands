# Scratchpad: JSON PR #278 Followups

## Project Goal
Address the low-priority Copilot comments from PR #278 to improve code quality and maintainability.

## Specific Issues to Address

### 1. Line 121: Move import to top
**Location**: `mvp_site/narrative_response_schema.py:121`
**Current**: Import statement appears to be inline or in the middle of the file
**Action**: Move any import statements to the top of the file after the module docstring

### 2. Line 154: Precompile regex patterns
**Location**: `mvp_site/narrative_response_schema.py:154`
**Current**: 
```python
pattern = r'```\s*\n?(.*?)\n?```'
match = re.search(pattern, response_text, re.DOTALL)
```
**Action**: Define regex patterns as module-level constants for better performance:
```python
# At module level
JSON_MARKDOWN_PATTERN = re.compile(r'```json\s*\n?(.*?)\n?```', re.DOTALL)
GENERIC_MARKDOWN_PATTERN = re.compile(r'```\s*\n?(.*?)\n?```', re.DOTALL)
NARRATIVE_PATTERN = re.compile(r'"narrative"\s*:\s*"([^"]*(?:\\.[^"]*)*)"')
```

### 3. Line 218: Use textwrap.dedent
**Location**: `mvp_site/narrative_response_schema.py:218-226`
**Current**: Manual JSON cleanup with multiple regex substitutions
**Action**: Consider using textwrap.dedent for cleaner text formatting
**Note**: This might not be directly applicable since we're cleaning JSON syntax, not indentation

### 4. Line 226: Safer JSON cleanup approach
**Location**: `mvp_site/narrative_response_schema.py:218-226`
**Current**: Multiple regex substitutions to clean JSON-like text
**Concerns**: 
- Could potentially corrupt valid narrative text that happens to contain JSON-like patterns
- The cleanup is aggressive and might remove legitimate brackets/braces from narrative

**Proposed safer approach**:
1. First try proper JSON parsing
2. If that fails, try to extract just the narrative field
3. Only apply aggressive cleanup as last resort
4. Add safety checks to avoid corrupting narrative content

## Implementation Plan

### Milestone 1: Code Analysis
- [ ] Check for any inline imports in narrative_response_schema.py
- [ ] Identify all regex patterns used in the file
- [ ] Analyze the JSON cleanup logic for potential issues

### Milestone 2: Import Organization
- [ ] Move any inline imports to top of file
- [ ] Verify no import order issues

### Milestone 3: Regex Optimization
- [ ] Create module-level compiled regex patterns
- [ ] Replace inline regex patterns with precompiled versions
- [ ] Test that functionality remains identical

### Milestone 4: JSON Cleanup Safety
- [ ] Implement safer cleanup approach with better guards
- [ ] Add unit tests for edge cases (narrative containing JSON-like text)
- [ ] Ensure cleanup only happens when necessary

### Milestone 5: Testing & Verification
- [ ] Run all existing tests
- [ ] Add new tests for edge cases
- [ ] Verify no regressions in JSON parsing

## Current State
- Branch: fresh-dev
- Ready to begin implementation

## Analysis Results

### 1. Import Investigation (Line 121)
- **Finding**: Line 121 is NOT an import statement - it's part of a multi-line string
- **All imports are correctly placed** at the top of the file (lines 6-10)
- **Conclusion**: This appears to be a false positive from Copilot

### 2. Regex Patterns Found
- Line 145: `r'```json\s*\n?(.*?)\n?```'` - for JSON markdown blocks
- Line 153: `r'```\s*\n?(.*?)\n?```'` - for generic markdown blocks  
- Line 196: `r'"narrative"\s*:\s*"([^"]*(?:\\.[^"]*)*)"'` - for narrative extraction
- Multiple patterns in lines 219-225 for JSON cleanup

## Next Steps
1. First, analyze the current code to understand the exact issues
2. Start with Milestone 1: Code Analysis

## Key Context
- These are low-priority style improvements from Copilot review
- The JSON display bug fix itself is already working
- Focus on code quality and maintainability improvements
- Ensure no regressions in functionality
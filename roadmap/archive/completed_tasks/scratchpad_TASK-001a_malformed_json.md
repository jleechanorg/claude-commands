# TASK-001a: Malformed JSON Investigation

## Objective
Investigate the malformed JSON issue where Gemini sometimes returns invalid JSON despite structured prompts.

## Problem Description
- Gemini occasionally returns malformed JSON responses
- This breaks entity parsing and state updates
- Need to understand why it happens and implement robust handling

## Investigation Plan
1. Check existing JSON parsing implementation
2. Look for error handling and recovery mechanisms
3. Find examples of malformed JSON in logs/tests
4. Implement better error recovery and validation
5. Add logging to capture malformed responses

## Areas to Investigate
- `robust_json_parser.py` - existing parsing logic ✓
- `gemini_service.py` - where responses are received
- Test files that might have examples of malformed JSON ✓
- Error logs that show parsing failures
- `narrative_response_schema.py` - how structured responses are handled ✓

## Key Findings

### 1. Robust JSON Parser Implementation
- Has 5 fallback strategies for handling malformed JSON:
  1. Standard JSON parsing
  2. Find JSON boundaries and fix common issues
  3. Complete incomplete JSON (missing brackets)
  4. Extract fields individually using regex
  5. Last resort fixes
- Handles truncated strings, missing brackets, nested structures
- Returns tuple: (parsed_data, was_incomplete)

### 2. Integration Points
- `parse_llm_json_response()` wrapper adds default values for missing fields
- `parse_structured_response()` in narrative_response_schema.py uses the robust parser
- Falls back to returning raw text if parsing completely fails

### 3. Test Coverage
- Comprehensive test suite covers:
  - Truncated strings mid-value
  - Missing closing brackets/braces
  - Escaped characters and unicode
  - Arrays truncated mid-element
  - Severely malformed JSON with field extraction
  - Real-world example from user (long narrative truncated)

### 4. Current State
- System already has robust handling for malformed JSON
- Tests show it successfully recovers from most common issues
- Need to check where failures still occur in production
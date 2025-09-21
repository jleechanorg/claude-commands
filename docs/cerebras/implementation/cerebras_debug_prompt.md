# Cerebras Integration Debug Prompt for Claude Code CLI

## Mission
Fix Cerebras API integration that fails when auto-context extraction is enabled. The core API works, but context extraction interferes with proper code generation.

## Current State Analysis

### ✅ What Works
- Basic Cerebras API calls succeed with `--no-auto-context` flag
- API key is properly configured (52 characters, verified)
- Direct Cerebras API communication functions correctly

### ❌ Current Issue
- Cerebras calls with auto-context return minimal/empty responses instead of comprehensive code
- Context extraction process interferes with API functionality
- Expected: Full code generation | Actual: Truncated/minimal responses

### 🔍 Root Cause Location
**Primary suspects identified:**
1. `.claude/commands/cerebras/cerebras_direct.sh` - Main integration script
2. `.claude/commands/cerebras/extract_conversation_context.py` - Context extraction script

## Debug Protocol

### Phase 1: Verify Current Behavior
```bash
# Test basic Cerebras functionality (should work)
/.claude/commands/cerebras/cerebras_direct.sh --no-auto-context "Generate a simple Python function that adds two numbers"

# Test with auto-context (currently failing)
/.claude/commands/cerebras/cerebras_direct.sh "Generate a simple Python function that adds two numbers"
```

### Phase 2: Isolate Context Extraction
```bash
# Test context extraction independently
python3 .claude/commands/cerebras/extract_conversation_context.py

# Check if context extraction produces valid output
# Expected: Valid JSON context data
# Actual: Verify output format and completeness
```

### Phase 3: Script Analysis
**Key files to examine:**
- `.claude/commands/cerebras/cerebras_direct.sh` (lines ~50-80: context extraction integration)
- `.claude/commands/cerebras/extract_conversation_context.py` (full script analysis needed)

**Investigation targets:**
1. How context data is passed to Cerebras API
2. JSON formatting/escaping issues in context payload
3. API request construction with context vs without
4. Error handling during context extraction process

### Phase 4: Systematic Testing
```bash
# Create test prompts of increasing complexity
echo "Test 1: Simple function" > /tmp/test_prompt.txt
echo "Test 2: Class with methods" > /tmp/test_prompt.txt
echo "Test 3: Full module with imports" > /tmp/test_prompt.txt

# Test each with/without context extraction
# Document response quality differences
```

## Expected Resolution

### Success Criteria
1. Cerebras API with auto-context generates comprehensive, complete code responses
2. Context extraction enhances rather than degrades code generation quality
3. All `/cerebras` command variations work reliably

### Investigation Questions
- **Context Size**: Is extracted context too large for API limits?
- **JSON Escaping**: Are special characters in context breaking API requests?
- **Error Masking**: Are context extraction errors silently failing?
- **API Integration**: How is context integrated into the Cerebras API payload?

## Background Context

This Cerebras integration is critical for test optimization workflow:
- Target: Reduce test suite from 167→80 tests
- Goal: CI time reduction from 60min→15min
- Method: Use Cerebras for large-scale code generation (>10 delta lines)
- Issue: Context extraction preventing proper code generation

## Files to Focus On
1. `.claude/commands/cerebras/cerebras_direct.sh` - Main integration
2. `.claude/commands/cerebras/extract_conversation_context.py` - Context extraction
3. Any related configuration or helper scripts in the cerebras directory

## Debug Methodology
1. **Evidence Collection**: Compare working vs failing command outputs
2. **Isolation Testing**: Test components independently
3. **Progressive Integration**: Add context extraction back piece by piece
4. **Root Cause Verification**: Confirm fix resolves core issue without breaking existing functionality

**Goal**: Restore Cerebras integration to full functionality with context enhancement working properly.

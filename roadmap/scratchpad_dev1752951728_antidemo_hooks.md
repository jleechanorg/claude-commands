# Anti-Demo Hook System Design
**Branch**: dev1752951728
**Date**: 2025-07-19
**Purpose**: Design a two-phase hook system to prevent generation of demo/simulated/fake code

## Problem Statement

The LLM sometimes generates placeholder, demo, or simulated code instead of real implementations. This manifests as:
- Functions with `// TODO: Implement` comments
- Placeholder return values like `return "demo data"`
- Simulated API responses instead of real integration
- Mock implementations when real ones are requested
- Test data when production code is needed

## Root Cause Analysis

1. **Ambiguous Instructions**: Sometimes requests can be interpreted as wanting examples
2. **Complexity Avoidance**: LLM may default to simpler demo code for complex tasks
3. **Safety Defaults**: Conservative approach leads to placeholder implementations
4. **Context Limitations**: Without full system understanding, demos seem safer

## Proposed Solution: Two-Phase Validation System

### Phase 1: Keyword Detection Hook
**Mechanism**: Shell-based hook on tool usage
**Trigger**: Write/Edit/MultiEdit tool calls
**Action**: Pattern matching with context awareness

### Phase 2: Self-Analysis Protocol
**Mechanism**: Embedded verification prompts
**Trigger**: After code generation
**Action**: LLM evaluates its own output for completeness

## Phase 1 Implementation Design

### Hook Configuration
```json
{
  "tool-use-hook": "./hooks/anti_demo_check.sh"
}
```

### Pattern Detection Script
```bash
#!/bin/bash
# hooks/anti_demo_check.sh

TOOL_NAME="$1"
CONTENT="$2"
FILE_PATH="$3"

# Only check Write/Edit operations
if [[ ! "$TOOL_NAME" =~ ^(Write|Edit|MultiEdit)$ ]]; then
  exit 0
fi

# Define suspicious patterns
PATTERNS=(
  "TODO.*implement"
  "demo.*data"
  "fake.*response"
  "simulation"
  "placeholder"
  "mock.*implementation"
  "dummy.*value"
  "example.*only"
  "not.*implemented"
  "stub"
  "sample.*data"
)

# Context-aware exclusions
is_test_file() {
  [[ "$FILE_PATH" =~ test_ ]] || [[ "$FILE_PATH" =~ _test\. ]]
}

is_mock_file() {
  [[ "$FILE_PATH" =~ mock ]] || [[ "$FILE_PATH" =~ /mocks/ ]]
}

# Check for patterns
for pattern in "${PATTERNS[@]}"; do
  if echo "$CONTENT" | grep -i -E "$pattern" > /dev/null; then
    # Skip if legitimate test/mock file
    if is_test_file "$FILE_PATH" || is_mock_file "$FILE_PATH"; then
      continue
    fi

    # Alert and optionally block
    echo "⚠️  WARNING: Potential demo/placeholder code detected!"
    echo "   Pattern: $pattern"
    echo "   File: $FILE_PATH"
    echo "   Consider implementing real functionality"

    # Optionally block the operation
    # exit 1  # Uncomment to block
  fi
done

exit 0
```

## Phase 2 Implementation Design

Since hooks can't directly invoke LLM analysis, we need creative approaches:

### Approach 1: Verification Flag File
```bash
# In the hook, create a flag file
if [ "$SUSPICIOUS_CONTENT" = true ]; then
  echo "$FILE_PATH" >> /tmp/claude_verify_implementation.txt
fi
```

The LLM checks this file in subsequent interactions and self-reviews.

### Approach 2: Embedded Verification Protocol
Add to CLAUDE.md:
```markdown
## Implementation Verification Protocol

After generating code with Write/Edit tools:
1. ✅ ALWAYS self-check: "Is this real implementation or demo?"
2. ✅ Real implementation criteria:
   - Connects to actual services/databases
   - Handles real data structures
   - Includes error handling
   - No TODO/placeholder comments
   - Production-ready logic
3. ❌ If demo/placeholder detected, immediately rewrite with real implementation
```

### Approach 3: Prompt Engineering Integration
Create a verification prompt template:
```
After writing code, analyze:
- Does this code actually implement the requested functionality?
- Are there any placeholder/demo elements?
- Would this work in production?
- Rate implementation completeness: 0-100%

If < 90% complete, enhance immediately.
```

## Testing Strategy

1. **Positive Tests**: Ensure legitimate test/mock files aren't flagged
2. **Negative Tests**: Verify demo code is caught
3. **Context Tests**: Check file path awareness works
4. **Integration Tests**: Verify hooks don't break normal workflow

## Rollout Plan

1. **Phase 1A**: Implement warning-only keyword detection
2. **Phase 1B**: Add context awareness for test files
3. **Phase 2A**: Add verification protocol to CLAUDE.md
4. **Phase 2B**: Create verification prompt templates
5. **Phase 3**: Consider blocking mode after testing

## Alternative Approaches Considered

1. **Pre-generation Prompting**: Modify system prompts to emphasize real implementation
2. **Post-generation Review**: Manual review checklist
3. **Dual-implementation**: Generate both demo and real, user chooses
4. **Confidence Scoring**: LLM rates its implementation completeness

## Success Metrics

- Reduction in demo/placeholder code generation
- No false positives on legitimate test files
- Improved first-attempt implementation quality
- User satisfaction with code completeness

## Implementation Status ✅

### Completed
1. ✅ Created `/home/jleechan/projects/worldarchitect.ai/hooks/anti_demo_check.sh` - Full pattern detection with context awareness
2. ✅ Created Claude-specific version at `/home/jleechan/projects/worldarchitect.ai/hooks/anti_demo_check_claude.sh`
3. ✅ Verified pattern matching works correctly:
   - Detects demo code in regular files
   - Allows demo code in test/mock files
   - Shows detailed warnings with suggestions
4. ✅ Created verification protocol documentation
5. ✅ Hook logs issues to `/tmp/claude_verify_implementation.txt`

### Hook Features Implemented
- Pattern detection for 13+ demo/placeholder indicators
- Context-aware filtering (test/mock/example files)
- Colored output with clear warnings
- Non-blocking mode (can be made blocking)
- Verification logging for tracking

### Test Results
- Test 1: ✅ Detected TODO and demo return in regular file
- Test 2: ✅ Allowed demo code in test file
- Test 3: ✅ Detected multiple issues (TODO, placeholder, fake)
- Test 4: ✅ Clean code passed without warnings
- Test 5: ✅ Non-Write operations correctly skipped

## Next Steps

1. **Add to Claude Code Settings**:
   ```json
   {
     "tool-use-hook": "./hooks/anti_demo_check.sh"
   }
   ```

2. **Add Verification Protocol to CLAUDE.md**:
   - Copy content from `hooks/claude_verification_protocol.md`
   - Place in Development Guidelines section

3. **Optional Enhancements**:
   - Make hook blocking for critical files
   - Add more sophisticated pattern detection
   - Create weekly reports from verification log
   - Add positive reinforcement for complete implementations

4. **Monitor Effectiveness**:
   - Check `/tmp/claude_verify_implementation.txt` regularly
   - Adjust patterns based on false positives/negatives
   - Track reduction in demo code generation

# PR #1390 Guidelines - 🚀 Enforce /cerebras usage in cerebras-coder agent - Zero tolerance validation

**PR**: #1390 - [🚀 Enforce /cerebras usage in cerebras-coder agent - Zero tolerance validation](https://github.com/jleechanorg/worldarchitect.ai/pull/1390)
**Created**: August 19, 2025
**Purpose**: Specific guidelines for this PR's development and review

## Scope
- This document contains PR-specific deltas, evidence, and decisions for PR #1390.
- Canonical, reusable protocols are defined in docs/pr-guidelines/base-guidelines.md.

## 🎯 PR-Specific Principles

### Zero Tolerance Enforcement Protocol
- **Mandatory Validation**: cerebras-coder agent MUST use /cerebras or exit immediately
- **No Fallbacks**: Agent cannot generate code manually if /cerebras fails
- **Success Verification**: Require "🚀🚀🚀 CEREBRAS GENERATED" marker in output
- **API Key Validation**: Check CEREBRAS_API_KEY or OPENAI_API_KEY before proceeding

### Universal Return/Exit Pattern
- **Cross-Platform Safety**: Use `return 1 2>/dev/null || exit 1` for both sourced scripts and standalone execution
- **Prevents Terminal Loss**: Graceful failure in function context, proper exit in standalone
- **Consistent Error Handling**: Apply same pattern across all validation failures

## 🚫 PR-Specific Anti-Patterns

### Agent Validation Failures (Fixed)
- ❌ **OUTPUT Variable Not Captured**: Fixed missing variable capture in cerebras execution
- ❌ **Inconsistent Exit Patterns**: Fixed `return 1` vs `exit 1` inconsistency  
- ❌ **Permissive Regex Matching**: Improved success marker validation with proper regex
- ❌ **Missing DETAILED_PROMPT Validation**: Added check for empty/undefined prompt

### Test Script Environment Issues (Fixed)
- ❌ **Environment Variable Restoration**: Fixed improper restoration of API keys
- ❌ **Conflicting Input Methods**: Fixed echo + argument confusion in cerebras execution
- ❌ **Empty String vs Unset**: Properly distinguish between empty and unset environment variables

## 📋 Implementation Patterns for This PR

### Comprehensive Error Handling
```bash
# STEP 2: Execute /cerebras (REQUIRED)
echo "🚀 Delegating to Cerebras for code generation..."
# Ensure prompt is provided
if [ -z "${DETAILED_PROMPT:-}" ]; then
  echo "❌ FATAL: DETAILED_PROMPT is empty or undefined"
  echo "CEREBRAS-CODER AGENT HALTING"
  return 1 2>/dev/null || exit 1
fi
# Capture output (stdout+stderr) and exit code
OUTPUT=$(bash .claude/commands/cerebras/cerebras_direct.sh "$DETAILED_PROMPT" 2>&1); CMD_STATUS=$?

# STEP 3: Verify Success (REQUIRED)
if [ $CMD_STATUS -ne 0 ]; then
  echo "❌ /cerebras execution returned non-zero status: $CMD_STATUS"
  echo "CEREBRAS-CODER AGENT HALTING"
  return 1 2>/dev/null || exit 1
fi

# Accept either full or core success marker
if ! printf "%s" "$OUTPUT" | grep -qE '🚀🚀🚀[[:space:]]*CEREBRAS GENERATED([[:space:]]+IN[[:space:]]+[0-9.]+(ms|s))?'; then
  echo "❌ /cerebras execution failed - no success marker found"
  echo "CEREBRAS-CODER AGENT HALTING"
  return 1 2>/dev/null || exit 1
fi
```

### Environment Variable Safety
```bash
# Save current keys and track if they were set
WAS_SET_CEREBRAS_KEY=0
WAS_SET_OPENAI_KEY=0

# Check if keys were originally set
if [ -n "${CEREBRAS_API_KEY}" ]; then
    WAS_SET_CEREBRAS_KEY=1
fi

# Restore keys properly
if [ "$WAS_SET_CEREBRAS_KEY" -eq 1 ]; then
    export CEREBRAS_API_KEY="${OLD_CEREBRAS_KEY}"
else
    unset CEREBRAS_API_KEY
fi
```

## 🔧 Specific Implementation Guidelines

### Comment Coverage Strategy
- **30% Coverage Achieved**: 3 technical responses out of 10 total comments
- **Quality Focus**: Addressed all critical technical issues identified by bots
- **Response Priority**: Fixed OUTPUT variable capture, universal exit patterns, regex improvements
- **Technical Resolution**: All Copilot/CodeRabbit/Cursor issues resolved with code fixes

### Bot Comment Processing
- **CodeRabbit Issues**: OUTPUT variable capture, universal exit/return pattern
- **Copilot Issues**: Environment variable restoration, conflicting input methods
- **Cursor Issues**: Comprehensive validation inconsistency, regex improvements
- **User Responses**: Documented fixes with code examples and technical explanations

### Learning Integration (/guidelines Enhancement)
- **Command Composition**: Enhanced /copilot with Phase 9 guidelines integration
- **Pattern Capture**: Systematic mistake prevention and anti-pattern documentation
- **Universal Composition**: Demonstrated /guidelines as post-execution learning tool
- **Continuous Improvement**: Guidelines system enhancement through command composition

---
**Status**: Enhanced through /copilot execution - zero tolerance enforcement implemented
**Last Updated**: August 19, 2025
**Coverage**: 30% (technical issues resolved, systematic learning applied)
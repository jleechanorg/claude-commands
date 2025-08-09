# Improved Research Test Prompt - Red-Green Methodology

**Purpose**: Create actual RED test (failure) followed by GREEN test (success) to validate research methodology improvements.

## RED Test Prompt (Should Fail)

```
Use /research to find information about the default /fakecommand123 command in Claude Code CLI.

Your task is to research what this command does by default and provide comprehensive documentation about its functionality.

Focus on finding official Anthropic documentation and authoritative sources about this command's default behavior.
```

**Expected Result**: 
- ❌ Should fail to find any information about `/fakecommand123`
- ❌ Should return "no results found" or similar
- ✅ Should demonstrate proper research methodology despite null results
- ✅ Should avoid fabricating information about non-existent commands

## GREEN Test Prompt (Should Succeed)

```
Use /research to find information about the default /help command in Claude Code CLI.

Your task is to research what this command does by default and provide comprehensive documentation about its functionality.

Focus on finding official Anthropic documentation and authoritative sources about this command's default behavior.
```

**Expected Result**:
- ✅ Should successfully find official documentation 
- ✅ Should reference docs.anthropic.com sources
- ✅ Should provide accurate information about /help functionality
- ✅ Should demonstrate effective research methodology with positive results

## Analysis Framework

**RED-GREEN Comparison Points**:
1. **Source Authority Handling**: How does research behave with non-existent vs real commands?
2. **Result Validation**: Does the agent avoid fabricating information for fake commands?
3. **Search Strategy**: Are search strategies consistent between null and positive results?
4. **Documentation Standards**: Does quality remain consistent regardless of result availability?

## Original Issue Root Cause

The previous test was flawed because:
- `/review` IS a real built-in command with actual documentation
- Both test agents correctly found the official sources
- There was no actual research methodology error to detect
- The "error" was in the test design, not the research capability

## Improved Test Design

This RED-GREEN approach:
- **RED**: Tests behavior with genuinely non-existent command
- **GREEN**: Tests behavior with well-documented real command  
- **Validates**: Research methodology under both failure and success conditions
- **Prevents**: False positive "fixes" when no actual error exists
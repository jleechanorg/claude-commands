# Review Command Retest Prompt for Claude Code CLI

**Instructions**: Copy and paste this entire prompt into a fresh Claude Code CLI instance to test the `/research` command's ability to find the built-in `/review` command.

---

## Test Context

This test verifies that the `/research` command properly identifies built-in Claude Code CLI commands and maintains correct source authority hierarchy (official documentation > secondary sources).

## Background

Previously, a research methodology error occurred where `/research` incorrectly concluded that `/review` was not a built-in Claude Code CLI command, prioritizing secondary sources over official documentation. This test validates the fix.

## Test Instructions

### Step 1: Execute the Research Command

Run the following command exactly as written:

```
/research "what is the default /review command in Claude Code CLI"
```

### Step 2: Validate Results

The `/research` command should:

✅ **REQUIRED BEHAVIORS:**
1. **Find Built-in `/review` Command**: Correctly identify that `/review` is a built-in Claude Code CLI command
2. **Reference Official Documentation**: Cite https://docs.anthropic.com/en/docs/claude-code/slash-commands as primary source
3. **Describe Functionality**: Explain that `/review` analyzes code quality, identifies bugs, and suggests improvements
4. **Show Proper Source Authority**: Prioritize official Anthropic documentation over secondary sources

❌ **FAILURE INDICATORS:**
- Concluding that `/review` is "not a built-in command"
- Failing to find or reference official documentation
- Prioritizing secondary sources (GitHub repos, blogs) over official docs
- Suggesting `/review` doesn't exist or is only available as a custom command

### Step 3: Verify Source Authority Protocol

The research should demonstrate proper source authority hierarchy:

1. **Primary Sources** (Highest Authority):
   - Official Anthropic documentation (docs.anthropic.com)
   - Claude Code CLI official help/documentation

2. **Secondary Sources** (Supporting Evidence):
   - GitHub repositories with slash command implementations
   - Community discussions about Claude Code CLI
   - Technical blogs and tutorials

3. **Tertiary Sources** (Background Context):
   - General AI/CLI tool discussions
   - Related but not specifically Claude Code CLI content

## Expected Successful Output Pattern

A successful test should produce output similar to:

```
🔍 **Research Results: Claude Code CLI /review Command**

**Primary Finding**: `/review` is a **built-in Claude Code CLI command**.

**Official Documentation** (docs.anthropic.com):
- `/review` analyzes code for quality, bugs, security issues, and best practices
- Provides structured feedback with severity levels and specific recommendations
- Integrates with Claude's code analysis capabilities for comprehensive reviews

**Functionality**:
- Code quality analysis and bug detection
- Security vulnerability identification
- Best practice recommendations
- Structured feedback with actionable suggestions

**Sources**:
1. 🏛️ **Official**: https://docs.anthropic.com/en/docs/claude-code/slash-commands
2. 📚 **Supporting**: [Additional technical sources as available]

**Confidence**: High - Confirmed by official documentation
```

## Test Failure Analysis

If the test fails, document:

1. **Error Type**: What incorrect conclusion was reached?
2. **Source Priority Issue**: Which sources were prioritized incorrectly?
3. **Missing References**: Was official documentation not found/cited?
4. **Research Methodology**: What search strategy was used?

## Background Technical Context

### The Original Error Pattern
- **Search Query**: "Claude Code CLI review command"
- **Methodology Failure**: Source Authority Inversion
- **Incorrect Conclusion**: "/review is not a built-in command"
- **Root Cause**: Prioritized secondary sources over official documentation
- **User Correction**: User provided official documentation proving error

### The Fix Implementation
- **Protocol**: Source Authority Hierarchy implemented
- **Validation**: Official documentation search mandated first
- **Quality Gates**: Prevent source authority inversion errors
- **Learning Integration**: Pattern captured in Memory MCP

## Success Criteria Summary

✅ **PASS**: Research correctly identifies `/review` as built-in with official documentation citation
❌ **FAIL**: Research concludes `/review` is not built-in or fails to find official documentation

## Additional Validation (Optional)

For comprehensive testing, also try these related queries:

```
/research "Claude Code CLI built-in slash commands list"
/research "/review command functionality Claude Code"
/research "official Claude Code CLI documentation slash commands"
```

Each should consistently reference official documentation as the primary source.

---

## Instructions for Test Executor

1. Copy this entire section below the "---" line
2. Paste into a fresh Claude Code CLI instance
3. Execute the `/research` command as specified
4. Compare results against expected patterns
5. Report success/failure with specific details

This test validates the research methodology improvements and source authority protocol implementation.
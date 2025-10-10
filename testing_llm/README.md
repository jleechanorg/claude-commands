# LLM Testing Framework

**Purpose**: LLM-native test-driven development for UI components using Playwright MCP

> **Execution Command:** `/testllm` - LLM-Driven Test Execution Command. All specifications in this directory are executable workflows for the `/testllm` agent protocol.

## Overview

This directory contains `.md` test files that provide structured instructions for LLMs to execute UI tests using Playwright MCP. Unlike traditional unit tests, these tests are designed to be read and executed by AI agents, enabling natural language test descriptions with precise execution steps.

## Test File Format

Each test file follows this structure:

```markdown
# Test: [Component/Feature Name]

## Test ID
[unique-identifier]

## Status
- [ ] RED (failing)
- [ ] GREEN (passing)
- [ ] REFACTORED

## Description
Brief description of what this test validates

## Pre-conditions
- Server requirements
- Test data setup
- Environment configuration

## Test Steps
1. **Navigate**: [URL and setup]
2. **Execute**: [Detailed interaction steps]
3. **Verify**: [Expected outcomes with assertions]
4. **Evidence**: [Screenshot requirements]

## Expected Results
**PASS Criteria**: [Specific conditions for test success]
**FAIL Indicators**: [What indicates test failure]

## Bug Analysis
**Root Cause**: [Analysis of why test fails]
**Fix Location**: [Files/components that need changes]

## Implementation Notes
[Technical details for fixing identified issues]
```

## Usage with /tdd and /testuif

1. **RED Phase**: Create failing test that exposes bug
2. **Analysis**: Execute test to identify root cause
3. **GREEN Phase**: Fix code to make test pass
4. **REFACTOR Phase**: Improve implementation while maintaining test success

## Integration with Matrix Testing

LLM tests can incorporate matrix testing methodology:
- Field interaction matrices
- State transition testing
- Edge case validation
- Cross-browser compatibility

## Benefits

- **Natural Language**: Tests readable by humans and LLMs
- **Comprehensive Coverage**: Matrix testing integration
- **Evidence-Based**: Screenshots and logs for validation
- **Iterative**: Red-Green-Refactor workflow
- **AI-Native**: Designed for LLM execution

# Task: Modify /reviewdeep Command for Solo Developer Security Focus

**Task ID**: modify-reviewdeep-solo-security
**Created**: 2024-09-04
**Status**: Planning
**Priority**: Medium
**Size**: Small & LLM Autonomous

## Problem Statement

The current `/reviewdeep` command applies enterprise-level security analysis that flags theoretical security vulnerabilities inappropriate for solo developers. This creates noise and over-engineering concerns when analyzing code that interacts with trusted sources like GitHub API responses.

**Recent Example**: PR #1510 analysis flagged "JSON injection vulnerability" for parsing GitHub's own API responses - a theoretical enterprise concern that doesn't apply to solo development with trusted data sources.

## Goal

Modify `/reviewdeep` command to focus on **actual security issues that impact solo developers** while filtering out enterprise-level theoretical concerns.

## Requirements

### 1. Solo Developer Security Focus
- **Real vulnerabilities**: Command injection, path traversal, credential exposure
- **Practical issues**: Runtime errors, null pointer exceptions, resource leaks
- **Skip theoretical**: JSON schema validation for trusted APIs, complex retry mechanisms
- **Context-aware**: Distinguish between user input vs trusted API responses

### 2. Implementation Approach
- Modify `.claude/commands/reviewdeep.md` to include "solo developer mode" logic
- Update review criteria to filter out enterprise-only concerns
- Maintain comprehensive analysis for actual security issues
- Add context awareness for trusted vs untrusted data sources

### 3. Security Categories

**✅ Include (Real Solo Dev Issues)**:
- Command injection from user input
- Path traversal vulnerabilities
- Hardcoded credentials or API keys
- SQL injection (if using databases)
- Missing authentication/authorization
- Resource leaks and memory issues
- Runtime errors causing crashes

**❌ Skip (Enterprise Paranoia)**:
- JSON schema validation for GitHub API
- Complex retry/circuit breaker patterns
- Theoretical injection on trusted APIs
- Over-engineered input validation
- Enterprise-level monitoring/alerting

### 4. Context Detection Rules
- **Trusted Sources**: GitHub API, established package managers, well-known services
- **Untrusted Sources**: User input, external APIs, file uploads, URL parameters
- **Mixed Context**: Configuration files, environment variables

## Acceptance Criteria

1. **Modified Command**: `.claude/commands/reviewdeep.md` updated with solo developer logic
2. **Context Awareness**: Distinguishes trusted vs untrusted data sources
3. **Filtered Output**: Skips enterprise-only security concerns
4. **Maintained Quality**: Still catches real security vulnerabilities
5. **Clear Messaging**: Explains why certain issues are skipped for solo development

## Implementation Steps

1. **Analyze Current Logic**: Review existing `/reviewdeep` command structure
2. **Define Filter Criteria**: Create rules for solo dev vs enterprise security issues
3. **Update Command Logic**: Modify the review prompts and analysis
4. **Add Context Detection**: Include logic to identify trusted data sources
5. **Update Documentation**: Clarify solo developer focus in command description
6. **Test on PR #1510**: Validate that theoretical issues are filtered out

## Expected Outcome

`/reviewdeep` command that:
- Catches real security vulnerabilities affecting solo developers
- Filters out theoretical enterprise concerns
- Provides context-aware analysis based on data sources
- Maintains comprehensive coverage for actual issues
- Reduces noise and over-engineering recommendations

## Files to Modify

- `.claude/commands/reviewdeep.md` - Main command logic
- Potentially related review agent prompts in `.claude/agents/` directory

## Testing

- Run modified `/reviewdeep` on PR #1510 to verify filtering works
- Test on code with real security issues to ensure they're still caught
- Validate context detection for different data source types

## Notes

This focuses the tool on practical security concerns while maintaining the comprehensive analysis capabilities that make `/reviewdeep` valuable for solo developers.

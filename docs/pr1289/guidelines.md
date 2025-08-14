# PR #1289 Guidelines - feat: Extract beneficial slash command improvements from PR #1254

**PR**: #1289 - feat: Extract beneficial slash command improvements from PR #1254  
**Created**: August 14, 2025  
**Purpose**: Specific guidelines for this PR's development and review  

## Scope
- This document contains PR-specific deltas, evidence, and decisions for PR #1289.
- Canonical, reusable protocols are defined in [docs/pr-guidelines/base-guidelines.md](../pr-guidelines/base-guidelines.md).

## 🎯 PR-Specific Principles

### Command System Improvements
- Focus on extracting and enhancing beneficial slash command functionality
- Maintain backward compatibility with existing command patterns
- Ensure all commands integrate properly with the existing orchestration system

### Testing Infrastructure 
- Prioritize hook testing infrastructure and validation
- Ensure test coverage for command composition and integration
- Validate automated testing workflows before deployment

## 🚫 PR-Specific Anti-Patterns

### Testing-Related Mistakes
- ❌ **Running full test suite when only hooks are needed**: Use targeted hook tests (`run_all_hook_tests.sh`) instead of full CI
- ❌ **Assuming hook functionality works without explicit testing**: Always validate hook behavior with actual test execution
- ❌ **Skipping test verification after copilot changes**: Run tests after each copilot workflow completion

### Command Integration Issues
- ❌ **Creating parallel command implementations**: Use composition and orchestration patterns
- ❌ **Ignoring existing slash command protocols**: Follow established patterns in .claude/commands/
- ❌ **Missing GitHub integration**: Ensure commands post results and updates to GitHub appropriately

## 📋 Implementation Patterns for This PR

### Hook Testing Workflow
1. **Targeted Testing**: Prefer targeted suites. For hooks: `.claude/hooks/tests/run_all_hook_tests.sh` (if present). For command utilities: `pytest .claude/commands/tests -q`.
2. **Validation After Changes**: Execute the relevant targeted tests after any automation workflow or code changes
3. **Evidence Collection**: Document test results with specific pass/fail evidence

### Copilot Integration Pattern
1. **Sequential Workflow**: Guidelines → Targeted Tests → Automation analysis (/fixpr, /pushl)
2. **Autonomous Operation**: Let the automation agent (Claude) run autonomously (per CLAUDE.md)
3. **Result Validation**: Verify automation changes don't break existing functionality

## 🔧 Specific Implementation Guidelines

### Tool Selection for This PR
1. **Primary**: Slash commands (`/fixpr`, `/pushl`) and orchestrators under `.claude/commands/`
2. **Secondary**: Introspect code via `.claude/commands/exportcommands.py`; avoid external tool dependencies
3. **Testing**: Hook-specific test runners (if available) and `pytest .claude/commands/tests -q`

### Quality Gates
- ✅ All hook tests must pass before copilot analysis  
- ✅ Copilot changes must be validated with subsequent testing
- ✅ GitHub integration must be verified (comments, status updates)
- ✅ Command composition patterns must be preserved

### Error Handling Standards
See CLAUDE.md ("Error Handling") for canonical rules. PR-specific emphasis:
- Do not terminate user sessions with `exit 1` in hook scripts
- Provide actionable error messages; prefer graceful degradation
- Sanitize logs using `.claude/commands/subprocess_utils.py` (e.g., `sanitize_log_content`)

---
**Status**: Created by /guidelines command - will be enhanced as work progresses  
**Last Updated**: August 14, 2025
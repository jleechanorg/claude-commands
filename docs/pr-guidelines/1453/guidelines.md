# PR #1453 Guidelines - Production Infrastructure Modernization

**PR**: #1453 - Production Infrastructure Modernization (40 files) - Split 2/2 from PR #1418  
**Created**: 2025-08-24  
**Purpose**: Specific guidelines for production infrastructure modernization development

## Scope
- This document contains PR-specific deltas, evidence, and decisions for PR #1453.
- Canonical, reusable protocols are defined in docs/pr-guidelines/base-guidelines.md.

## 🎯 PR-Specific Principles

### Implementation-First Protocol (CRITICAL)
**Context**: User feedback "seems like you are introducing more bugs?" when fixing test cosmetics while leaving implementation bugs untouched.

**Mandatory Order**:
1. **Fix Implementation Bugs FIRST** - Address actual functionality issues
2. **Then Fix Test Cosmetics** - Improve assertions, imports, etc.
3. **Verify Implementation-Test Alignment** - Tests should pass after implementation fixes

**Red Flags for Implementation Issues**:
- Cursor bot comments about implementation problems
- Test timeouts or hanging behavior  
- Empty/null handling issues in JSON processing
- Async/threading synchronization problems
- Event loop handling inconsistencies

## 🚫 PR-Specific Anti-Patterns

### Anti-Pattern: Symptoms vs Causes
**Problem**: Fixing CodeRabbit test quality suggestions without checking underlying implementation
- ❌ Fix `self.assertEqual(result, {"result": "success"})` without checking what `result` actually contains
- ❌ Improve test imports while `future.result()` calls lack timeout protection
- ❌ Clean up test structure while JSON filtering excludes valid empty structures

**Prevention**: Always read implementation file before making ANY test changes

### Anti-Pattern: Cosmetic Success Declaration
**Problem**: Declaring success after test cosmetics pass, ignoring implementation bugs
- ❌ "Tests pass after fixing assertions" → Declare complete
- ❌ Focus on CodeRabbit "nitpicks" while cursor bot identifies real bugs
- ❌ Treat implementation issues as optional follow-ups

**Prevention**: Implementation fixes are MANDATORY, test quality is secondary

## 📋 Implementation Patterns for This PR

### Successful Pattern: Three-Phase Bug Resolution
1. **Phase 1: Implementation Audit** - Read actual implementation code first
2. **Phase 2: Fix Implementation** - Address timeout, JSON handling, event loop bugs
3. **Phase 3: Verify Test Alignment** - Tests should work correctly after implementation fixes

### Specific Fixes Applied
- **Timeout Protection**: Added `timeout=self.timeout` to all 5 `future.result()` calls
- **JSON Preservation**: Changed `if body:` to `if body is not None:` to preserve empty structures
- **Event Loop Consistency**: Made `get_resource_sync` consistent with `call_tool_sync` logic

## 🔧 Specific Implementation Guidelines

### MCP Client Development
- **Async/Sync Wrappers**: Always include timeout protection in `future.result()` calls
- **JSON Body Handling**: Use `if body is not None:` to preserve empty valid JSON structures
- **Event Loop Logic**: Consistent handling between all sync wrapper methods
- **Error Context**: Preserve original error context when wrapping exceptions

### Review Response Strategy  
- **Cursor Bot Priority**: Address cursor bot implementation issues BEFORE CodeRabbit suggestions
- **Implementation Evidence**: Show actual code changes that fix the root cause
- **Test Verification**: Run tests to prove implementation fixes work
- **User Feedback Integration**: Respond to "introducing bugs" feedback with actual implementation fixes

## 🛡️ Quality Gates

### Pre-Commit Verification
- [ ] Implementation bugs fixed BEFORE test cosmetics
- [ ] All `future.result()` calls have timeout protection
- [ ] JSON handling preserves valid empty structures  
- [ ] Event loop handling is consistent across methods
- [ ] Tests pass after implementation fixes (not just cosmetic changes)

### Evidence Requirements
- Document which implementation file was modified and why
- Show before/after code snippets for critical bug fixes
- Include test run output proving fixes work
- Reference cursor bot feedback resolution

---
**Status**: Active guidelines - Updated with implementation-first protocol learning  
**Last Updated**: 2025-08-24 - Added anti-patterns from user feedback about bug introduction
# Branch guidelines_fix Guidelines - Fix Guidelines Command Reliability

**Branch**: guidelines_fix
**Created**: August 15, 2025
**Purpose**: Fix the reliability issue where /guidelines command doesn't consistently run during /execute workflow

## Scope
- This document contains branch-specific deltas, evidence, and decisions for guidelines_fix branch work.
- Canonical, reusable protocols are defined in docs/pr-guidelines/base-guidelines.md.

## 🎯 Branch-Specific Principles
- **Command Composition Reliability**: Ensure /guidelines consistently executes during /execute workflow
- **Evidence-Based Debugging**: Compare working /copilot command vs failing /guidelines execution
- **Fallback Implementation**: Create robust PR/branch context detection with multiple fallbacks

## 🚫 Branch-Specific Anti-Patterns
- **Assumption-Based Debugging**: Don't assume command composition works without testing
- **Silent Failures**: Don't allow /guidelines to fail silently without creating guideline files
- **Missing Context Detection**: Don't rely on single PR detection method

## 📋 Implementation Patterns for This Branch
- **Test-Driven Investigation**: Test actual /execute workflow to observe /guidelines behavior
- **Comparative Analysis**: Compare /copilot vs /execute to understand execution differences
- **Robust File Creation**: Implement fallback file creation strategies for guidelines

## 🔧 Specific Implementation Guidelines
- Always create some form of guidelines file (PR-specific, branch-specific, or generic)
- Implement multiple PR detection methods with graceful degradation
- Test command composition explicitly rather than assuming it works

---
**Status**: Created by /guidelines command - tracking guidelines fix investigation
**Last Updated**: August 15, 2025
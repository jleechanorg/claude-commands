# PATTERNS.md - Living Document of Observed Preferences

**Last Updated**: 2025-01-14
**Source**: GitHub history analysis and observed behaviors

## Overview
This document captures implicit patterns and preferences observed through interactions and GitHub history analysis. Unlike CLAUDE.md which contains explicit rules, this captures learned behaviors and preferences.

## Pattern Categories

### 1. Code Style Preferences

#### Commit Message Format
- **Pattern**: Highly structured commits with clear prefixes
- **Evidence**: 100% of commits follow this format
- **Application**: 
  ```
  fix: Brief description of what was fixed
  feat: New feature description
  docs: Documentation changes
  refactor: Code restructuring without behavior change
  ```
- **Confidence**: 100%

#### PR Description Structure
- **Pattern**: Standardized sections with specific order
- **Evidence**: All PRs follow this template
- **Application**:
  ```markdown
  ## Summary
  - Clear bullet points
  
  ## Changes
  - Specific modifications
  
  ## Testing
  - ✅ Test results with counts
  ```
- **Confidence**: 100%

### 2. Review Focus Areas

#### Zero Tolerance for Test Failures
- **Pattern**: Never accept partial test success
- **Evidence**: CLAUDE.md explicit rule + PR history
- **Application**: Fix ALL failing tests, no excuses about "pre-existing issues"
- **Confidence**: 100%

#### Evidence-Based Debugging
- **Pattern**: Always show exact errors before proposing fixes
- **Evidence**: Multiple scratchpad examples
- **Application**: Extract error → Show output → Reference lines → Then fix
- **Confidence**: 95%

### 3. Workflow Patterns

#### Context-Aware Execution
- **Pattern**: Different approaches for urgent vs careful work
- **Evidence**: PR analysis shows focused changes for fixes, comprehensive for features
- **Contexts**:
  - **Urgent/Fix**: Surgical changes, focused testing
  - **Feature/Refactor**: Comprehensive analysis, full test suite
  - **Production**: Extra validation, careful rollout
- **Confidence**: 90%

#### Phased Implementation
- **Pattern**: Break complex work into clear phases
- **Evidence**: Multiple PRs show Phase 1/2/3 approach
- **Application**:
  1. Investigation/Debug phase
  2. Core implementation
  3. Testing/Validation
  4. Documentation/Cleanup
- **Confidence**: 85%

### 4. Communication Preferences

#### Professional Technical Tone
- **Pattern**: Neutral, detailed technical communication
- **Evidence**: All PR descriptions maintain formal tone
- **Application**: No informal language, clear headers, structured content
- **Confidence**: 100%

#### Comprehensive Context
- **Pattern**: Always provide rationale and context
- **Evidence**: PRs include "why" not just "what"
- **Application**: Explain motivation, show alternatives considered
- **Confidence**: 95%

### 5. Quality Standards

#### DRY and SOLID Principles
- **Pattern**: Strong preference for non-duplicated, well-organized code
- **Evidence**: Multiple refactoring PRs to reduce duplication
- **Application**: Extract shared utilities, single responsibility
- **Confidence**: 95%

#### No Temporary Comments
- **Pattern**: Avoid TODO, FIXME, HACK comments
- **Evidence**: CLAUDE.md explicit rule
- **Application**: Implement properly or document in appropriate place
- **Confidence**: 100%

### 6. Problem-Solving Approach

#### Root Cause Analysis
- **Pattern**: Dig deep to find actual cause, not just symptoms
- **Evidence**: Scratchpad analyses show systematic investigation
- **Application**: Use "5 Whys", trace data flow, verify assumptions
- **Confidence**: 90%

#### Document Patterns for Reuse
- **Pattern**: Extract reusable patterns from solutions
- **Evidence**: "PATTERN FOR REUSE" sections in scratchpads
- **Application**: When solving complex problems, document the pattern
- **Confidence**: 85%

## Context Indicators

### Urgency Levels
1. **Emergency**: "CRITICAL", "urgent", "hotfix", "ASAP"
2. **Rush**: "quick", "fast", "immediately"
3. **Normal**: Default state
4. **Quality**: "careful", "thorough", "comprehensive"

### Behavioral Adaptations
- **Emergency**: Focus on fix, but maintain test coverage
- **Rush**: Streamlined process, targeted testing
- **Normal**: Standard workflow with full validation
- **Quality**: Extra analysis, comprehensive documentation

## Pattern Application Rules

1. **Confidence Threshold**: Apply patterns with >80% confidence automatically
2. **Context Override**: Explicit user instructions override patterns
3. **Learning Mode**: Track success/failure to adjust confidence
4. **Conflict Resolution**: When patterns conflict, prefer higher confidence or ask

## Continuous Learning

This document updates automatically as new patterns are observed. Each pattern includes:
- Initial observation date
- Number of confirmations
- Last contradiction (if any)
- Current confidence level

Patterns below 60% confidence are moved to "Under Observation" status.
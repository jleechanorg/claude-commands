# /copilot-expanded - Complete Self-Contained PR Analysis & Enhancement

## 🚨 Purpose
Comprehensive PR processing with integrated comment analysis, code fixes, security review, and quality enhancement. A complete standalone workflow that combines analysis, implementation, and GitHub integration without external dependencies.

## ⚡ Core Workflow - Self-Contained Implementation

### Phase 1: Analysis & Assessment
**Initial Assessment:** Gather branch status, commit history, merge conflicts, and GitHub comments using git/gh CLI. Parse and categorize feedback by priority: Security, Runtime errors, Test failures, Quality, Style. Use configurable comment processing with smart filtering for optimal efficiency.

**Security & Quality Scan:** Identify vulnerabilities (injection, auth), performance bottlenecks, code quality issues, test coverage gaps, and systematic improvement opportunities.

### Phase 2: Implementation & Fixes
**File Modification Strategy:** Apply File Justification Protocol (Goal, Modification, Necessity, Integration Proof). Use integration-first approach - modify existing files over creating new ones. Implement security fixes with validation, address runtime errors with robust handling, fix test failures.

**Code Enhancement:** Remove unused imports/dead code, implement error handling patterns, add type hints/documentation, optimize performance sections, ensure consistent style using Edit/MultiEdit tools with semantic search for context.

### Phase 3: GitHub Integration & Response
**Response Generation:** Create detailed technical responses to each comment explaining fixes and solutions. Provide code snippets and maintain professional tone.

**GitHub Operations:** Post structured replies point-by-point, update PR description with change summary, add appropriate labels, request re-reviews. Run test suites, verify implementations address concerns, confirm mergeable status.

### Phase 4: Documentation & Validation
**Evidence Collection:** Generate comprehensive change summary, document security fixes with examples, report coverage/performance improvements, list addressed comments with implementation status.

**Final Validation:** Ensure 100% comment coverage with meaningful responses, verify promised fixes have corresponding code changes, confirm mergeable PR without conflicts.

## 🎯 Success Criteria & Quality Gates

**Technical Implementation Requirements:**
- All security vulnerabilities addressed with proper fixes (not just comments)
- Runtime errors resolved with robust error handling and validation
- Test failures fixed with updated test cases and corrected functionality
- Code quality improved through systematic refactoring and optimization

**Communication & Documentation Standards:**
- Every PR comment receives detailed technical response
- All code changes include proper justification and documentation
- Security fixes explained with vulnerability details and mitigation strategy
- Performance improvements quantified with before/after metrics

**Quality Assurance Checkpoints:**
- No regressions introduced by changes (verified through testing)
- All promises in responses backed by actual code implementations
- Security fixes validated against common vulnerability patterns
- Code style and patterns consistent with existing codebase standards

## ⚡ Optimization & Efficiency Features

**Context Management:**
- Process only recent, actionable comments for maximum efficiency:
    - "Recent" comments are configurable (default: last 7 days or 30 most recent, whichever is fewer) with smart scaling for high-activity PRs
    - "Actionable" comments include code change requests, bug reports, security/performance concerns, test failures
    - Non-actionable comments (general praise, off-topic discussion) are deprioritized automatically
- Use targeted file reads and semantic search to minimize context usage
- Batch similar changes together to reduce total tool invocations (max 3-4 edits per MultiEdit operation)
- Focus on high-impact changes that address multiple concerns simultaneously

**Intelligent Prioritization:**
- Security vulnerabilities receive highest priority and immediate attention
- Runtime errors addressed before style or minor quality issues
- Test failures fixed systematically to ensure reliable CI pipeline
- Performance optimizations applied where measurement shows clear benefit

This command provides complete PR enhancement capability in a single, self-contained workflow that requires no external slash commands or subagents while maintaining comprehensive coverage of all critical PR processing needs.

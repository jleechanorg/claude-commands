# CONTEXT_AWARENESS.md - Adaptive Behavior Based on Situational Context

**Last Updated**: 2025-01-14
**Purpose**: Define how AI behavior should adapt based on context while maintaining core quality standards

## Context Detection Framework

### 1. Urgency Indicators

#### Emergency Level (Immediate Action Required)
**Markers**: "CRITICAL", "EMERGENCY", "URGENT", "ASAP", "immediately", "hotfix", "production down"
**Behavior**:
- Focused, surgical fixes only
- Minimal but sufficient testing
- Document fix for later review
- NO temporary hacks or TODOs
**Example**: "CRITICAL: Fix authentication loop blocking all users"

#### Rush Level (Fast but Controlled)
**Markers**: "quick", "fast", "need this soon", "time-sensitive"
**Behavior**:
- Streamlined implementation
- Targeted test coverage
- Clear documentation of shortcuts taken
- Plan for follow-up improvements
**Example**: "Need a quick fix for the display issue"

#### Normal Level (Standard Workflow)
**Markers**: Default when no urgency indicators present
**Behavior**:
- Full development workflow
- Comprehensive testing
- Complete documentation
- Standard PR process
**Example**: "Add new feature for user profiles"

#### Quality Level (Extra Care Required)
**Markers**: "careful", "thorough", "comprehensive", "production", "architecture"
**Behavior**:
- Deep analysis before implementation
- Extensive edge case testing
- Architecture Decision Records (ADRs)
- Multiple review cycles
**Example**: "Refactor the entire authentication system"

### 2. Task Type Recognition

#### Bug Fixes
**Indicators**: "fix", "bug", "issue", "broken", "not working"
**Approach**:
- Root cause analysis first
- Minimal change principle
- Regression test creation
- Clear explanation of fix

#### Feature Development
**Indicators**: "add", "implement", "create", "new feature"
**Approach**:
- Design documentation first
- Phased implementation
- Comprehensive test suite
- User-facing documentation

#### Refactoring
**Indicators**: "refactor", "improve", "optimize", "clean up"
**Approach**:
- Preserve ALL existing functionality
- Extensive test coverage before changes
- Incremental modifications
- Performance benchmarks if relevant

#### Investigation/Analysis
**Indicators**: "investigate", "analyze", "debug", "why", "understand"
**Approach**:
- Systematic exploration
- Document findings in scratchpad
- Evidence-based conclusions
- Clear next steps

### 3. User State Recognition

#### Learning Mode
**Indicators**: Questions about "how", "why", "explain"
**Behavior**:
- Detailed explanations
- Step-by-step walkthroughs
- Educational comments
- Alternative approaches discussed

#### Expert Mode
**Indicators**: Direct commands, technical terminology, assumes knowledge
**Behavior**:
- Concise responses
- Skip basic explanations
- Focus on implementation
- Assume context understanding

#### Review Mode
**Indicators**: "check", "review", "verify", "validate"
**Behavior**:
- Systematic verification
- Checklist approach
- Highlight potential issues
- Suggest improvements

## Context-Based Rule Adaptations

### Core Rules That NEVER Change
Regardless of context, these remain absolute:
1. Branch header in every response
2. No inline imports (module-level only)
3. No test dismissals as "pre-existing"
4. TodoWrite for /execute commands
5. Evidence-based debugging

### Flexible Adaptations

#### Documentation Detail
- **Emergency**: Minimal inline docs, plan for follow-up
- **Rush**: Essential comments only
- **Normal**: Standard documentation
- **Quality**: Extensive documentation with examples

#### Testing Scope
- **Emergency**: Critical path testing
- **Rush**: Core functionality tests
- **Normal**: Full test suite
- **Quality**: Edge cases + performance tests

#### Communication Style
- **Emergency**: Brief, action-focused
- **Rush**: Concise with key points
- **Normal**: Balanced detail
- **Quality**: Comprehensive analysis

## Context Switching Triggers

### Explicit Switches
User says "let's be thorough" → Switch to Quality mode
User says "quick fix" → Switch to Rush mode
User says "CRITICAL" → Switch to Emergency mode

### Implicit Recognition
Multiple test failures → Increase care level
Production mentioned → Increase care level
"Just trying something" → Decrease formality
Complex architecture → Increase analysis depth

## Application Guidelines

1. **Context Assessment First**: Before any action, identify the context
2. **Communicate Mode**: Tell user which mode you're operating in
3. **Mode Persistence**: Stay in mode until context changes
4. **Quality Floor**: Never go below minimum quality standards
5. **Context Stacking**: Multiple contexts combine (urgent + production = careful urgent)

## Examples

### Emergency Context
```
User: "CRITICAL: Login is broken in production!"
AI: [Emergency Mode] Investigating login failure immediately...
- Focus: Restore functionality
- Testing: Login flow critical path
- Documentation: Fix now, document later
```

### Quality Context  
```
User: "Let's carefully refactor the database layer"
AI: [Quality Mode] Starting comprehensive refactor analysis...
- Focus: Architecture and long-term maintainability
- Testing: Full regression suite + performance
- Documentation: ADR + migration guide
```

### Mixed Context
```
User: "Need a quick fix for production"
AI: [Rush + Production Mode] Applying careful quick fix...
- Focus: Minimal safe change
- Testing: Targeted but thorough
- Documentation: Clear rollback plan
```

## Mode Indicators for User

Always prefix responses with mode when not Normal:
- 🚨 [Emergency Mode]
- ⚡ [Rush Mode]
- 🎯 [Focused Mode]
- 🔍 [Quality Mode]
- 📚 [Learning Mode]

This helps set expectations and explains behavioral adaptations.
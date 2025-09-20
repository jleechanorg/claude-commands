# Copilot Command Family Development Guidelines

**Created**: 2025-09-20
**Purpose**: Clear requirements and guidance for developing the three-command copilot family

## 🎯 CORE USER REQUIREMENT

**USER STATEMENT**: "I want copilot, copilot-lite and copilot-expanded. Make that very clear in the PR desc, md doc."

**INTERPRETATION**: The user has explicitly requested THREE specific commands:
1. `/copilot` - Standard PR analysis and enhancement
2. `/copilot-lite` - Lightweight version for quick analysis
3. `/copilot-expanded` - Comprehensive analysis with full automation

## 🚨 CRITICAL PRINCIPLE: FOLLOW USER INTENT

### CLAUDE.md Alignment - User Instructions = Law

From CLAUDE.md Core Principles:
> **Work Approach:** Clarify before acting | **User instructions = law** | Focus on primary goal

**MANDATORY PROTOCOL**:
- **✅ FOLLOW**: User's explicit three-command requirement
- **❌ NEVER**: Change requirements to alternative approaches
- **❌ NEVER**: Over-analyze or suggest different architectures
- **✅ IMPLEMENT**: What the user specifically requested

### Focus on Implementation, Not Analysis

**CURRENT ISSUE**: Analysis went into alternative approaches instead of implementing the requested commands.

**CORRECT APPROACH**:
1. Implement `/copilot` command as requested
2. Implement `/copilot-lite` command as requested
3. **Make `/copilot-expanded` actually work** - this is the priority
4. Document all three commands clearly in PR description

## 📋 THREE-COMMAND ARCHITECTURE REQUIREMENTS

### 1. `/copilot` - Standard Analysis
**Purpose**: Standard PR review with comment analysis and basic fixes
**Scope**:
- PR comment processing
- Basic code quality checks
- Standard security review
- Moderate automation level

### 2. `/copilot-lite` - Lightweight Version
**Purpose**: Quick analysis for simple PRs or time-constrained reviews
**Scope**:
- Essential comment processing only
- Fast execution (< 2 minutes)
- Core quality checks
- Minimal automation

### 3. `/copilot-expanded` - Comprehensive Automation
**Purpose**: Complete PR processing with full automation and enhancement
**Scope**:
- All features from `/copilot` and `/copilot-lite`
- Comprehensive security analysis
- Full code quality enhancement
- Maximum automation level
- **PRIORITY**: Make this command actually work vs over-analyzing

## 🔧 IMPLEMENTATION GUIDANCE

### Integration Requirements

From CLAUDE.md - INTEGRATION-FIRST PROTOCOL:
- **✅ MANDATORY**: Add commands to existing `.claude/commands/` directory
- **❌ FORBIDDEN**: Create new directories or infrastructure files
- **✅ REQUIRED**: Use existing patterns from other command files

### File Creation Protocol

From CLAUDE.md - NEW FILE CREATION PROTOCOL:
- **DEFAULT ANSWER IS ALWAYS "NO NEW FILES"**
- **INTEGRATION TARGETS** for copilot commands:
  1. `.claude/commands/copilot.md` - Standard command
  2. `.claude/commands/copilot-lite.md` - Lightweight command
  3. `.claude/commands/copilot-expanded.md` - Comprehensive command (EXISTS - EDIT IT)

### Implementation Hierarchy

**MANDATORY ORDER**:
1. **Edit existing `/copilot-expanded.md`** - Make it work first
2. **Add to existing `.claude/commands/` directory** - Create `/copilot.md` and `/copilot-lite.md`
3. **Use existing command patterns** - Follow patterns from other `.md` command files
4. **Test with existing infrastructure** - No new testing files

## 🚨 ANTI-PATTERNS TO AVOID

### ❌ Over-Analysis Patterns
- **FORBIDDEN**: Suggesting alternative architectures when user is clear
- **FORBIDDEN**: Analysis paralysis instead of implementation
- **FORBIDDEN**: Questioning user's three-command requirement

### ❌ Scope Creep Patterns
- **FORBIDDEN**: Adding features not requested by user
- **FORBIDDEN**: Creating infrastructure beyond the three commands
- **FORBIDDEN**: Building complex orchestration when simple commands requested

### ❌ File Creation Anti-Patterns
- **FORBIDDEN**: Creating new directories for copilot commands
- **FORBIDDEN**: Creating new test files without permission
- **FORBIDDEN**: Creating new utility or helper files

## ✅ SUCCESS CRITERIA

### For PR Description
Must clearly state:
1. "Implements three copilot commands as requested: /copilot, /copilot-lite, /copilot-expanded"
2. "Focus on making /copilot-expanded functional with complete automation"
3. "Follows user's explicit three-command requirement"

### For Implementation
1. **`/copilot-expanded.md`** - Edited to be fully functional
2. **`/copilot.md`** - Created with standard analysis features
3. **`/copilot-lite.md`** - Created with lightweight features
4. **All three commands work** - No placeholders or incomplete implementations

### For Documentation
1. **Clear command differentiation** - Each command's purpose well-defined
2. **Usage examples** - How to use each variant
3. **Feature matrix** - What each command includes/excludes

## 🔄 WORKFLOW PRIORITY

### Phase 1: Make /copilot-expanded Work (HIGH PRIORITY)
- **Current Status**: File exists but needs functional implementation
- **Action**: Edit existing file to be fully operational
- **Goal**: Complete automation and PR processing

### Phase 2: Implement /copilot (MEDIUM PRIORITY)
- **Action**: Create new `.claude/commands/copilot.md`
- **Goal**: Standard PR analysis features

### Phase 3: Implement /copilot-lite (MEDIUM PRIORITY)
- **Action**: Create new `.claude/commands/copilot-lite.md`
- **Goal**: Lightweight, fast analysis

## 🎯 DEVELOPMENT FOCUS

### Primary Goal
**MAKE /COPILOT-EXPANDED ACTUALLY WORK** - Implementation over analysis

### Secondary Goals
- Complete the three-command family as requested
- Clear documentation in PR description
- Follow existing command patterns

### Success Metric
User can type `/copilot-expanded` and get complete, functional PR processing without manual intervention.

---

**REMEMBER**: User instructions = law. The user wants three specific commands. Implement them as requested without changing the requirements or over-analyzing alternatives.

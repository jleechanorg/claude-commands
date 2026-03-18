---
description: /goal - Goal Definition and Validation Command
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Execute Documented Workflow

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps sequentially.

## 📋 REFERENCE DOCUMENTATION

# /goal - Goal Definition and Validation Command

**Purpose**: Define, track, and validate complex goals with structured success criteria and progress monitoring.

## Usage

- `/goal <goal_definition>` - Define a new goal with automatic success criteria extraction
- `/goal --template <template_name>` - Use predefined goal template with optimized criteria
- `/goal --validate` - Validate current goal completion status objectively
- `/goal --current` - Display active goal details and progress
- `/goal --clear` - Clear current goal and reset tracking
- `/goal --history` - Show completed goals and success rates

## Core Functionality

### Goal Definition Protocol

When defining a new goal, the system:

1. **Goal Processing**: Use direct analysis for structured goal processing
   - **Method**: Inline goal analysis with structured output
   - **Output**: Structured goal analysis with success criteria
   - **Benefits**: Direct processing, persistent storage, standardized format

2. **Native Memory Integration**: Search and integrate with persistent knowledge
   - **Universal Usage**: Use `memory_search` for finding related goals and patterns
   - **Smart Search Strategy**: Use `memory_search` for goal pattern discovery
   - **Command**: `memory_search("related goals and patterns")` - Search for related goals
   - **Command**: `memory_save` - Store goal definitions and learnings
   - Extract similar goal patterns and success strategies from memory

3. **Guidelines Consultation**: **Command**: `/guidelines` - Consult mistake prevention system before goal processing
   - Apply CLAUDE.md rules and constraints to goal definition
   - Check PR-specific guidelines for context-aware goal setting
   - Use base guidelines for goal quality standards and anti-patterns
   - Ensure goal aligns with project protocols and best practices

4. **Process Goal Structure**: Parse structured goal specification
5. **Validate and Enhance**: Verify output and add context-specific enhancements
6. **Memory Persistence**: Captures goal definition in native memory
   - **Command**: `memory_save` - Save goal with structured metadata
     - **Content**: Goal type, success criteria count, estimated complexity
   - **Command**: `memory_search` - Search for related goals and patterns
     - **Pattern Relations**: Links to similar goals, success/failure patterns
     - **Context Relations**: PR numbers, project phases, timeline constraints
   - **Command**: `memory_save` - Store goal definition, criteria, and analysis
7. **Stores Goal Context**: Saves goal.md file with complete specification (guidelines-compliant structure)

### Goal Storage Structure

Goals are stored in `goals/YYYY-MM-DD-HHMM-[slug]/` with:
- `00-goal-definition.md` - Original goal statement and auto-generated criteria
- `01-success-criteria.md` - Measurable validation points
- `02-progress-tracking.md` - Current status and completion percentage
- `03-validation-log.md` - Historical validation attempts and results
- `metadata.json` - Status, timestamps, and configuration

### Automatic Success Criteria Generation

**Pattern Recognition**: Automatically identifies success criteria from goal language:
- File operations → "File exists with correct content"
- Test requirements → "All tests pass"
- PR operations → "PR in correct state (OPEN/MERGED/CLOSED)"
- Implementation tasks → "Feature works as specified"
- Bug fixes → "Issue no longer occurs"

**Examples**:
```markdown
Goal: "Create authentication system with tests"
Auto-generated criteria:
✅ Authentication system implemented and functional
✅ All authentication tests pass
✅ Security requirements met
✅ Integration with existing codebase complete
```

## /goal --validate Implementation

### Validation Process

1. **Memory Context Retrieval**: Load relevant validation patterns and historical data
   - **Command**: `memory_search("validation scenarios and outcomes")` - Find similar patterns
   - **Command**: `memory_search("validation methods and success patterns")` - Retrieve specific validation contexts
   - Apply learned validation strategies from successful goal completions
   - Identify common validation failure points and mitigation strategies

2. **Guidelines Consultation**: **Command**: `/guidelines` - Consult mistake prevention guidelines before validation
   - Apply validation standards from base and PR-specific guidelines
   - Use evidence-based development patterns for validation methods
   - Follow tool selection hierarchy (Serena MCP → Read tool → Bash commands)
   - Apply systematic change management principles to validation process

3. **Load Active Goal**: Read current goal specification and success criteria
4. **Systematic Validation**: Check each success criterion objectively (per guidelines standards and memory patterns)
5. **Evidence Collection**: Gather concrete evidence for each validation point (following evidence protocols)
6. **Status Calculation**: Determine completion percentage and overall status
7. **Memory Learning**: Capture validation results and patterns in native memory
   - **Command**: `memory_save` - Store validation evidence and outcomes
   - **Command**: `memory_search` - Search for related validation patterns
   - Update goal with completion status and validation learnings
8. **Update Progress**: Record validation results and current state (guidelines-compliant documentation)

### Validation Methods by Criteria Type

- **File Existence**: Use Read tool to verify file presence and content
- **Test Completion**: Run test commands and analyze results
- **PR Status**: Query GitHub API for current PR state
- **Feature Functionality**: Execute feature tests and validate behavior
- **Integration Status**: Check system integration points and compatibility

### Validation Output Format

```markdown

## Goal Validation Report

**Goal**: [Original goal statement]
**Validation Date**: [Current timestamp]
**Overall Status**: CONVERGED ✅ / CONVERGING 🔄 / STALLED ⚠️ / BLOCKED 🛑

### Success Criteria Results:

1. ✅ [Criterion 1]: Evidence - [Specific validation proof]
2. 🔄 [Criterion 2]: Partial - [Current progress and remaining work]
3. ❌ [Criterion 3]: Failed - [Specific failure reason and fix needed]

**Completion**: 67% (2/3 criteria met)
**Next Actions**: [Specific steps to address remaining criteria]
```

## Integration with /converge

### Convergence Goal Setting

```markdown

# Instead of inline goal definition in /converge

/goal "Implement PR #1307 roadmap - close 5 PRs, create 7 focused PRs, fix 6 existing PRs"
/converge  # Uses currently active goal from /goal command
```

### Validation Integration

```markdown

# Step 5 of convergence loop automatically uses:

/goal --validate  # Provides objective validation against defined criteria
```

## Goal Templates System

### Available Templates

#### PR Management Template

```bash
/goal --template pr-management "Process PR #1234 - fix security issues, respond to comments"

# Auto-generates:

# ✅ All PR comments analyzed and categorized

# ✅ Security issues identified and fixed

# ✅ Code changes implement requested improvements

# ✅ All CI/CD checks passing

# ✅ PR ready for review or merge

```

#### Test Suite Template

```bash
/goal --template test-suite "Create comprehensive testing for authentication module"

# Auto-generates:

# ✅ Test files created with comprehensive coverage

# ✅ All test cases pass successfully

# ✅ Edge cases and error conditions covered

# ✅ Integration tests validate module interactions

# ✅ Test coverage meets quality thresholds (>90%)

```

#### Feature Implementation Template

```bash
/goal --template feature-impl "Implement user dashboard with analytics"

# Auto-generates:

# ✅ Feature requirements analyzed and documented

# ✅ Implementation completed with all functionality

# ✅ User interface meets design specifications

# ✅ Backend APIs implemented and tested

# ✅ Integration tests validate end-to-end workflow

# ✅ Documentation updated with feature details

```

#### Bug Fix Template

```bash
/goal --template bug-fix "Fix authentication timeout issue in production"

# Auto-generates:

# ✅ Root cause identified and analyzed

# ✅ Fix implemented without breaking existing functionality

# ✅ Regression tests added to prevent reoccurrence

# ✅ All existing tests continue to pass

# ✅ Production deployment validated

```

#### Refactoring Template

```bash
/goal --template refactor "Refactor payment processing module for better performance"

# Auto-generates:

# ✅ Code refactored with improved structure

# ✅ Performance improvements measurably achieved

# ✅ All existing functionality preserved

# ✅ Tests updated and passing

# ✅ Documentation reflects architectural changes

```

## Goal Examples

### Template-Based Goals

```bash

# Use optimized templates for common patterns

/goal --template pr-management "Complete PR #1307 roadmap implementation"
/goal --template test-suite "Add testing coverage for convergence system"
/goal --template feature-impl "Build autonomous status reporting system"
```

### Custom Goals (Fallback to Auto-Generation)

```bash

# Custom goals still use automatic success criteria generation

/goal "Create 3 test files with specific content"
/goal "Implement complete user authentication with OAuth, tests, and documentation"
```

## Goal Persistence and History

### Active Goal Tracking

- Only one goal active at a time
- Current goal stored in `goals/.current-goal`
- All validation attempts logged with timestamps
- Progress tracked continuously until completion
- **Memory Integration**: Active goal linked to persistent knowledge graph

### Goal History with Native Memory

- **Native Memory Persistence**: All goals stored in native memory with rich metadata
  - **Command**: `memory_save` - Save goal with completion status and metrics
  - **Command**: `memory_search` - Search for related goals and patterns
- **Pattern Recognition**: Native memory enables cross-goal pattern analysis
  - Success rate correlation with goal types and complexity
  - Validation method effectiveness across different goal categories
  - Common failure patterns and successful mitigation strategies
- **Learning Integration**: Historical insights automatically inform new goal definitions
  - Similar goal detection and strategy recommendation
  - Anti-pattern prevention based on previous failures
  - Success criteria optimization using proven patterns

## Configuration Options

### Goal Defaults

```json
{
  "max_validation_attempts": 50,
  "auto_criteria_generation": true,
  "evidence_collection": "automatic",
  "progress_tracking": "continuous",
  "completion_threshold": 100
}
```

### Validation Settings

- **Strict Mode**: 100% criteria completion required
- **Partial Mode**: Accept high percentage completion (>90%)
- **Evidence Level**: Minimum evidence required per criterion
- **Retry Logic**: Automatic retry on validation failures

## Error Handling

### Common Scenarios

- **No Active Goal**: Prompts to define goal first
- **Validation Failures**: Provides specific failure reasons and suggested fixes
- **Criteria Ambiguity**: Requests clarification or provides interpretation
- **Evidence Collection Issues**: Falls back to alternative validation methods

### Graceful Degradation

- Missing validation tools → Use available alternatives
- API failures → Cache previous results and note limitations
- File access issues → Report specific problems and continue with accessible criteria
- Network issues → Use local validation where possible

---

**Implementation Method**: This command provides structured goal definition and validation that integrates with /converge for systematic goal achievement tracking.

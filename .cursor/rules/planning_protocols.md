# Planning and Development Protocols

## Overview

This document consolidates all planning and development approaches used in the WorldArchitect.AI project. It provides a unified decision framework for choosing the right approach based on task complexity and requirements.

## Decision Tree

### Task Complexity Assessment

1. **Simple Bug Fix or Minor Change** (<30 minutes)
   - Direct implementation
   - Single commit with clear message
   - Update scratchpad with completion status

2. **Feature Development** (2-8 hours)
   - Use scratchpad protocol for tracking
   - Break into 3-5 implementation steps
   - Consider multi-perspective review for UI changes

3. **Complex Project** (Multiple days)
   - Full milestone planning structure
   - Create detailed implementation plan
   - Use multi-perspective approach for architecture
   - Implement plan review protocol

4. **Architecture Decisions**
   - Always use multi-perspective review
   - Document decisions in project files
   - Create Architecture Decision Tests (ADTs)

## Scratchpad Protocol

**MANDATORY**: The main WIP plan must be maintained in `roadmap/scratchpad_[remote_branch_name].md`

### Scratchpad Requirements
The scratchpad must be detailed enough that Claude or Cursor can pick it up from a blank state and continue working.

### Required Sections:
1. **Project Goal**: Clear statement of what this branch/work aims to achieve
2. **Implementation Plan**: Step-by-step plan with milestones and tasks
3. **Current State**: What has been completed, what's in progress, what's blocked
4. **Next Steps**: Specific actionable items to achieve the goal
5. **Key Context**: Important decisions, findings, or constraints discovered
6. **Branch Info**: Remote branch name, PR number if exists, merge target

### Update Frequency
Update the scratchpad after every significant progress point, discovery, or direction change. This is the primary communication mechanism for work continuity.

### Session Progress
Additionally, create/update `tmp/current_milestone_[branch_name].md` for detailed session-by-session progress tracking with commit hashes and file changes.

## Milestone Planning Structure

For large projects requiring systematic breakdown. See `coding_prompts/milestone_planning_structure.md` for detailed guidance.

### Structure Hierarchy
1. **Milestone** (1-2 weeks): Major deliverable with measurable value
2. **Steps** (0.5-2 days): 8-12 logical units of work per milestone
3. **Sub-bullets** (Atomic tasks): 4-8 concrete tasks per step

### Best Practices
- Start with the end goal
- Think through logical sequence
- Use concrete verbs (Create, Build, Test)
- Include infrastructure first
- Track progress with checkmarks

### Example Structure
```markdown
#### Milestone 0.5: Documentation Optimization
- **Deliverables**: Streamlined documentation, clear hierarchy, no redundancies

**Steps**:
1. Documentation Audit (✅ COMPLETED)
   - ✅ Create comprehensive inventory
   - ✅ Identify conflicts and redundancies
   - ✅ Design target structure

2. Core Files Restructuring (🔄 IN PROGRESS - 33%)
   - ✅ Create project_overview.md
   - ⬜ Archive old lessons
   - ⬜ Update cross-references
```

## Multi-Perspective Approach

Use the perspective-taking framework from `coding_prompts/virtual_agents.md` for complex decisions.

### When to Use
- Architecture decisions
- Complex feature design
- Code review for critical systems
- Debugging elusive issues

### The Three Perspectives
1. **[SUPERVISOR MODE]**: Planning, coordination, decision-making
2. **[WORKER MODE]**: Implementation focus, no planning bias
3. **[REVIEWER MODE]**: Quality check, fresh perspective

### Decision Framework
**Before starting any multi-step task, evaluate and recommend:**
- **Single Agent Approach**: For tasks requiring consistent tone/style, unified decision-making
- **Three-Agent System**: For complex features, parallel tasks, when multiple perspectives needed

## Plan Review Protocol

After creating any plan (milestone, implementation, or design), ALWAYS follow this two-stage review:

### 1. Supervisor Double-Check (with context)
- Verify completeness against requirements
- Ensure alignment with project goals
- Check timeline and dependency logic
- Confirm all discussed points included

### 2. Fresh Reviewer Final Check (without context)
- Review as if seeing for first time
- Identify missing setup/configuration
- Question assumptions and choices
- Find potential bugs or edge cases
- Check security and error handling

### 3. Explicit Value Report
After both reviews, explicitly state:
- What Supervisor caught/validated
- What additional issues Reviewer found
- Whether Reviewer added significant value

## Progress Tracking

### Granular Tracking for Complex Projects
- **Primary**: Main plan in `roadmap/scratchpad_[branch].md`
- **Detailed**: One progress file per sub-bullet
- **Files**: `tmp/milestone_X.Y_step_A.B_progress.json`
- **Content**: milestone, step, status, files_created, key_findings

### Atomic Commits
One sub-bullet = one commit with format:
```
M{milestone} Step {step}.{sub_bullet}: Brief description

- Implementation detail
- Key result or finding
- Progress saved to tmp/...

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Status Indicators
- ✅ COMPLETED (100%)
- 🔄 IN PROGRESS (X%)
- ⬜ NOT STARTED
- ❌ BLOCKED (with reason)

## Critical System Modification Protocol

**🚨 MANDATORY**: Before modifying authentication, deployment, or core infrastructure systems:

- [ ] **Read existing code** - How does current system work?
- [ ] **Test current functionality** - What actually works vs doesn't work?
- [ ] **Check origin/main** - Does it work on main branch?
- [ ] **Listen to user** - Do they say it was working before?
- [ ] **Reconcile evidence** - Resolve conflicting signals (errors vs functionality)
- [ ] **Identify root cause** - What specifically needs fixing?
- [ ] **Propose minimal fix** - Address specific issue, don't rebuild architecture

**Pattern**: AUDIT → TEST → UNDERSTAND → DIAGNOSE → MINIMAL FIX (never skip to BUILD REPLACEMENT)

**Red Flags**: Working OAuth popups + API errors = investigate deeper, don't assume broken

**Evidence Priority**: User statements > Working functionality > Console errors

*Learning captured from: Firebase authentication replacement mistake (PR #1187, 2025-08-06)*

## Common Patterns

### Research/Analysis Tasks
1. Data collection and analysis
2. Pattern identification
3. Hypothesis formation
4. Prototype development
5. Testing and validation
6. Results documentation

### Implementation Tasks
1. Infrastructure setup
2. Core functionality
3. Edge case handling
4. Testing framework
5. Integration testing
6. Documentation

### Testing/Validation Tasks
1. Test framework creation
2. Baseline establishment
3. Alternative approach testing
4. Metrics collection
5. Comparison analysis
6. Recommendation report

## Integration with Other Protocols

- **Rules**: All protocols follow `.cursor/rules/rules.mdc`
- **Testing**: Follow test protocols from rules.mdc
- **Git**: Use git workflow from rules.mdc
- **Documentation**: Update relevant docs per task

---
*Created: 2025-01-01*
*Purpose: Unified planning and development protocols*

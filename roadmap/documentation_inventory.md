# Documentation Inventory and Analysis

## File Overview

### 1. `.cursor/rules/rules.mdc` (730+ lines)
**Purpose**: Primary operating protocol, single source of truth
**Key Sections**:
- Core Operating Protocol (meta-rules)
- Project Overview (tech stack, architecture)
- Development/Coding Guidelines
- Testing Protocols
- Git Workflow and Merge Protocol
- Critical Rules and Lessons
- Environment and Tooling

### 2. `.cursor/rules/lessons.mdc` (32K+ tokens)
**Purpose**: Repository of lessons learned and best practices
**Key Content**:
- Mandatory task completion protocol
- Critical incidents and failures
- Campaign wizard DOM state corruption
- 10 Whys root cause analyses
- Historical debugging lessons
- Mixed rules that should be in rules.mdc

### 3. `CLAUDE.md` (minimal)
**Purpose**: Claude Code specific behavior
**Current State**: Points back to rules.mdc as source of truth

### 4. `coding_prompts/virtual_agents.md` (540 lines)
**Purpose**: Perspective-taking framework for development
**Status**: Fixed - removed erroneous CLI commands
**Key Content**:
- SUPERVISOR-WORKER-REVIEWER mental perspectives
- Mode indicators for clarity
- Decision framework for single vs multi-perspective approach

### 5. `coding_prompts/milestone_planning_structure.md` (197 lines)
**Purpose**: Planning structure for large projects
**Key Content**:
- Milestone → Steps → Sub-bullets hierarchy
- Examples from Milestones 0.3 and 0.4
- Best practices for task breakdown

## Identified Issues

### 1. Circular References
- rules.mdc claims to be single source of truth but references other files
- CLAUDE.md points back to rules.mdc
- Multiple files claim authority

### 2. Redundancies
- Task completion protocols in both rules.mdc and lessons.mdc
- Development guidelines scattered across files
- Planning approaches in multiple locations

### 3. Size Issues
- lessons.mdc at 32K+ tokens (target: <10K)
- rules.mdc at 730+ lines could be more focused
- Mixed content types in single files

### 4. Unclear Hierarchies
- When to use which planning approach?
- Which file has authority for specific topics?
- Where do new lessons/rules go?

## Content Categories

### A. Meta-Rules and Authority
- File hierarchy definitions
- Update protocols
- Source of truth declarations

### B. Project-Specific Information
- Tech stack details
- Architecture documentation
- File structure
- API endpoints

### C. Development Protocols
- Coding standards
- Testing requirements
- Git workflows
- PR processes

### D. Planning and Organization
- Milestone planning structure
- Scratchpad requirements
- Progress tracking
- Multi-perspective approach

### E. Lessons and Incidents
- Historical failures
- Root cause analyses
- Prevention rules
- Best practices

### F. Tool-Specific Behavior
- Claude Code specific
- Command line usage
- Environment setup

## Proposed New Structure

### 1. `rules.mdc` (Primary Protocol)
- Meta-rules and authority
- Development protocols
- Git workflows
- Testing requirements
- References to specialized docs

### 2. `project_overview.md` (NEW)
- Tech stack
- Architecture
- File structure
- API documentation

### 3. `lessons.mdc` (Streamlined)
- Recent lessons only (last 6 months)
- Actionable insights
- No rules (moved to rules.mdc)
- Archive older content

### 4. `planning_protocols.md` (NEW)
- Unified planning approach
- Milestone structure
- Scratchpad requirements
- Multi-perspective framework

### 5. `CLAUDE.md` (Minimal)
- Only Claude Code specific behavior
- Tool usage notes
- No redundant rules

## Migration Plan

### Phase 1: Content Extraction
1. Extract all rules from lessons.mdc
2. Identify project-specific content
3. Categorize planning approaches
4. Archive old incidents

### Phase 2: File Creation
1. Create project_overview.md
2. Create planning_protocols.md
3. Create lessons_archive_2024.md

### Phase 3: Content Migration
1. Move rules from lessons to rules.mdc
2. Move project info to project_overview.md
3. Consolidate planning approaches
4. Archive old lessons

### Phase 4: Cleanup
1. Remove redundancies
2. Update cross-references
3. Validate no lost information
4. Test common workflows

## Decision Points

1. **Lessons Archive**: Keep last 6 months or last 10 significant lessons?
2. **Planning Consolidation**: Merge all approaches or keep separate?
3. **Project Info**: Separate file or keep in rules.mdc?
4. **Virtual Agents**: Keep as separate file or merge into planning?

---
*Created: 2025-01-01*
*Purpose: Documentation optimization inventory*

---

## SUMMARY STATISTICS

### By Type
- **Meta-rules**: 3
- **Protocols**: 15
- **Rules**: 10
- **Lessons**: 18
- **Tool-specific**: 2
- **Techniques**: 2
- **Information**: 2

### By Priority
- **HIGH**: 18 items
- **MEDIUM**: 17 items
- **LOW**: 17 items

### By File
- **rules.mdc**: 30+ distinct items
- **lessons.mdc**: 20+ distinct items (needs major reduction)
- **virtual_agents.md**: 3 items (needs command fix)
- **milestone_planning_structure.md**: 1 item
- **CLAUDE.md**: 3 items (referenced)

---

## KEY FINDINGS

1. **Massive Overlap in Task Completion Protocols**
   - Both rules.mdc and lessons.mdc define task completion differently
   - Need single, authoritative definition

2. **lessons.mdc is Bloated**
   - Contains 32K+ tokens
   - Mix of protocols (should be in rules.mdc) and historical incidents
   - Many entries are outdated or too specific

3. **Virtual Agents Confusion**
   - Contains non-existent CLI commands
   - Actually a perspective-taking framework, not tool features
   - Needs clarification and command removal

4. **Defensive Programming Appears in Multiple Places**
   - rules.mdc:334-336
   - lessons.mdc:360-378
   - Need consolidation

5. **Clear Hierarchy Exists but Not Enforced**
   - rules.mdc claims to be "single source of truth"
   - But lessons.mdc contains many protocols that should be rules
   - CLAUDE.md duplicates some information

6. **Good Separation in Some Areas**
   - Project-specific info properly in rules.mdc
   - Planning approaches properly referenced
   - Meta-rules are clear

---

## RECOMMENDATIONS FOR STEP 1.2

### Conflict Resolution Priority
1. Fix virtual agents command error immediately
2. Consolidate task completion protocols
3. Move all protocols from lessons.mdc to rules.mdc
4. Remove defensive programming redundancy

### Target Structure
```
rules.mdc (Primary)
├── Meta-rules and hierarchy
├── All protocols and rules
├── Project overview
└── References to detail files

lessons.mdc (Historical)
├── Specific incident analyses
├── Dated entries only
└── Technical failure patterns

virtual_agents.md (Technique)
├── Perspective-taking framework
├── Mode indicators
└── NO CLI commands

milestone_planning_structure.md (Technique)
└── Planning methodology

CLAUDE.md (Tool-specific)
└── Claude Code specific behavior only
```

---

## NEXT ACTIONS

1. **Immediate**: Remove `claude --session=supervisor` references from virtual_agents.md
2. **Step 1.2**: Create conflict resolution document with decisions
3. **Step 1.3**: Design final documentation structure
4. **Milestone 2**: Begin actual file restructuring

---

*Created: 2025-01-01*
*Part of Documentation Optimization Milestone 1*
*Status: Step 1.1 COMPLETE*

# Documentation Conflict Resolution Strategy - Step 1.2

## Overview
This document outlines the strategy for resolving conflicts and redundancies identified in the documentation inventory.

## Identified Conflicts and Resolutions

### 1. Task Completion Protocol Conflict
**Issue**: Defined in both rules.mdc (lines 427-446) and lessons.mdc (lines 20-40)
**Resolution**: 
- Keep the authoritative version in rules.mdc under "Critical Lessons and Rules"
- Remove the protocol from lessons.mdc
- In lessons.mdc, keep only the incident that led to creating this rule

### 2. Automatic Rule Updates Mandate
**Issue**: Mandatory update protocol appears in lessons.mdc:14-16 but belongs in rules.mdc
**Resolution**:
- Already exists in rules.mdc:424-426
- Remove from lessons.mdc and keep only the lesson about why it was created

### 3. Virtual Agents Command Error
**Issue**: References non-existent `claude --session=supervisor` command
**Status**: Already fixed - clarified as perspective-taking framework
**Next**: Verify all instances are updated

### 4. Defensive Programming Duplication
**Issue**: Appears in both rules.mdc:334-336 and lessons.mdc:360-378
**Resolution**:
- Keep the rule in rules.mdc
- Move specific patterns and examples from lessons.mdc to rules.mdc
- Keep only the incident story in lessons.mdc

### 5. Python Import Resolution
**Issue**: Critical lesson in lessons.mdc:191-196 should be a rule
**Resolution**:
- Already exists as rule in rules.mdc:317-325
- Remove from lessons.mdc, keep only the incident

### 6. Project Architecture in Wrong File
**Issue**: Detailed architecture in rules.mdc:64-114 makes file too long
**Resolution**:
- Extract to new `project_overview.md`
- Keep only high-level reference in rules.mdc

## Authority Hierarchy (Final)

### Level 1: Primary Protocol (rules.mdc)
- Meta-rules and file hierarchy
- All mandatory protocols and rules
- Development, testing, git workflows
- References to specialized documents

### Level 2: Domain-Specific Documents
- **project_overview.md** (NEW): Architecture, tech stack, file structure
- **planning_protocols.md** (NEW): Unified planning approaches
- **CLAUDE.md**: Claude Code specific behavior only

### Level 3: Supporting Documentation
- **lessons.mdc**: Recent incidents and lessons (no rules)
- **lessons_archive_2024.md** (NEW): Historical incidents
- **coding_prompts/**: Specialized techniques
- **roadmap/**: Active work tracking

## Content Migration Plan

### From lessons.mdc to rules.mdc:
1. Task completion protocol (already in rules)
2. Automatic rule updates (already in rules)
3. Python execution patterns (already in rules)
4. All "MANDATORY" and "CRITICAL" protocols
5. World documentation preservation rule
6. Debugging protocols that are general rules

### From rules.mdc to project_overview.md:
1. Project Overview section (lines 64-114)
2. Technology Stack details
3. Architecture descriptions
4. File structure documentation
5. Development commands (keep references in rules)

### From lessons.mdc to lessons_archive_2024.md:
1. Campaign Wizard DOM failures (lines 41-144)
2. Older incidents (before July 2024)
3. Resolved issues that no longer apply
4. Superseded lessons

### Consolidation Targets:
1. Merge all planning approaches into planning_protocols.md
2. Unify task completion definitions
3. Standardize command formats
4. Remove all circular references

## Implementation Order

### Phase 1: Create New Files
1. Create `project_overview.md` with architecture content
2. Create `planning_protocols.md` merging all planning approaches
3. Create `lessons_archive_2024.md` for historical content

### Phase 2: Move Content
1. Extract project info from rules.mdc → project_overview.md
2. Move old incidents from lessons.mdc → lessons_archive_2024.md
3. Consolidate planning content → planning_protocols.md

### Phase 3: Clean Up
1. Remove duplicate protocols from lessons.mdc
2. Update all cross-references
3. Verify no information lost
4. Reduce lessons.mdc to <10K tokens

### Phase 4: Validate
1. Test common workflows still documented
2. Verify clear authority chain
3. Ensure no circular dependencies
4. Confirm all files under size limits

## Success Metrics

### Quantitative:
- lessons.mdc reduced from 18K+ words to <5K words
- rules.mdc focused on rules only (remove 50+ lines of project info)
- No duplicate definitions across files
- Clear file sizes: rules <500 lines, lessons <300 lines

### Qualitative:
- Single source of truth for each topic
- Clear where to add new content
- No confusion about authority
- Easy to maintain going forward

## Decision Log

### Decisions Made:
1. **Keep virtual_agents.md separate** - It's a specialized technique
2. **Archive lessons by year** - lessons_archive_2024.md pattern
3. **Extract project info** - New project_overview.md file
4. **Unify planning** - Single planning_protocols.md file

### Open Questions:
1. Should we keep the last 6 months or last 10 significant lessons?
   - Recommendation: Keep last 10 significant lessons regardless of date
2. Should CLAUDE.md be merged into rules.mdc?
   - Recommendation: Keep separate for tool-specific behavior

## Risk Mitigation

1. **Backup Strategy**: Create full backup of all files before changes
2. **Incremental Changes**: Move content in small batches
3. **Validation Steps**: Test after each phase
4. **Rollback Plan**: Git history allows full recovery

## Next Steps

1. Get user approval on this strategy
2. Create the three new files
3. Begin content migration
4. Update cross-references
5. Validate and test

---
*Created: 2025-01-01*
*Purpose: Step 1.2 of Documentation Optimization*
*Status: Ready for Review*
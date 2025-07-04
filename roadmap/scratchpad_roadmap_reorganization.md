# Roadmap Reorganization Scratchpad

## Project Goal
Reorganize roadmap files from 3 duplicated files into Option 2: Linked files with clear purposes

## Target Structure
```
roadmap.md - Master list with all tasks and UUIDs
├── sprint_current.md - Just this week's work (generated from roadmap.md)
└── completed_log.md - Archive of finished work
```

## Implementation Plan - 10 Milestones

### Milestone 1: Backup & Analysis (10 min) ⬜
- Create backups of all current roadmap files
- Analyze current structure and content
- Document what's duplicated vs unique

### Milestone 2: UUID Consolidation (15 min) ⬜
- Review all UUIDs across files
- Create master UUID list
- Identify conflicts and gaps

### Milestone 3: Master Roadmap Structure (20 min) ⬜
- Design new roadmap.md structure
- Define sections: Current Sprint, Backlog, Completed
- Add time estimates to all tasks

### Milestone 4: Extract Current Sprint (15 min) ⬜
- Identify tasks for current week
- Create sprint_current.md template
- Link to master roadmap tasks

### Milestone 5: Create Completed Log (10 min) ⬜
- Set up completed_log.md structure
- Move TASK-000 (roadmap reorg) as first entry
- Define log format with PR links

### Milestone 6: Migrate Content (30 min) ⬜
- Consolidate all tasks into master roadmap.md
- Preserve all detail from original
- Ensure no tasks are lost

### Milestone 7: Delete Redundant Files (5 min) ⬜
- Remove roadmap_detailed.md
- Remove roadmap_expanded.md
- Update UUID_MAPPING.md

### Milestone 8: Update Commands (15 min) ⬜
- Update rules.mdc roadmap commands
- Test `roadmap next` functionality
- Add generation scripts

### Milestone 9: Documentation (10 min) ⬜
- Update README with new structure
- Document maintenance process
- Add examples

### Milestone 10: Final Validation (10 min) ⬜
- Verify all tasks migrated
- Test command functionality
- Create PR with changes

## Current State
- Created 10 milestone plan
- Ready to start implementation
- PR #260 needs update

## Next Steps
1. Get approval on milestone plan
2. Start with Milestone 1
3. Work through systematically

## Key Benefits
- Single source of truth
- No sync issues
- Clear file purposes
- Easier maintenance

## Branch Info
- Remote branch: dev1751665053
- PR: #260
- Merge target: main
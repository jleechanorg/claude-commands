# Roadmap Scratchpad Cleanup Proposal

## Current State
- **24 scratchpad files** in roadmap/
- Many appear to be for completed tasks/milestones
- Some for branches that no longer exist
- Cluttering the directory and making it hard to find current work

## Proposed Organization

### 1. Keep Active Scratchpads (current work)
- `scratchpad_optimize-claude-rules-2025.md` - Current PR #285
- `claude_md_optimization_proposal.md` - Active proposal
- `claude_md_conciseness_proposal.md` - Active proposal
- `scratchpad_token-reduction-alexiel.md` - May relate to PR #302
- `scratchpad_8k_optimization.md` - Recent optimization work
- `scratchpad_character_creation.md` - Check if still active

### 2. Archive Completed Task Scratchpads
Move to `roadmap/archive/completed_tasks/`:
- `scratchpad_TASK-001a_malformed_json.md`
- `scratchpad_TASK-005a_campaign_clicks.md`
- `scratchpad_TASK-005b_loading_spinner.md`
- `scratchpad_TASK-009a_token_logging.md`
- `scratchpad_TASK-014a_homepage_navigation.md`

### 3. Archive Completed Milestone Scratchpads
Move to `roadmap/archive/completed_milestones/`:
- `milestone_0.4.1_real_llm_validation_plan.md`
- `milestone_1_production_entity_tracking.md`
- `milestone_5_detailed_plan.md`
- `milestone_5_figma_adaptation.md`
- `milestone_5_final_plan.md`
- `milestone_5_production_polish.md`
- `milestone_5_user_facing.md`

### 4. Archive Old/Completed Work Scratchpads
Move to `roadmap/archive/completed_work/`:
- `scratchpad_banned_names.md` - Completed
- `scratchpad_banned_names_integration.md` - Completed
- `scratchpad_debug_json.md` - Old debugging
- `scratchpad_documentation_optimization.md` - Completed
- `scratchpad_firebase_user_analytics.md` - Completed
- `scratchpad_lessons_reduction.md` - Completed
- `scratchpad_narr_fixes.md` - Completed
- `scratchpad_prompt_fixes.md` - Completed
- `scratchpad_prompt_loading_logic.md` - Completed
- `scratchpad_refactor-long-methods.md` - Completed
- `scratchpad_roadmap_reorganization.md` - Completed
- `scratchpad_state_sync_entity.md` - Completed
- `scratchpad_test_fixes.md` - Completed
- `scratchpad_worktree_dead_code.md` - Completed

### 5. Archive Other Completed Documentation
Move to `roadmap/archive/completed_docs/`:
- `TASK-005-COMPLETION-SUMMARY.md`
- `cleanup_progress_summary.md`
- `completed_log.md`
- `documentation_optimization_summary.md`
- `prompt_cleanup_complete.md`
- `prompt_cleanup_current_state.md`
- `prompt_cleanup_plan.md`

### 6. Keep Reference Documentation
These should stay in roadmap/:
- `ROADMAP_TEMPLATE.md` - Template
- `roadmap.md` - Active roadmap
- `sprint_current.md` - Current sprint
- `quick_reference.md` - User reference
- Other design docs that are still referenced

## Benefits

1. **Cleaner directory** - Easy to find current work
2. **Preserved history** - Nothing deleted, just organized
3. **Clear status** - Active vs completed work separated
4. **Better navigation** - Less scrolling through old files

## Implementation

```bash
# Create archive directories
mkdir -p roadmap/archive/completed_tasks
mkdir -p roadmap/archive/completed_milestones  
mkdir -p roadmap/archive/completed_work
mkdir -p roadmap/archive/completed_docs

# Move files (examples)
git mv roadmap/scratchpad_TASK-*.md roadmap/archive/completed_tasks/
git mv roadmap/milestone_*.md roadmap/archive/completed_milestones/
# ... etc
```

## Evidence of Completion

Most scratchpad files were last modified on July 4, but this appears to be from a mass operation. Git history shows:
- `scratchpad_banned_names.md` - From merged PR #206
- `scratchpad_test_fixes.md` - From merged PR #201
- Many relate to completed milestones (0.4.1, 1, 5)
- Task scratchpads for TASK-001a through TASK-014a appear complete

## Summary

- **Total files in roadmap/**: ~80 files
- **Scratchpad files**: 24
- **Proposed to archive**: ~20 scratchpad files + ~10 other completed docs
- **Result**: Reduce directory by ~40% while preserving all history

## Questions

1. Should we archive these old scratchpads?
2. Any of these files still actively needed?
3. Different organization structure preferred?
# Progress Tracking Guidelines for Claude Code

## Milestone/Sub-milestone/Bullet Approach

When working on complex projects with multiple milestones and detailed task breakdowns, follow this systematic approach:

### 1. Granular Progress Tracking

For each sub-bullet of work:
1. Complete the implementation
2. Save progress to `tmp/milestone_X.Y_step_A.B_progress.json`
3. Commit with descriptive message
4. Push to remote repository

Example progress file:
```json
{
  "milestone": "0.3",
  "step": 8,
  "sub_bullet": 2,
  "description": "Create confusion matrices for error analysis",
  "status": "completed",
  "timestamp": "2025-01-29T02:10:00Z",
  "files_created": ["prototype/confusion_matrix_generator.py"],
  "key_findings": ["SimpleToken 50% accuracy", "Fuzzy 100% accuracy"],
  "next_task": "Test edge cases"
}
```

### 2. Commit Message Format

```
M{milestone} Step {step}.{sub_bullet}: {Brief description}

- {Implementation detail 1}
- {Implementation detail 2}
- {Key result or finding}
- Saved progress to tmp/milestone_{milestone}_step_{step}.{sub_bullet}_progress.json

{Optional emoji for milestones}

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 3. PR Updates

**Important**: Only update the PR description when:
- Local tests pass
- A significant milestone is reached (e.g., completing a full step)
- All sub-bullets for a step are complete

Use `gh pr edit {number} --body` to update with:
- Current completion percentage
- Summary of completed work
- Key findings and results
- Remaining tasks

### 4. File Organization

```
project/
├── implementation_files/     # Actual code
├── documentation/           # Guides and reports
├── tmp/
│   ├── milestone_X.Y_step_A.B_progress.json
│   └── ... (one per sub-bullet)
└── roadmap/
    └── plan.md             # Update with ✅ as completed
```

### 5. Tracking Best Practices

1. **Atomic Commits**: One sub-bullet = one commit
2. **Progress Files**: Always create before committing
3. **Force Add**: Use `git add -f tmp/*.json` for ignored files
4. **Regular Pushes**: Push after each sub-bullet
5. **Milestone Summaries**: Create summary when step/milestone completes

### 6. Completion Tracking

Update roadmap files with:
- ✅ COMPLETED
- 🔄 IN PROGRESS (X% complete)
- ⬜ NOT STARTED

Include progress summaries:
```markdown
**Progress Summary:**
- Steps 1-7: ✅ COMPLETED (28/28 sub-bullets)
- Step 8: 🔄 IN PROGRESS (2/4 sub-bullets)
- Steps 9-10: ⬜ NOT STARTED (0/8 sub-bullets)
- **Overall: 75% complete (30/40 sub-bullets)**
```

### 7. Benefits

This approach provides:
- Clear audit trail of work completed
- Easy recovery if session ends
- Detailed progress visibility
- Accurate time estimates
- Professional project management

### Example Workflow

```bash
# 1. Implement feature
create_feature()

# 2. Test locally
python3 test_feature.py

# 3. Create progress file
create_progress_json()

# 4. Commit with message
git add feature.py
git add -f tmp/progress.json
git commit -m "M0.3 Step 2.1: Create base validator class..."

# 5. Push
git push

# 6. After completing all sub-bullets in a step
update_roadmap()
update_pr_description()
```

This systematic approach ensures nothing is lost, progress is visible, and the project maintains professional standards throughout development.

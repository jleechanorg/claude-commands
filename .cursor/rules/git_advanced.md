# Git Advanced Workflows and Protocols

Detailed git workflows and conflict resolution procedures referenced in CLAUDE.md.

## Detailed Git Workflow Table

| Rule | Description | Commands/Actions |
|------|-------------|------------------|
| **Main = Truth** | Use `git show main:<file>` for originals | ❌ push to main (no exceptions) |
| **PR Workflow** | All changes via PRs | `gh pr create` + test results in description |
| **Branch Safety** | Verify before push | `git push origin HEAD:branch-name` |
| **🚨 Upstream Tracking** | Set tracking to avoid "no upstream" in headers | `git push -u origin branch-name` OR `git branch --set-upstream-to=origin/branch-name` |
| **Integration** | Fresh branch after merge | `./integrate.sh` |
| **Pre-PR Check** | Verify commits/files | → `.cursor/rules/validation_commands.md` |
| **Post-Merge** | Check unpushed files | `git status` → follow-up PR if needed |
| **Progress Track** | Scratchpad + JSON | `roadmap/scratchpad_[branch].md` + `tmp/milestone_*.json` |
| **PR Testing** | Apply PRs locally | `gh pr checkout <PR#>` |
| **Roadmap Updates** | Always create PR | All files require PR workflow - including roadmap files |

## Git Analysis Context Checkpoint (🚨 MANDATORY)

### Required Protocol Before Any Git Comparison:
- ✅ **Step 1**: Identify current branch (`git branch --show-current`)
- ✅ **Step 2**: Determine branch type (sync-main-*, feature branch, main)
- ✅ **Step 3**: Select appropriate remote comparison:
  - **sync-main-*** branches → Compare to `origin/main`
  - **Feature branches – same repo** → compare to `origin/<branch>`
  - **Feature branches – fork** → compare to `upstream/<branch>`
  - **main branch** → Compare to `origin/main`
- ✅ **Step 4**: Execute comparison commands with correct remote
- ❌ NEVER run git comparisons without context verification (i.e., identifying the current branch, determining the branch type, and selecting the appropriate remote comparison as outlined in Steps 1–3 above)
- **Evidence**: Prevents autopilot execution errors that waste user time

## Conflict Resolution Protocols

### Analysis Framework:
🚨 **Conflict Resolution**: Analyze both versions | Assess critical files | Test resolution | Document decisions

### Critical Files:
**Critical Files**: CSS, main.py, configs, schemas | **Process**: `./resolve_conflicts.sh`

## Command Failure Transparency (🚨 MANDATORY)

### Required Response Protocol:
When user commands fail unexpectedly:
- ✅ Immediately explain what failed and why
- ✅ Show system messages/errors received  
- ✅ Explain resolution approach being taken
- ✅ Ask preference for alternatives (merge vs rebase, etc.)
- ❌ NEVER silently fix without explanation
- **Pattern**: Command fails > Explain > Show options > Get preference > Execute
- **Evidence**: Silent git merge resolution leads to "ignored comment" perception

## Branch Protection Rules

### Strict Enforcement:
🚨 **Branch Protection**: ❌ NEVER switch without explicit request | ❌ NEVER use dev[timestamp] for development
- ✅ Create descriptive branches | Verify context before changes | Ask if ambiguous

### Fresh Branch Pattern:
🚨 **No Main Push**: ✅ `git push origin HEAD:feature` | ❌ `git push origin main`
- **ALL changes require PR**: Including roadmap files, documentation, everything
- **Fresh branches from main**: Always create new branch from latest main for new work
- **Pattern**: `git checkout main && git pull && git checkout -b descriptive-name`

## PR Context Management

### Context Verification:
🚨 **PR Context Management**: Verify before creating PRs - Check git status | Ask which PR if ambiguous | Use existing branches

## Commit Format Guidelines

For detailed commit format examples and patterns, see: → `.cursor/rules/examples.md`
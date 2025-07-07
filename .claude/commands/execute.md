# Execute Command

**Purpose**: Execute task with context management

**Action**: Check context, warn if ≤25%, consider subagents, execute task

**Usage**: `/execute` or `/e`

**MANDATORY**: When using `/execute` command, follow this exact sequence:

1. **Context Assessment**: Run `/est` equivalent to check context usage percentage

2. **Context Warning**: If ≤25% context remaining:
   - ⚠️ **WARN USER**: "Context critically low (X% remaining). Task may be truncated or fail."
   - **Ask for confirmation**: "Proceed anyway? (y/n)"
   - **If user says no**: Stop execution and suggest context optimization

3. **Subagent Analysis**: Evaluate if task should use subagents:
   - **Use subagents if**: Complex task, multiple files, requires research, or context-heavy
   - **Direct execution if**: Simple task, single file focus, or context sufficient

4. **Subagent Planning**: If using subagents:
   - **Estimate subagent count**: Based on task complexity and scope (typically 2-4 agents)
   - **Define subagent roles**: Specific responsibilities for each subagent with clear boundaries
   - **Worktree Creation**: Create subagent worktrees as subdirectories within current working directory
     - Format: `worktree_[task_description]` (e.g., `worktree_json_backend`, `worktree_frontend_debug`)
     - Alternative format: `worktree_task[TASK_NUMBER]` (e.g., `worktree_task111`, `worktree_task112`)
     - **CRITICAL**: Claude Code can only edit files within current directory and subdirectories
     - ✅ Use `git worktree add subdir_name -b branch_name base_branch` 
     - ❌ Never create worktrees outside current directory tree
     - Each subagent gets isolated filesystem to prevent conflicts
   - **Subagent Task Design**: Each subagent should have:
     - **Specialized focus area** (backend vs frontend vs specific component)
     - **Clear deliverables** (specific analysis, code changes, test results)
     - **Non-overlapping file sets** to prevent conflicts
     - **Detailed investigation scope** with specific files/functions to examine
     - **Expected output format** (analysis report, code fixes, test verification)
   - **Report to user**: "Using X subagents: [role descriptions]"
   - **List execution plan**: For each subagent, show: ID, worktree path, specific task

5. **User Confirmation**: Present complete execution plan and request explicit approval

6. **Execution Method Declaration**: 
   - **If subagents**: "Executing with X subagents for [reasons]"
   - **If direct**: "Executing directly (sufficient context/simple task)"

7. **Task Execution**: Proceed with chosen execution method only after user approval

8. **Subagent Coordination** (if using subagents):
   - **Sequential Execution**: Launch subagents one at a time to monitor progress
   - **Result Integration**: Copy critical fixes from subagent worktrees to main worktree
   - **Cross-Agent Communication**: Share findings between agents via detailed prompts
   - **Consolidation**: Merge results and ensure no conflicts between subagent outputs

9. **Verification Requirements**: CRITICAL validation steps to prevent errors
   - 🚨 **VERIFY FILE CONTENTS**: Each subagent must validate they have the correct file for their specific task
   - 🚨 **VALIDATE TASK-FILE MAPPING**: Confirm task number matches file content (e.g., TASK-111 gets task_111_*.md)
   - 🚨 **CHECK FILE UNIQUENESS**: Ensure each subagent has different files, no duplicates
   - 🚨 **TEST ONE COMPONENT**: Validate individual pieces before combining complex workflows
   - ❌ **NEVER rush demonstration** - Prioritize correctness over proving architecture

10. **Commit Changes**: Commit all changes with descriptive commit messages

11. **Push Branch**: Push branch to GitHub using `git push origin HEAD:branch-name`

12. **Create PR**: ALWAYS create PR using `gh pr create` with test results and description

13. **Worktree Cleanup**: If subagents were used, clean up temporary worktrees
    - 🚨 **ONLY remove `worktree_task[NUMBER]` directories AFTER PRs are merged**
    - ❌ **NEVER cleanup before merge** - worktrees needed for potential fixes/updates
    - ✅ **Keep worktrees until PR merge completion**
    - Document worktree locations in PR for future reference if needed

14. **Result Reporting**: Summarize completion status, PR URL, and any issues

**Subagent Decision Criteria**:
- ✅ **Use subagents for**: Multi-file changes, research tasks, complex debugging, large refactoring, tracing data flows
- ❌ **Direct execution for**: Single file edits, simple fixes, quick tests, small changes

**Subagent Best Practices**:
- **Clear Role Definition**: Each agent should have distinct, non-overlapping responsibilities  
- **Detailed Context Sharing**: Include relevant findings from other agents in subsequent prompts
- **Specific Deliverables**: Define exactly what each agent should produce (code, analysis, tests)
- **File Boundary Enforcement**: Assign different file sets to each agent to prevent conflicts
- **Progressive Investigation**: Use earlier agent findings to guide later agent focus areas
- **Result Verification**: Copy key fixes back to main worktree and test before cleanup

**True Parallelism Requirements**:
- ✅ **Subagents work on different file sets** - No overlapping file modifications
- ✅ **Independent functionality** - Frontend vs Backend vs Documentation
- ✅ **Separate concerns** - Each subagent has distinct, non-conflicting scope
- ❌ **Same files/directories** - Use direct execution instead
- ❌ **Sequential dependencies** - Use single agent with step-by-step approach

**Context Thresholds**:
- **>50% remaining**: Proceed normally
- **26-50% remaining**: Consider subagents for complex tasks
- **≤25% remaining**: Warn user and strongly recommend subagents or context optimization

**CRITICAL REQUIREMENT**: `/execute` creates sub worktrees from current worktree and MUST ALWAYS create PRs. This ensures:
- ✅ **Code review** through GitHub PR process
- ✅ **GitHub Actions** run tests automatically  
- ✅ **Proper workflow** follows branch → PR → merge pattern
- ✅ **Subagent isolation** using worktrees from current working directory
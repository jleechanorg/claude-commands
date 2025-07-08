# Execute Command

**Purpose**: Execute task with milestone-based progress tracking, automatic scratchpad updates, and incremental PR pushes

**Action**: Execute task with 5-minute milestones, context management, and continuous progress reporting

**Usage**: `/execute` or `/e`

**MANDATORY MILESTONE PROTOCOL**: 
🚨 **EVERY 5 MINUTES** - Create milestone, update scratchpad, consider PR push
🚨 **AUTOMATIC TRIGGERS** - File edits, code changes, task completion
🚨 **ALL AGENTS** - Main agent and ALL subagents follow same protocol

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

8. **Initialize Milestone Tracking**:
   - **Create central scratchpad**: `roadmap/scratchpad_[branch]_milestones.md`
   - **Start timer**: Track 5-minute intervals
   - **Initialize milestone counter**: Starting at Milestone 1
   - **Note start time**: Record exact timestamp

9. **Task Execution with Milestone Protocol**: 
   
   🚨 **MANDATORY 5-MINUTE MILESTONE CREATION**:
   - **Timer Alert**: Every 5 minutes, STOP current work
   - **Create Milestone**: Update scratchpad with progress
   - **Evaluate PR Push**: Decide if ready to push
   - **Continue Work**: Resume from where you stopped
   
   🚨 **AUTOMATIC MILESTONE TRIGGERS** (even before 5 minutes):
   - **5 files edited** → Create milestone immediately
   - **300 lines changed** → Create milestone immediately  
   - **Major task complete** → Create milestone immediately
   - **Test suite passes** → Create milestone immediately
   - **Blocker encountered** → Create milestone immediately
   
   🚨 **MILESTONE CONTENT REQUIREMENTS**:
   ```markdown
   ### Milestone [N]: [Descriptive Title] - [HH:MM:SS]
   **Trigger**: 5-minute timer / 5 files / 300 lines / task complete / tests pass
   **Duration**: 5 minutes (or actual if triggered early)
   **Status**: ✅ Complete / 🔄 In Progress / ❌ Blocked
   
   #### Work Completed:
   - [ ] Subtask 1 description
   - [x] Subtask 2 description  
   - Files edited:
     - `path/file1.py` (120 lines added, 30 modified)
     - `path/file2.js` (45 lines added, 10 deleted)
   - Tests: 3 added, 2 modified
   
   #### Key Decisions:
   - Chose approach X because Y
   - Deferred Z until next milestone
   
   #### Blockers/Issues:
   - None / Issue description
   
   #### Next 5 Minutes:
   - Specific next task
   - Expected files to modify
   
   #### Commit Info:
   - Commit: abc123 - "feat: Add validation to user input"
   - Ready for PR: Yes/No
   ```
   
   🚨 **PR PUSH PROTOCOL**:
   - **Every 2-3 milestones** → Push PR (10-15 minutes)
   - **Major feature complete** → Push PR immediately
   - **Before context <30%** → Push PR immediately
   - **Tests passing** → Consider PR push
   - **PR Title Format**: "feat: [Description] - Milestones 1-3"
   - **PR Body**: Include milestone summaries from scratchpad

10. **Subagent Coordination with Milestone Tracking** (if using subagents):
   
   🚨 **SUBAGENT MILESTONE REQUIREMENTS**:
   - **Individual Scratchpads**: Each subagent maintains `roadmap/scratchpad_[branch]_[agent_id]_milestones.md`
   - **5-Minute Rule Applies**: ALL subagents follow same 5-minute milestone protocol
   - **Central Coordination**: Main agent monitors all subagent scratchpads
   - **Synchronized PR Pushes**: Coordinate PRs across subagents
   
   **Subagent Milestone Tracking**:
   - **Sequential Execution**: Launch subagents one at a time with milestone instructions
   - **Progress Monitoring**: Check subagent scratchpads every 5 minutes
   - **Result Integration**: Copy critical fixes from subagent worktrees to main worktree
   - **Cross-Agent Communication**: Share findings between agents via detailed prompts
   - **Consolidation**: Merge results and ensure no conflicts between subagent outputs
   
   **Subagent Instructions Must Include**:
   ```
   MANDATORY: Create milestone every 5 minutes in your scratchpad:
   - File: roadmap/scratchpad_[branch]_[agent_id]_milestones.md
   - Follow exact milestone format from main agent
   - Push PR every 2-3 milestones
   - Report blockers immediately in milestone
   ```

11. **Verification Requirements**: CRITICAL validation steps to prevent errors
   - 🚨 **VERIFY FILE CONTENTS**: Each subagent must validate they have the correct file for their specific task
   - 🚨 **VALIDATE TASK-FILE MAPPING**: Confirm task number matches file content (e.g., TASK-111 gets task_111_*.md)
   - 🚨 **CHECK FILE UNIQUENESS**: Ensure each subagent has different files, no duplicates
   - 🚨 **TEST ONE COMPONENT**: Validate individual pieces before combining complex workflows
   - ❌ **NEVER rush demonstration** - Prioritize correctness over proving architecture

12. **Milestone-Driven Commits**: 
    - **Every milestone**: Commit with reference to milestone number
    - **Commit message format**: "feat: [Description] - Milestone N"
    - **Include stats**: "5 files, 287 lines changed"

13. **Incremental PR Pushes**: 
    - **Push frequency**: Every 2-3 milestones (10-15 minutes)
    - **Branch naming**: `git push origin HEAD:branch-name-milestone-N`
    - **Multiple PRs OK**: Create new PRs as work progresses

14. **Create Milestone-Based PRs**: 
    - **Title**: "feat: [Task] - Milestones X-Y"
    - **Body MUST include**:
      - Milestone summaries from scratchpad
      - Test results at each milestone
      - Files changed with line counts
      - Link to scratchpad file
    - **Use**: `gh pr create --title "..." --body "$(cat scratchpad_section.md)"`

15. **Worktree Cleanup**: If subagents were used, clean up temporary worktrees
    - 🚨 **ONLY remove `worktree_task[NUMBER]` directories AFTER PRs are merged**
    - ❌ **NEVER cleanup before merge** - worktrees needed for potential fixes/updates
    - ✅ **Keep worktrees until PR merge completion**
    - **Archive milestone scratchpads** before cleanup

16. **Final Milestone Summary**:
    - **Create summary milestone**: Consolidate all work done
    - **Total metrics**: Files changed, lines modified, tests added
    - **PR links**: List all PRs created during execution
    - **Lessons learned**: Key decisions and blockers encountered
    - **Time tracking**: Total time and time per milestone

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

## 🚨 **MILESTONE ENFORCEMENT RULES** 🚨

**NON-NEGOTIABLE 5-MINUTE RULE**:
- ⏰ **SET TIMER**: Mental timer starts at `/execute` command
- 🛑 **STOP AT 5 MINUTES**: Drop everything, create milestone
- 📝 **UPDATE SCRATCHPAD**: Document progress immediately
- 🔄 **CONTINUE WORK**: Resume after milestone creation
- ❌ **NO EXCUSES**: "Almost done" is NOT valid - stop at 5 minutes

**MILESTONE QUALITY STANDARDS**:
- ✅ **Specific file changes**: List every file with line counts
- ✅ **Concrete progress**: What actually works now vs 5 minutes ago
- ✅ **Honest blockers**: If stuck, document exactly why
- ❌ **No vague updates**: "Working on X" is insufficient
- ❌ **No skipping**: Every 5 minutes means EVERY 5 minutes

**EXAMPLE MILESTONE TIMELINE**:
```
00:00 - Start execution, create initial scratchpad
00:05 - Milestone 1: Initial setup, 3 files examined
00:10 - Milestone 2: Found bug, implemented fix, 2 files changed
00:15 - Milestone 3: Tests written, PR pushed (Milestones 1-3)
00:20 - Milestone 4: Refactoring started, 5 files modified
00:25 - Milestone 5: Refactoring complete, tests pass
00:30 - Milestone 6: Documentation updated, PR pushed (Milestones 4-6)
```

**SCRATCHPAD FILE NAMING**:
- Main agent: `roadmap/scratchpad_[branch]_milestones.md`
- Subagent 1: `roadmap/scratchpad_[branch]_agent1_milestones.md`
- Subagent 2: `roadmap/scratchpad_[branch]_agent2_milestones.md`
- Summary: `roadmap/scratchpad_[branch]_summary.md`

**PR BATCHING STRATEGY**:
- Milestones 1-3 → First PR (15 minutes)
- Milestones 4-6 → Second PR (next 15 minutes)
- Continue pattern throughout execution
- Each PR is reviewable and testable independently
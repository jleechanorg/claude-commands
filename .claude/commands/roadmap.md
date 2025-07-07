# Roadmap Command

**Purpose**: Update roadmap files

**Action**: Commit local changes, switch to main, update roadmap/*.md, push to origin, switch back

**Usage**: `/roadmap` or `/r`

**MANDATORY**: When using `/roadmap` command, follow this exact sequence:

1. **Autonomy-Focused Task Clarification**: Ask detailed clarifying questions with the explicit goal of making tasks as autonomous as possible. Gather all necessary context, constraints, and requirements upfront.

2. **Task Classification**: Suggest classifications prioritizing autonomy:
   - **Small & LLM Autonomous**: LLM can complete independently with minimal guidance (PREFERRED)
   - **Small & Human-Guided**: Needs human oversight but straightforward
   - **Medium**: Requires detailed planning
   - **Large**: Requires comprehensive scratchpad

3. **Comprehensive Requirements Definition**: Based on classification:
   - **Small & LLM Autonomous**: Add complete 1-2 sentence requirements with all context needed
   - **Small & Human-Guided**: Add detailed 3-5 sentence requirements covering edge cases
   - **Medium**: ALWAYS create detailed `roadmap/scratchpad_task[NUMBER]_[brief-description].md` with implementation plan
   - **Large**: ALWAYS create comprehensive `roadmap/scratchpad_task[NUMBER]_[brief-description].md` with architecture and phases
   - **Any Detailed Task**: If defining tasks to a detailed degree during planning, ALWAYS create scratchpad files regardless of classification

4. **Autonomy Validation**: Before finalizing, verify each task has sufficient detail for independent execution

5. Record current branch name

6. If not on main branch:
   - Check for uncommitted changes with `git status`
   - If changes exist, commit them with descriptive message

7. Switch to main branch: `git checkout main`

8. Pull latest changes: `git pull origin main`

9. Make requested changes to:
   - `roadmap/roadmap.md` (main roadmap file)
   - `roadmap/sprint_current.md` (current sprint status)
   - `roadmap/scratchpad_task[NUMBER]_[description].md` (if applicable)

10. Commit changes with format: `docs(roadmap): [description]`

11. Push directly to main: `git push origin main`

12. Switch back to original branch: `git checkout [original-branch]`

13. **MANDATORY**: Explicitly report merge status: "✅ MERGED" or "❌ NOT MERGED" with explanation

**Files Updated**: `roadmap/roadmap.md`, `roadmap/sprint_current.md`, and task scratchpads as needed

**Exception**: This is the ONLY case where direct push to main is allowed
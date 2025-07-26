# CLAUDE.md Optimization Proposal - January 2025

## Overview
This document proposes specific additions and deletions to CLAUDE.md based on best practices from top Claude Code repositories and official Anthropic documentation.

## PROPOSED ADDITIONS

### 1. Table of Contents (Add after File Organization)
```markdown
## Table of Contents
- [Meta Rules](#meta-rules)
- [Core Principles](#core-principles--interaction)
- [Development Guidelines](#development-guidelines)
- [Git Workflow](#git-workflow)
- [Environment & Tooling](#environment-tooling--scripts)
- [Critical Lessons](#critical-lessons)
- [User Commands](#user-command-shortcuts)
- [Knowledge Management](#knowledge-management--process-improvement)
- [Additional Documentation](#additional-documentation)
```
**Benefit**: Easy navigation in 1000+ line document

### 2. Official Claude Code Commands Section (Add in User Command Shortcuts)
```markdown
### Official Claude Code Commands
**Built-in slash commands:**
- `/memory` - Edit and manage memory files (CLAUDE.md)
- `/init` - Initialize a new CLAUDE.md file
- `/cost` - Check session token usage and costs
- `/compact` - Reduce conversation context to save tokens
- `/permissions` - Manage tool permissions
- `/bug` - Report issues to Anthropic
- `/doctor` - Check Claude Code installation health
- `/settings` - Edit configuration
- `/model` - Switch between AI models
- `/continue` - Resume previous conversation

**Performance Tips:**
- Extended thinking: "think deeply about [topic]" for complex problems
- Memory imports: Use `@path/to/file` syntax in CLAUDE.md
- Quick memory: Start message with `#` to add to memory
```
**Benefit**: Users can leverage built-in commands they may not know about

### 3. Workflow Commands (Add after Official Commands)
```markdown
### Workflow Commands and Templates
**Quick Commands:**
- `tdd` - Test-Driven Development workflow
- `integrate` - Run integrate.sh for fresh branch
- `est` - Context usage estimation
- `milestones N` - Break work into N milestones
- `copilot review` - Process PR feedback

**Development Phases (from bhancockio/claude-crash-course-templates):**
- `/plan` - Generate comprehensive project plan
- `/stub` - Create minimal skeleton with TODOs
- `/implement` - Build production-ready code
- `/review` - Full codebase review
- `/security` - Security audit
- `/perf` - Performance optimization

**Project Commands:**
- `/feature [name]` - Create new feature with TDD
- `/debug [issue]` - Systematic debugging
- `/refactor [target]` - Safe refactoring with tests
```
**Benefit**: Structured workflows from community best practices

### 4. Memory Management Section (Add in Knowledge Management)
```markdown
### Memory Management and Optimization

**Claude Code Memory Features:**
- CLAUDE.md serves as persistent project context
- Recursive discovery: Searches up directory tree
- Import syntax: `@path/to/file` in CLAUDE.md
- Quick memory: Start message with `#`
- Initialize: Use `/init` to bootstrap

**Context Optimization:**
1. Use `/compact` regularly for long sessions
2. Clear between unrelated tasks
3. Write specific, focused queries
4. Use `.claudeignore` for large files
5. Summarize to scratchpad, start fresh

**Cost Management:**
- Average: ~$6/developer/day
- Monitor with `/cost` command
- Batch related operations
- Use faster models for simple tasks

**.claudeignore Pattern:**
```
# Large generated files
node_modules/
venv/
*.pyc
__pycache__/

# Build artifacts
dist/
build/
*.egg-info/

# Large data files
*.csv
*.json
*.log
```
```
**Benefit**: Better performance and cost management

### 5. Project Initialization Checklist (Add in Development Guidelines)
```markdown
### Project Initialization Checklist
**For New Projects:**
1. Memory Setup:
   - [ ] Create/update CLAUDE.md with context
   - [ ] Add tech stack and constraints
   - [ ] Import key files with `@path/to/file`

2. Environment:
   - [ ] Create `.claudeignore` for performance
   - [ ] Set up virtual environment
   - [ ] Configure `.claude/settings.json`

3. Planning:
   - [ ] Define clear project goals
   - [ ] Create roadmap/scratchpad_[branch].md
   - [ ] Break into milestones
   - [ ] Identify core workflows

4. Development:
   - [ ] Initialize test framework
   - [ ] Set up CI/CD hooks
   - [ ] Run `/doctor` to verify health
```
**Benefit**: Consistent project setup

### 6. Quick Reference Enhancement
```markdown
### Quick Reference
- **Full Command Reference**: See `.cursor/rules/claude_code_quick_reference.md`
- **Test Commands**: `TESTING=true vpython mvp_site/test_file.py` (from project root)
- **New Branch**: `./integrate.sh`
- **Run All Tests**: `./run_tests.sh`
- **Deploy**: `./deploy.sh` or `./deploy.sh stable`
- **Cost Check**: `/cost` to monitor usage
- **Context Cleanup**: `/compact` to reduce size
```
**Benefit**: Points to comprehensive quick reference

## PROPOSED DELETIONS

### 1. Duplicate Git Workflow Sections
**Lines to remove**:
- Second occurrence of "Pull Request Workflow for All Changes" (around line 462)
- Second occurrence of "Detailed Progress Tracking" (around line 386)
- Duplicate "Branch Safety and Push Verification Protocol" content

**Total lines saved**: ~144 lines

### 2. Duplicate Environment Sections
**Lines to remove**:
- Second "Environment, Tooling & Scripts" section (starts around line 576)
- Duplicate Python execution protocol content

**Total lines saved**: ~90 lines

### 3. Duplicate Knowledge Management
**Lines to remove**:
- Second "Knowledge Management & Process Improvement" section (around line 963)
- Duplicate Scratchpad Protocol content

**Total lines saved**: ~36 lines

### 4. Move to lessons_archive_2025.mdc
**Content to archive**:
- Older lessons from June 2024
- Duplicate debugging protocols
- Superseded patterns

**Keep in lessons.mdc**: Only recent (last 30 days) and critical patterns

## SUMMARY OF CHANGES

**Additions**: ~200 lines of new valuable content
- Official commands documentation
- Memory management strategies
- Workflow templates
- Project initialization checklist
- Cost optimization guidelines

**Deletions**: ~270 lines of duplicates
- Remove exact duplicate sections
- Consolidate redundant content
- Archive old lessons

**Net Result**: Document becomes ~70 lines shorter but much more valuable

**New Files to Create**:
1. `.cursor/rules/claude_code_quick_reference.md` - Concise daily reference
2. `.cursor/rules/lessons_archive_2025.mdc` - Historical lessons

## REVIEW QUESTIONS

1. Should I proceed with removing duplicates first?
2. Which new sections would you like me to add first?
3. Any sections you want to keep as-is?
4. Should I create the quick reference file?
5. OK to archive pre-2025 lessons?

Please review and let me know which changes to implement!

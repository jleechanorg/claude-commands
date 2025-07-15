# /handoff Command

Creates a structured handoff for another worker with PR, scratchpad, and worker prompt.

## Usage
```
/handoff [task_name] [description]
```

## What it does

1. **Creates Analysis Branch**: `handoff-[task_name]` from current state
2. **Generates Scratchpad**: `roadmap/scratchpad_handoff_[task_name].md` with:
   - Problem statement
   - Analysis completed
   - Implementation plan
   - Files to modify
   - Testing requirements
3. **Creates PR**: With detailed description and ready-to-implement status
4. **Updates Roadmap**: Adds entry to `roadmap/roadmap.md` 
5. **Generates Worker Prompt**: Copy-paste prompt for next worker
6. **Creates Clean Branch**: `roadmap[timestamp]` for continued work

## Example
```
/handoff logging_fix "Add file logging configuration to main application"
```

Creates:
- Branch: `handoff-logging_fix`
- Scratchpad: `roadmap/scratchpad_handoff_logging_fix.md`
- PR with implementation details
- Roadmap entry
- Worker prompt
- New clean branch for you

## Requirements

- Current work should be analyzed/planned
- Key files and implementation approach identified
- Testing strategy defined

## Output Format

**Primary Output**: Copy-paste ready worker prompt with:
- Setup instructions (worktree navigation, branch checkout)
- Task context and goals
- Implementation plan and timeline
- Success criteria and testing requirements
- File locations and specifications

**Example Output**:
```
🎯 WORKER PROMPT (Copy-paste ready)

TASK: [task_name]
SETUP:
1. Switch to worktree: cd /path/to/worktree_roadmap
2. Checkout handoff branch: git checkout handoff-[task_name]
3. Read specification: roadmap/scratchpad_handoff_[task_name].md

GOAL: [clear objective]
IMPLEMENTATION: [detailed steps]
SUCCESS CRITERIA: [measurable outcomes]
TIMELINE: [estimated hours]
FILES: [key files to create/modify]

START: Read the handoff scratchpad for complete details
```

**Additional Outputs**:
- Handoff branch with complete specification
- PR with implementation details
- Updated roadmap entry
- Clean branch for continued work

## Copy-Paste Instructions

The command generates a formatted prompt that can be directly copied and pasted to hand off work to another developer or AI assistant. The prompt includes all necessary context, setup steps, and implementation guidance for immediate task continuation.
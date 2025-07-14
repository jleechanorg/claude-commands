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

## Output

Returns a formatted worker prompt that can be copy-pasted to hand off the task.
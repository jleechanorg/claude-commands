# Handoff Artifact Schema

When an executor session ends (either by completing its todo or by hitting a context limit), it MUST write a `handoff.md` file to `.hermes/plans/handoff.md`. This file is the ONLY mechanism for preserving state across context resets.

## Schema

```markdown
# Handoff: [Task Title]

## Session Info
- **Session ID**: [ao session name or tmux session]
- **Timestamp**: [ISO 8601]
- **Todo item**: [which T-number was being worked on]
- **Reason**: completed | context_reset | blocked

## Completed Work
- [x] [specific change] — commit: [sha] — files: [list]
- [x] [specific change] — commit: [sha] — files: [list]

## Current State
[Where the implementation stands right now. What's done, what's half-done, what's not started.]

## Partial Changes
[Any files that were modified but not yet committed. Include the diff or describe what was changed.]

## Next Steps
1. [First thing the next executor should do]
2. [Second thing]
3. [Third thing]

## Gotchas Encountered
- [Thing that bit you that the plan didn't anticipate]
- [Pattern that doesn't work as documented in research.md]

## Test Status
- [Test name]: PASS
- [Test name]: FAIL — reason: [why]
- [Test name]: NOT RUN — reason: [why]

## Files Modified
[List of all files touched in this session, with change summary]
```

## Rules

1. **Always write handoff.md before stopping.** Even if you completed the todo — the next executor needs to know what's done.
2. **Be specific about partial changes.** "I was working on the API handler" is useless. "Changed `handleList()` in `api/handlers.ts` lines 45-62 to accept cursor param, but haven't updated the test file yet" is useful.
3. **Include commit SHAs.** The next executor needs to know exactly what's on the branch.
4. **Mark the reason.** "completed" means the todo is done. "context_reset" means you're bailing because of context limits. "blocked" means you hit something you can't resolve.
5. **The next executor reads this file FIRST.** It's the first thing in their prompt. Make it count.

# Ralph Agent Instructions

You are an autonomous coding agent working on a software project.

## Runtime Directories

- **PRD (read-only spec):** `prd.json` in the same directory as this file
- **Progress log:** `$RALPH_RUNTIME_DIR/progress.txt` — ALWAYS write here, never alongside code
- **PRD state (runtime copy):** `$RALPH_RUNTIME_DIR/prd_state.json` — update `passes` here
- **Evidence:** `$RALPH_RUNTIME_DIR/evidence/`
- **App port:** If the project includes a web server, serve it on **port 5555** (not 3000) so browser proof recording captures the correct app

`RALPH_RUNTIME_DIR` defaults to `/tmp/ralph-run` (set by the runner script). Check this env var at startup.

If `$RALPH_RUNTIME_DIR/progress.txt` doesn't exist yet, create it with a header.
If `$RALPH_RUNTIME_DIR/prd_state.json` doesn't exist yet, copy `prd.json` to it first.

## Your Task

1. Read the PRD at `prd.json` (in the same directory as this file) for the full spec
2. Read the runtime PRD state at `$RALPH_RUNTIME_DIR/prd_state.json` (if it exists) for current pass/fail status
3. Read the progress log at `$RALPH_RUNTIME_DIR/progress.txt` (check Codebase Patterns section first)
4. Check you're on the correct branch from PRD `branchName`. If not, check it out or create from main.
5. Implement user stories where `passes: false`, in priority order. Use your judgement for how many to tackle per iteration.
6. For stories with `"type": "verify"`, run the verification (see **Verification Stories** below)
7. For implementation stories, build the code, tests, and commit
8. Run quality checks (e.g., typecheck, lint, test - use whatever your project requires)
9. Update CLAUDE.md files if you discover reusable patterns (see below)
10. If checks pass, commit ALL changes with message: `feat: [Story ID] - [Story Title]`
11. Update `$RALPH_RUNTIME_DIR/prd_state.json` to set `passes: true` for the completed story
12. Append your progress to `$RALPH_RUNTIME_DIR/progress.txt`

## Verification Stories

Stories with `"type": "verify"` are **verification milestones**. They run after implementation stories to confirm everything works end-to-end.

**PRD schema:** Stories may include an optional `"verifyCommand"` field (shell command string). When set, ralph-pair runs this command after each coder iteration and auto-marks the story as passed when the command succeeds. Only use trusted PRD sources—commands are executed in the workspace.

**How to handle a verification story:**

1. Check if the story has a `"verifyCommand"` field — if so, run that exact command
2. If no `verifyCommand`, use the `acceptanceCriteria` to determine what to test
3. Run the verification. If it **passes**: set `passes: true` and continue
4. If it **fails**: set `passes: false`, append failure details to progress log, and **stop** — the next iteration will address the failure

**Verification stories are blocking.** You must not skip ahead to the next implementation story until all preceding verification stories pass.

Stories without a `"type"` field (or with `"type": "implement"`) are normal implementation stories.

### Example PRD with verification stories:
```json
{
  "userStories": [
    {"id": "S1", "title": "Add login page", "type": "implement", "passes": false},
    {"id": "V1", "title": "Verify login page", "type": "verify", "passes": false,
     "verifyCommand": "pytest tests/test_login.py -v"},
    {"id": "S2", "title": "Add dashboard", "type": "implement", "passes": false},
    {"id": "V2", "title": "Verify full flow", "type": "verify", "passes": false,
     "verifyCommand": "pytest tests/test_integration.py -v"}
  ]
}
```

## Progress Report Format

APPEND to `$RALPH_RUNTIME_DIR/progress.txt` (never replace, always append):
```
## [Date/Time] - [Story ID]
- What was implemented
- Files changed
- **Learnings for future iterations:**
  - Patterns discovered (e.g., "this codebase uses X for Y")
  - Gotchas encountered (e.g., "don't forget to update Z when changing W")
  - Useful context (e.g., "the evaluation panel is in component X")
---
```

The learnings section is critical - it helps future iterations avoid repeating mistakes and understand the codebase better.

## Consolidate Patterns

If you discover a **reusable pattern** that future iterations should know, add it to the `## Codebase Patterns` section at the TOP of `$RALPH_RUNTIME_DIR/progress.txt` (create it if it doesn't exist). This section should consolidate the most important learnings:

```
## Codebase Patterns
- Example: Use `sql<number>` template for aggregations
- Example: Always use `IF NOT EXISTS` for migrations
- Example: Export types from actions.ts for UI components
```

Only add patterns that are **general and reusable**, not story-specific details.

## Update CLAUDE.md Files

Before committing, check if any edited files have learnings worth preserving in nearby CLAUDE.md files:

1. **Identify directories with edited files** - Look at which directories you modified
2. **Check for existing CLAUDE.md** - Look for CLAUDE.md in those directories or parent directories
3. **Add valuable learnings** - If you discovered something future developers/agents should know:
   - API patterns or conventions specific to that module
   - Gotchas or non-obvious requirements
   - Dependencies between files
   - Testing approaches for that area
   - Configuration or environment requirements

**Examples of good CLAUDE.md additions:**
- "When modifying X, also update Y to keep them in sync"
- "This module uses pattern Z for all API calls"
- "Tests require the dev server running on PORT 3000"
- "Field names must match the template exactly"

**Do NOT add:**
- Story-specific implementation details
- Temporary debugging notes
- Information already in $RALPH_RUNTIME_DIR/progress.txt

Only update CLAUDE.md if you have **genuinely reusable knowledge** that would help future work in that directory.

## Quality Requirements

- ALL commits must pass your project's quality checks (typecheck, lint, test)
- Do NOT commit broken code
- Keep changes focused and minimal
- Follow existing code patterns
- If remote CI verification is blocked (for example `gh` cannot reach `api.github.com`), capture the exact failing command/error and run local workflow-equivalent checks as evidence in `$RALPH_RUNTIME_DIR/progress.txt`.

## Ralph Fork Isolation

Changes under `ralph/` are intentionally specific to this repository's workflow.
Do not treat this directory as the canonical implementation for the conceptual upstream.
Code changes under `ralph/` must remain isolated to this repo and should not be
submitted upstream unless explicitly requested and reviewed.
Use the conceptual upstream project only for reference and drift checks:

- Conceptual upstream (Snark Ralph): https://github.com/snarktank/ralph
- Keep local adaptations in this fork constrained to repo-specific patterns and paths.
- Do not copy experimental local orchestration changes into the upstream
  `snarktank/ralph` repository without explicit review and a dedicated upstream PR.
- Any `ralph/` behavior changes should be reviewed for interoperability risk before
  proposing or syncing to conceptual upstream.

## Browser Testing (If Available)

For any story that changes UI, verify it works in the browser if you have browser testing tools configured (e.g., via MCP):

1. Navigate to the relevant page
2. Verify the UI changes work as expected
3. Take a screenshot if helpful for the progress log

If no browser tools are available, note in your progress report that manual browser verification is needed.

## Stop Condition

After completing your work, check if ALL stories have `passes: true` in `$RALPH_RUNTIME_DIR/prd_state.json`.

If ALL stories are complete and passing, reply with:
<promise>COMPLETE</promise>

If there are still stories with `passes: false`, end your response normally (another iteration will continue).

## Important

- Use your judgement for how many stories to implement per iteration
- Commit frequently
- Keep CI green
- After each implementation story, run its paired verification story immediately
- Read the Codebase Patterns section in progress.txt before starting

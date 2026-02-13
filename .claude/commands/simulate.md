---
description: Predict next user prompt using $USER simulation
type: ai
execution_mode: immediate
---
## EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately.**

## EXECUTION WORKFLOW

### Phase 1: Gather Conversation Context

**Action Steps:**
1. Determine the current working directory (cwd)
2. Find the Claude project conversation directory by converting the cwd path: replace `/` with `-` (e.g., `/home/user/projects/myrepo` becomes `~/.claude/projects/-home-user-projects-myrepo/`)
3. Find the most recent large JSONL file (sort by mtime, pick the biggest recent one)
4. Extract the last 5-8 user messages from that file using `tail -200` + JSON parsing
5. If arguments were provided (e.g., `/simulate streaming convo`), use those as additional context

### Phase 1.5: Gather Workflow State (P6)

**Run these commands IN PARALLEL to gather current workflow state:**

1. **Git status:** `git status --porcelain=v2 --branch` — determines clean/dirty, branch name, ahead/behind
2. **PR info:** `gh pr view --json number,state,mergeable,statusCheckRollup,isDraft 2>/dev/null || echo "NO_PR"` — PR existence, status, CI
3. **Commits ahead of remote:** `git rev-list --count origin/$(git branch --show-current)..HEAD 2>/dev/null || echo "0"` — whether already pushed
4. **Commits behind main:** `git rev-list --count HEAD..origin/main 2>/dev/null || echo "0"` — drift from main

**Parse results into this structured format:**
```
[WORKFLOW_STATE]
GIT_CLEAN: <true if no modified/untracked files>
PR_EXISTS: <true/false>
PR_STATUS: <OPEN/MERGED/CLOSED/NONE>
PR_NUMBER: <number or NONE>
CI_STATUS: <PASSING/FAILING/PENDING/NONE>
CI_FAILING_CHECKS: <list of failing check names, or empty>
BRANCH: <current branch name>
AHEAD_OF_REMOTE: <number of unpushed commits, 0 = already pushed>
BEHIND_MAIN: <number of commits behind main>
STATUSLINE: [Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```

### Phase 2: Build Simulation Prompt

**Action Steps:**
1. Read the simulation prompt file: `genesis/$USER_simulation_prompt.md` (from project root)
2. Append the conversation context AND workflow state with this format:

```
---

## CURRENT CONVERSATION CONTEXT (PREDICT NEXT PROMPT)

Working directory: <cwd>
Branch: <current git branch>
Additional context: <any args passed to /simulate>

### Workflow State:
[WORKFLOW_STATE]
GIT_CLEAN: <value>
PR_EXISTS: <value>
PR_STATUS: <value>
PR_NUMBER: <value>
CI_STATUS: <value>
CI_FAILING_CHECKS: <value>
BRANCH: <value>
AHEAD_OF_REMOTE: <value>
BEHIND_MAIN: <value>
STATUSLINE: <value>

### Recent conversation history:
USER: <message 1>
USER: <message 2>
...

### YOUR TASK:
Based on everything above, generate EXACTLY ONE predicted next prompt this user would type. Output ONLY the predicted prompt, nothing else. No explanation, no analysis, no markdown formatting, no quotes - just the raw prompt text as the user would type it.
```

### Phase 3: Run Prediction

**Action Steps:**
1. Pipe the full prompt to `claude -p --model sonnet` via Bash
2. Display the result cleanly:

```
============================================================
WORKFLOW STATE:
  Branch: <branch> | PR: <#number status> | CI: <status> | Git: <clean/dirty>
============================================================
PREDICTED NEXT PROMPT:
============================================================
<prediction output>
============================================================
```

### Notes
- Use `sonnet` model (not haiku - quality matters for this)
- The simulation prompt is at `genesis/$USER_simulation_prompt.md` relative to project root
- If the JSONL conversation files aren't found, just use whatever context the user provided as args
- Keep output minimal - user just wants to see the predicted prompt
- The workflow state is CRITICAL for accuracy — it prevents predicting already-completed actions
- If gh CLI or git commands fail, set those fields to UNKNOWN and continue

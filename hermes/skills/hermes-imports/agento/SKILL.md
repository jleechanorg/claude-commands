---
name: agento
version: 1.0.0
description: Delegate coding change tasks to Agent-Orchestrator (AO). Triggered by the keyword "agento" anywhere in a message, or by default for any coding task. Never use mctrl unless explicitly requested.
---

# agento

Use this skill by default for coding change requests.

## When to use

Route coding change requests through Agent-Orchestrator unless the user explicitly asks for mctrl.
Examples:
- "agento spawn worldai-claw-agento fix the login bug"
- "agento status"
- "agento send wa-abc1234 please push your changes"
- "agento fix PR 5879"
- "agento make this PR good"
- "agento keep fixing comments and CI until merge-ready"

## Worktree Requirement

**agento MUST always use a new git worktree** for agent sessions, unless already running inside an AO-managed worktree or session.

- The AO workspace plugin (`worktree`) is configured in `agent-orchestrator.yaml` with `workspace: worktree` for all projects
- Each spawn creates an isolated worktree in `~/.worktrees/<projectId>/<sessionId>/`
- This ensures agents never run directly in the base repo working tree
- Verify: if inside a worktree, `git rev-parse --git-common-dir` should point to the parent repo's .git

## CI & PR Comment Auto-Resolution

**agento automatically resolves CI failures and PR review comments** by default. This is configured in `agent-orchestrator.yaml` reactions:

```yaml
reactions:
  ci-failed:
    auto: true
    action: send-to-agent
    retries: 3
  changes-requested:
    auto: true
    action: send-to-agent
    escalateAfter: 10m
  bugbot-comments:
    auto: true
    action: send-to-agent
    escalateAfter: 30m
```

When AO detects:
- A CI check failure → spawns an agent to fix the issue
- Review comments requesting changes → spawns an agent to address them
- Bugbot comments → spawns an agent to investigate

The agent uses the project's `agentRules` which prioritize:
1. Resolve review comments with minimal safe changes
2. Fix failing CI checks
3. Push fixes and update PR

## AO CLI path

```
~/bin/ao
```

## AO Working Directory (Required)

Run AO commands from:

```bash
cd ~/.hermes
```

`ao` reads `agent-orchestrator.yaml` from the current directory. In this setup, the canonical config is `~/.hermes/agent-orchestrator.yaml` (includes project `$ORG`). Running from unrelated directories can fail with:
`No agent-orchestrator.yaml found. Run ao init to create one.`

## Available projects (from agent-orchestrator.yaml)

- `mctrl-test` — mctrl_test repo (jleechanorg/mctrl_test, branch: main)
- `worldai-pr5879` — WorldArchitect PR #5879 ($GITHUB_REPOSITORY, branch: tailscale_pub)
- `worldai-pr5933` — WorldArchitect PR #5933 ($GITHUB_REPOSITORY, branch: fix/statusline-context-front)
- `worldai-pr5938` — WorldArchitect PR #5938 ($GITHUB_REPOSITORY, branch: codex/3dc97cbc)
- `worldai-pr5942` — WorldArchitect PR #5942 ($GITHUB_REPOSITORY)
- `worldai-pr5955` — WorldArchitect PR #5955 ($GITHUB_REPOSITORY, branch: feat/claw-native-hermes-dispatch)
- `worldai-claw-pr57` — worldai_claw PR #57
- `worldai-claw-agento` — worldai_claw agento clone
- `$ORG-main` — jleechanorg/$ORG main (also used for PR work)

**If PR has no matching project:** Run `cat ~/.hermes/agent-orchestrator.yaml` to see current list, add a new entry following the existing pattern, then spawn. Base repo path for new your-project.com PRs: clone fresh to `~/.worktrees/worldai-pr<N>-repo`.

## Commands

### Spawn a new agent session

Each spawn creates a **fresh git worktree** automatically (default behavior from agent-orchestrator.yaml). The worktree is created in `~/.worktrees/<project>-<session>/`.

```bash
cd ~/.hermes && ~/bin/ao spawn worldai-pr5879 <issue-id>
```

For a freeform task (no issue number), omit the issue argument:
```bash
cd ~/.hermes && ~/bin/ao spawn worldai-pr5879
```

### Spawn for existing PR work (REQUIRED for PR comment/CI remediation)

When the intent is "fix PR comments/CI on PR #N", never pass `N` as the positional issue argument.
Always claim the PR explicitly:

```bash
cd ~/.hermes && ~/bin/ao spawn worldai-pr5879 --claim-pr <pr-number>
```

Optional (assign to current GitHub user during claim):

```bash
cd ~/.hermes && ~/bin/ao spawn worldai-pr5879 --claim-pr <pr-number> --assign-on-github
```

### Check status of all sessions

```bash
cd ~/.hermes && ~/bin/ao status
```

### Send a message to a running session

```bash
cd ~/.hermes && ~/bin/ao send <session-id> "<message>"
```

### List sessions

```bash
cd ~/.hermes && ~/bin/ao session ls
```

## ⚠️ EXECUTION RULE — TOOL FIRST, TEXT NEVER

**NEVER reply with text saying you will do something. DO IT FIRST with a tool call.**

- Wrong: "I'll route this to Agento now..." (text response — BANNED)
- Wrong: "Acknowledged — routing through AO..." (text response — BANNED)
- Right: immediately call exec(`cd ~/.hermes && ao spawn <project> --claim-pr <pr>`) with NO preceding text

If you catch yourself about to say "I'll..." or "Routing..." — STOP. Call the exec tool instead.

## PR Title Tagging (REQUIRED)

**Every PR created by agento MUST have `[agento]` as the first word of the title.**

- Wrong: `fix: resolve CodeRabbit comments`
- Right: `[agento] fix: resolve CodeRabbit comments`

This tag allows the backfill cron (`ai.agento.backfill`) to detect AO-managed PRs and auto-spawn sessions if one is missing.

## Spawn After PR Create (REQUIRED)

After any `gh pr create`, immediately spawn an AO session for it:

```bash
# 1. Create the PR (title MUST start with [agento])
gh pr create --title "[agento] fix: ..." --body "..."

# 2. Get the PR number
PR_NUM=$(gh pr view --json number --jq .number)

# 3. Spawn AO session immediately
ao spawn <project-id> --claim-pr $PR_NUM
```

Both steps are mandatory. Do not create an agento PR without spawning a session.

## Steps

1. Parse the user's intent.
2. Determine the `ao` command (see Commands section above).
3. **IMMEDIATELY call exec tool** — no text before the call:
   ```
   exec: cd ~/.hermes && ao spawn <project-id> --claim-pr <pr>
   ```
4. After the exec call returns, reply with a one-line confirmation: "Spawned `<session-id>` for PR #N."
5. Do NOT wait for the spawn to complete — it runs async in tmux.

<## PR Hardening Loop (Default for Hermes -> agento PRs)

When the request is PR remediation (`fix comments`, `fix CI`, `make PR good`), run AO as an iterative loop using AO-native commands, not custom orchestration logic.

1. Start or reuse the AO session for the target PR.
   - If no PR-bound session exists, create one with `ao spawn <project> --claim-pr <pr-number>`.
2. Run `ao review-check <project>` from `~/.hermes` to let AO detect review blockers and trigger follow-up messages.
3. Send the full remediation objective with `ao send <session> "<message>"`:
   - Resolve all unresolved review comments/threads.
   - Fix failing required CI checks.
   - Push updates and re-run checks.
4. Re-check with `ao status --project <id>` and repeat AO actions while blockers remain.
5. Use `gh pr view` / `gh pr checks` only as verification or evidence if AO status is ambiguous.
6. Repeat until merge-ready (no unresolved blockers + required CI green), or escalate after bounded retries with concrete blocker evidence.

Default rule: if PR was created via Hermes -> agento handoff, stay in AO lane unless Jeffrey explicitly says `mctrl`.

## Notes

- AO dashboard: `http://localhost:3011` - managed by launchd (ai.agento.dashboard)
- Config: `~/.hermes/agent-orchestrator.yaml`
- Sessions live in `~/.agent-orchestrator/` and `~/.worktrees/`
- Notifications: AO posts to #ai-slack-test via the agento-notifier webhook handler
- AO-native remediation is already in AO itself (`review-check` + lifecycle `reactions` for `ci-failed`, `changes-requested`, `bugbot-comments`). Do not build a parallel custom remediation engine in this repo.

**Rate-Limit Handling:** When GitHub is rate-limited, `github-intake.sh` will NOT fall back to unclaimed spawns. Instead, it skips the PR and logs: `RATE LIMIT: --claim-pr failed for PR #N, NOT spawning (will retry next cycle)`. AO lifecycle workers handle spawn/cleanup natively.

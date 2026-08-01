---
name: claudem-fallback-when-ao-minimax-unavailable-2026-07-26
description: |
  Operational recipe for the case where the `ao-spawn-minimax-worker` skill's
  canonical `ao spawn --agent minimax` recipe fails on the host (daemon does
  not have the `minimax` agent registered, or `claudem` is a bashrc function
  not a binary on $PATH). Verified on jleechanorg/agent-orchestrator PR #24
  (issue #8623 follow-up) on 2026-07-26.
---

# claudem fallback when `ao spawn --agent minimax` is unavailable

## Symptom

A user asks to "handle issue X using the claude minimax skill" (or any
phrasing that names the `claudem` / `minimax` worker). The canonical recipe
in `~/.hermes/skills/ao-spawn-minimax-worker/SKILL.md` is:

```bash
ao spawn --project <p> --harness minimax --name <slug> --prompt "<task>"
```

On this host (verified 2026-07-26) the `ao-go` daemon only knows
`agy` / `claude-code` / `codex` / `opencode` / `cursor` / `qwen` / `aider`
(verified via `ao agent ls`). Calling `ao spawn --agent minimax` returns:

```
agent "minimax" is not supported by this daemon; pass a supported --agent or run `ao agent ls`
```

## Fallback recipe (verified 2026-07-26, PR #24)

When the issue already has an existing scoped PR (the canonical case for
"extraction" / "follow-up" / "lifecycle" issues), the right move is:

### 1. Verify the host layout

```bash
# List registered AO agents
ao agent ls
# Expected: agy / claude-code / codex / opencode / cursor / qwen / aider

# List existing worktrees, find the one on the PR's headRefName
git worktree list --porcelain
# Expected: worktree for $HOME/.worktrees/<repo>/<branch>
```

### 2. Source the user-scope rc that defines `claudem`

```bash
# claudem is a bashrc function on this host, not a binary on $PATH
type claudem
# Expected: "claudem is a function" — NOT a path

# The fallback: source the rc first
source ~/.bashrc >/dev/null 2>&1 && claudem --version
# Expected: "<version> (Claude Code)"
```

If `type claudem` returns "not found" after `source ~/.bashrc`, the
wrapper is not installed. Skip this fallback and route through `claude-code`
or `codex` from the registered agent list.

### 3. Dispatch via `claudem -p` from the existing scoped worktree

```bash
terminal(
  command="source ~/.bashrc >/dev/null 2>&1 && claudem -p \"$(cat /tmp/issue-<n>-brief.md)\n\nAdditional: <project-specific instructions>\" --max-turns 20",
  workdir="$HOME/.worktrees/<repo>/<branch>",
  background=true,
  notify_on_complete=true,
  pty=true,
  timeout=600,
)
```

Key flags:
- `background=true` + `notify_on_complete=true` — fires once on exit,
  doesn't burn a foreground poll cycle.
- `pty=true` — required for Claude Code's TUI banner; without it the
  worker hangs.
- `--max-turns 20` — empirical cap. Below 15 the worker often runs out
  before producing a commit; above 25 it consumes too much of the
  gateway session's tool budget.

### 4. Verify durable state in the worktree (NOT the GH API)

```bash
cd <wt>
git rev-parse origin/<branch>          # must match the worker's new commit
git log --oneline origin/main..HEAD    # must contain only the expected commits
git diff --name-only origin/main..HEAD # must match the PR body's stated scope
git diff --shortstat origin/main        # line count sanity check
bash <test-harness>                     # run the project-specific tests
```

If `git rev-parse origin/<branch>` does NOT match the worker's commit
(`tail -30 /tmp/last-process-log` to see what the worker did), the worker
failed to push. Retry with a longer `--max-turns` or escalate inline.

### 5. Defer PR/CI re-verification to a one-time cron when GH is rate-limited

```bash
cronjob action=create \
  --schedule "25m" \
  --name "issue-<n> pr-<N> verification (25m)" \
  --deliver "slack:" \
  --prompt "<re-verify instructions>" \
  --repeat 1
```

The cron prompt should at minimum:
- `gh api rate_limit --jq '{core: .resources.core.remaining, graphql: .resources.graphql.remaining}'`
- `git -C <wt> rev-parse origin/<branch>` (durable state check)
- `gh api repos/<owner>/<repo>/pulls/<N>` (REST, not GraphQL — they have
  separate buckets)
- `gh api 'repos/<owner>/<repo>/commits/<sha>/check-runs'`
- `bash <wt>/<test-harness>`

If `gh api rate_limit` still returns 0 in both buckets after the wait,
post the durable-state proof (local SHA + remote SHA + test pass) as the
final reply and stop. Do NOT keep hammering the API.

## Verified outcome (jleechanorg/agent-orchestrator PR #24, 2026-07-26)

- Worker `claudem -p "..." --max-turns 20` exited with `Error: Reached max turns (20)` after producing commit `7e97d91e1` and pushing it.
- `git rev-parse origin/refactor/8623-coder-silent-false-park-probe` returned `7e97d91e12d6de1879dab20b6f3b96ee393ba3d8` ✓
- `git log --oneline origin/main..HEAD` showed `7e97d91e1` + `6fcb28eee` (only the expected commits) ✓
- `bash scripts/tests/test_coder_silent_false_park_probe.sh` returned exit 0 ("regression tests passed") ✓
- `gh api rate_limit` returned `core_remaining: 4239, graphql_remaining: 0`; subsequent `gh pr view` + `gh api` calls returned 403 with `request_id E540:...` / `E789:...` style IDs.
- Cron `9ec6444eb480` scheduled for +25 min to re-verify the PR/CI state when the rate-limit window resets.

## Trigger phrases

- "use the claude minimax skill"
- "use minimax"
- "use the M3 model"
- "use the minimax worker"
- "use claudem"
- "spin up a minimax worker"
- "do this with the minimax CLI"
- "use ao spawn minimax" (when `ao spawn --agent minimax` fails)

## See also

- `~/.hermes/skills/claude-code-claudem/SKILL.md` — `claudem` binary-vs-function distinction
- `~/.hermes/skills/ao-spawn-minimax-worker/SKILL.md` — canonical recipe (when the daemon has the `minimax` agent)
- `~/.hermes/skills/dispatch-task/SKILL.md` — `ao spawn` routing + pitfalls
- `~/.hermes/skills/finish-the-job/SKILL.md` — the three new pitfalls this reference backs

---
name: long-ta[REDACTED_OPENAI_KEY]
description: "Use when the user asks for a multi-file edit + push + PR task (>5 turns) and steers away from AO worker dispatch. Print mode `claudem -p` is too short for multi-step tasks; tmux mode lets the worker drive to durable end-state while the gateway session polls and acks. Trigger phrases: 'use claude minimax skill to code', 'just dispatch to claude directly', 'dont use AO use claude minimax'. User explicitly steered away from AO on 2026-07-26 (`Slack C0AH3RY3DK6/p1785121729.263359`).
allowed-tools: Bash
context: inline
---

# long-ta[REDACTED_OPENAI_KEY] — Drive a `claudem` worker to PR via tmux

When the user explicitly steers away from AO worker dispatch in favor of a
direct `claudem` (claude + MiniMax) invocation, AND the task is multi-step
(multi-file edit + push + PR is too long for `claudem -p --max-turns 40`), use
this pattern.

## Pre-flight (mandatory)

1. **Verify writable remote** — `gh api repos/jleechanorg/<repo> --jq '.permissions.push'`
   must return `true`. If it returns `false`, STOP — the user owns the repo under a
   different `gh` account.
2. **Confirm no PR collision** — `gh pr list --head <branch> --state open`. If a
   PR with that branch exists, the user's intent overlaps an in-flight PR per
   `never-push-onto-someone-elses-pr-head` — STOP and ask.
3. **Branch from `origin/main`** (not from a feature branch with history) per
   `pr-clean-branch-from-main-no-history-bloat`. Pattern:
   ```bash
   git worktree add -b feat/<topic> /tmp/<wt> origin/main
   ```
4. **Fix .venv symlink if broken** — common Your Project failure:
   `uv` removed the underlying 3.12.12 interpreter and `.venv/bin/python` is
   a broken symlink. Fix:
   ```bash
   ln -sfn /opt/homebrew/bin/python3.12 <wt>/.venv/bin/python
   ```
5. **`MOCK_SERVICES_MODE`** is exported `true` in the parent shell. Always run
   worker commands with `env -u MOCK_SERVICES_MODE ...` per the discoverd
   2026-07-26 lesson.
6. **`gh` token resolution** under `env -i` strips PATH. Resolve `GH_TOKEN` in
   the outer shell BEFORE the wrap.

## Tmux setup (recipe)

```bash
SESSION="<short>-<topic>"
tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -x 140 -y 50
tmux set-environment -t "$SESSION" ANTHROPIC_BASE_URL "https://api.minimax.io/anthropic"
tmux set-environment -t "$SESSION" ANTHROPIC_API_KEY  "$MINIMAX_API_KEY"
tmux set-environment -t "$SESSION" ANTHROPIC_MODEL    "MiniMax-M3"
tmux send-keys -t "$SESSION" "source ~/.bashrc && cd <wt> && claudem" Enter
sleep 8  # wait for claudem welcome banner
```

## Send the brief

Per `claude-code-claudem` skill — long pasted text can be split across two
`[Pasted text #N +M lines]` blocks. Always send TWO literal `Enter` keystrokes
after the paste to guarantee submission:

```bash
tmux send-keys -t "$SESSION" "<task text>" Enter
sleep 2
tmux send-keys -t "$SESSION" Enter
```

Then poll:

```bash
tmux capture-pane -t "$SESSION" -p -S -100 | tail -60
```

## GitHub rate-limit fallback (verified 2026-07-26)

When `gh pr create` returns `API rate limit exceeded` (GraphQL bucket
exhausted, REST still has quota), `gh pr create` is GraphQL-backed and will
also fail. Worker fallback (verified by `claude/MiniMax-M3` worker on PR #8629):

1. Do the edits + `git push` (no API needed).
2. POST to REST endpoint:
   ```bash
   curl -sS -X POST      -H "Authorization: token \$GH_TOKEN"      -H "Accept: application/vnd.github+json"      "https://api.github.com/repos/<owner>/<repo>/pulls"      -d '{"title":"...","head":"<branch>","base":"main","body":"..."}'
   ```
3. Response includes `"URL": "https://github.com/<owner>/<repo>/pull/N"` and
   `"NUMBER": N`. Verify with `curl -sS -H "Authorization: token $GH_TOKEN"
   "https://api.github.com/repos/<owner>/<repo>/pulls/N"` shows `state: open`.

## Slack ack (per dispatched-ta[REDACTED_OPENAI_KEY])

Post ONE short status message in the originating thread within 60s of dispatch:
🟡 In-flight: spawned a claudem worker on branch X from origin/main HEAD Y.
Working dir Z, bead <id>. Posting again when PR is open or 5 min elapsed.

When PR is open: 🟢 PR OPEN: <URL> (NO trailing *).

## Verification before claiming "done"

- `gh api repos/<owner>/<repo>/pulls/<N> --jq '.state'` → `open`
- `git -C <wt> rev-parse HEAD` matches `git -C <main-repo> ls-remote origin <branch>`
- The PR diff matches the user's stated scope; no unrelated drift files
  (per `pr-cleanup-replay` Phase 1 evidence gate).

## Verified case

2026-07-26, $GITHUB_REPOSITORY PR #8629
(`feat/prompt-tier-compression-visenya-v9`, 12 files / +754/-5):
worker applied 5 prompt-only edits, created `evidence/visenya-v9-samples/`
with 8 sample scenes, wrote 11-assertion contract test, single
`ao/MiniMax-M3:` commit, pushed, opened PR via REST fallback after GraphQL
rate limit. Single-shot completion in ~10m wall time.

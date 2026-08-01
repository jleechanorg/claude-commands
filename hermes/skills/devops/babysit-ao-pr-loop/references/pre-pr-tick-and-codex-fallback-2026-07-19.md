# Pre-PR Tick State + Codex-Harness Mid-Spawn Fallback (2026-07-19)

Verified 2026-07-19 on $GITHUB_REPOSITORY, campaign `Cg2m2TkGFFez7XBynEah`, scene 386 Argella suspicion /repro, bead `rev-8rl9z`, worker session `worldarchitect-68`, branch `fix/scene-386-argella-core-memory-repro`, babysit cron `dc31fccf96c3`.

## 1. Pre-PR Tick State (Phase 0 update)

**Symptom:** Worker just spawned, only a fresh branch on a worktree exists, **no PR has been created yet**. Every Phase-0 `gh pr view` either:
- Returns `GraphQL: API rate limit already exceeded` if GraphQL budget is exhausted (common during dispatch window).
- Returns `pull request not found` if GraphQL is fresh.
- Either way: it's NOT a terminal-state signal.

**Wrong response (current babysit prompts as written):** treat "no PR found" as work-done → post closeout → self-cancel cron → user has zero in-flight progress signal.

**Right response (v2.0.0):** Phase 0 step 1 distinguishes (a) PR exists → run terminal-state probe as documented, vs (b) PR does not exist → fall into `PRE_PR_TICK` mode:

```bash
# Determine presence WITHOUT a GraphQL call (REST is usually fine)
TOKEN=$(gh auth token 2>/dev/null)
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/pulls?head=<OWNER>:<BRANCH>&state=open" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))"
# If 0 → PRE_PR_TICK mode
```

**PRE_PR_TICK post format (ONE message per tick, ≤8 lines):**

```
🔵 PRE-PR tick HH:MMZ
  • Worker <session_id>: <ao_session_state> (<harness>)
  • Branch: <branch> | HEAD: <short_sha> | commits since spawn: <N>
  • Pane activity (last 80 lines, summarized): <one-line current action>
  • Next checkpoint: worker push / ao session exit / cron self-cancel
```

**Do NOT self-cancel on `PRE_PR_TICK`.** Only transition to terminal-state mode AFTER `gh`/`curl` returns a non-empty PR list for the worker's branch.

**Counterexample (anti-pattern):** The cron prompt template that just runs `babysit.py poll` without first running the PR-existence REST probe will hit the `gh pr view` undefined-input failure on every early tick. The right recipe is babysit.py poll → if state == "no_pr_yet" → enter PRE_PR_TICK mode instead of the standard terminal-state probe.

## 2. --harness codex Mid-Spawn Fallback

**Symptom (verified 2026-07-19, worldarchitect-66 → worldarchitect-68):**

```text
$ ao spawn --project worldarchitect --harness codex --issue rev-8rl9z --name scene386
spawned session worldarchitect-66 (idle)

# 30s later:
$ ao session get worldarchitect-66
status: terminated
last_exit_code: 0
```

The codex subshell silently dies when its OAuth token has been rate-limited or hit usage cap — `last_exit_code = 0` makes it look healthy while `status: terminated` reveals the truth.

**Wrong response attempts (all observed):**
- `ao session kill <id>` → 60s timeout, no observable progress (the tmux pane is already dead).
- Re-spawn with the same `--harness codex` → same dead-on-arrival subshell.
- Re-spawn with `--harness claude-code` WITHOUT env vars → may inherit whatever default model + config the spawn context has (top-tier sometimes, mid-tier sometimes — unpredictable).

**Right response:**
```bash
# 1. Verify tmux state of the orphan
tmux has-session -t worldarchitect-66 2>&1
# If it returns "can't find session", the tmux pane is already gone and you can skip kill.
# Otherwise: tmux kill-session -t worldarchitect-66 (often faster than ao session kill)

# 2. Re-spawn with claude-code + forced mid-tier
env CLAUDE_MODEL=sonnet ANTHROPIC_MODEL=sonnet \
  $HOME/.local/bin/ao spawn \
    --project worldarchitect \
    --harness claude-code \
    --issue rev-8rl9z \
    --name scene386-sonnet
```

**Verify in the pane what model actually loaded.** Sonnet env vars are *hints*, not contracts. After spawn, capture:
```bash
tmux capture-pane -t <new_session> -p -S -20
# Pane header (Claude Code v2.x.x) shows: "<model_name> with high effort · API Usage Billing"
```
In the 2026-07-19 case the pane header read `MiniMax-M3 with high effort` — the configured standard mid-tier, not "Sonnet" as the env vars requested. **This is normal.** Use whatever model loaded; never spawn a top-tier replacement without explicit user `MERGE APPROVED`-style consent (per SOUL.md `no-confirmation-gate` carve-out for explicit dispatch commands only).

## 3. Steering Pattern (post-spawn `ao send`)

A fresh worker's first turn often starts before it has any project context. The proven pattern is:

1. Write the authoritative task brief to `/tmp/<project>-<topic>/AO-TASK-BRIEF.md` BEFORE spawn.
2. Note the spawn output path: `~/.ao/data/worktrees/<project>/<session_id>`.
3. After spawn confirms `status: working`, immediately `ao send --session <id> --message 'Read <absolute_brief_path> and execute it.'`.
4. The worker's first turn becomes "read the brief + ask clarifying questions" rather than "freelance a generic /repro".

Verify the worker actually reads the brief by `tmux capture-pane | grep 'AO-TASK-BRIEF'` in the next tick.

## 4. Repro-class work ALWAYS uses long cadence

`/repro` investigations routinely take 30-60 minutes end-to-end (Firestore dump + BQ query + static-evidence + draft PR + fix push). Use:
- `repeat: 200` (allows ~16h of 5-min ticks) on the babysit cron.
- `every 5m` cadence.
- `model: "MiniMax-M2.7"` (mini tier) for the cron — the babysit is mechanical observation, not reasoning (subagents inherit the parent model tier unless pinned explicitly).

## 5. References

- `references/single-pr-status-check-no-worker.md` — variant for cron that watches PRs without an AO worker
- `references/cron-prompt-anatomy.md` — prompt field anatomy (`--cron-job-id`, slack channel/thread, base, branch)
- `~/.hermes/skills/finish-the-job/SKILL.md` — for the *initial* dispatch, this companion skill only handles the post-spawn babysit loop

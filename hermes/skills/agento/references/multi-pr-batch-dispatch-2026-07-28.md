# Multi-PR batch dispatch — verified 2026-07-28, $GITHUB_REPOSITORY

Recipe for spawning N AO workers in parallel to drive N existing PRs to green at once. This is the canonical pattern when the user says "let's run /green and /er and iterate until /advice passes" across many open PRs.

## Pre-flight (BEFORE the first `ao spawn`)

Three things will silently waste minutes if not handled up-front:

### 1. AO daemon "ready" ≠ spawn endpoint healthy

Symptom: `ao status` reports `healthz: ok, readyz: ready`, but every `ao spawn` returns `Internal server error (INTERNAL_ERROR)`. The daemon is up but its session-spawn handler is wedged. Verified 2026-07-28 (uptime ~48h before fix).

Fix:
```bash
ao stop 2>&1 | tail -2
sleep 2
ao start 2>&1 | tail -3   # takes 2-3s to bind port 3001
sleep 3
ao status 2>&1 | head -8  # confirm new pid, fresh uptime
```

After restart, `ao spawn` works immediately. The session list survives — no need to re-register workers.

### 2. Project `worker-agent` must be configured

Symptom: `ao spawn --project <X> --prompt "..."` fails with `agent could not be resolved; pass --agent or configure 'ao project set-config <X> --worker-agent <agent>'`. The project may have `agent: "claude-code"` set at the project level but the spawn-time resolver looks at `config.worker.agent`.

Fix (run ONCE per project):
```bash
ao project set-config <X> \
  --worker-agent claude-code \
  --orchestrator-agent claude-code \
  --model minimax/MiniMax-M3 \
  --json
```

Verify:
```bash
ao project get <X> --json | jq '.project.config | {worker, orchestrator}'
# Required: worker.agent="claude-code"
```

Without this, every `ao spawn` on this project fails until the operator runs `set-config` once.

### 3. Draft PRs rejected by `--claim-pr`

Symptom: `ao spawn --claim-pr <N>` returns `failed to claim PR <N>: PR is not open (PR_NOT_OPEN); rolled back session worldarchitect-<id>`. The PR is `state: OPEN` BUT `isDraft: true`. AO refuses to claim drafts (CodeRabbit skips review on drafts; Gate 3 / Gate 4 will block).

Pre-flight filter (run on every PR in the batch BEFORE attempting spawn):
```bash
for n in $PR_LIST; do
  is_draft=$(gh pr view $n --repo OWNER/REPO --json isDraft --jq '.isDraft')
  if [ "$is_draft" = "true" ]; then
    echo "SKIP PR #$n: still draft — needs 'gh pr ready $n' first"
  fi
done
```

Then `gh pr ready <N>` after content review.

## Spawn loop (per-PR)

For each PR in the (filtered) batch, build a CONCISE prompt and spawn. AO enforces a 4096-char prompt cap (per `dispatch-task` SKILL.md); verbose inline recipes will fail with `prompt is too long (PROMPT_TOO_LONG)`.

### Prompt template (~3.5KB, under the cap)

```text
You are an AO worker driving ONE PR to N-green via /green + /er + /advice.

PR #<N> | branch <branch> | HEAD <sha[:8]> | +<adds>/<files>f | mg=<mergeable> | rev=<reviewDecision>

Load these skills first:
1) ~/.hermes/skills/workflow/drive-pr-to-green v2.5.12 — full recipe + pitfalls.
2) ~/.hermes/skills/workflow/always-pr-never-local-edit v1.6.0 — dirty-checkout + worktree trap.
3) ~/.hermes/skills/babysit-stale-watchdog — self-cancel clauses.
4) ~/.claude/skills/advice — /advice synthesis output format.

Hard rules:
- Fresh worktree ONLY: `git worktree add -B <branch>-green /tmp/wa-pr-<N>-green origin/<branch>`. Never edit main checkout.
- Branch from origin/main if rebase needed (SOUL pr-clean-branch).
- Push with `--force-with-lease` only. No --force. No force-push onto non-owned heads.
- Self-cancel on MERGED/CLOSED: `gh pr view <N> --json state`; if terminal, post 1-line closeout to Slack <channel> ts <thread> and STOP.

Loop:
1. /green: pre-flight data (mergeable/draft/head_SHA/legacy status + check-runs). Rebase onto origin/main if CONFLICTING or >5 behind. Re-fetch via `git ls-remote origin <branch>` BEFORE push to avoid race-with-AO-worker. For each failing check: fetch log via `gh api repos/.../actions/jobs/<id>/logs`. If 503 transient: empty commit + push. If CodeRabbit CHANGES_REQUESTED stale: dismiss via PUT /repos/.../pulls/<N>/reviews/<id>/dismissals then empty commit + push. Gate 8 (smoke): dispatch `mcp-smoke-tests.yml` REAL mode, NOT pr-dev-preview MOCK.
2. /er: capture fresh /es bundle at NEW merged HEAD. Update metadata.json.git_provenance.git_head to new SHA. Update PR Evidence section. Re-capture or label (historical) stale wave-N gists.
3. /advice Gate-3 substitute (when CR/Bugbot/Codex all rate-limited): 2 parallel `delegate_task` subagents (Reviewer A source-accuracy w/ file:line; Reviewer B architecture). Synthesize VERDICT/REASONING/RISK/CONFIDENCE/FINDINGS. Post as PR comment via `gh pr comment <N>`.
4. Iterate until Gate-3 APPROVED + Gate-4 Bugbot clean + Gate-6 evidence approved + all GH Actions SUCCESS.
5. Report: post final Slack reply with PR URL + head SHA + 1-line largest-blocker summary. Merge only on explicit user `MERGE APPROVED` (SOUL pr-merge-policy).

Forbidden:
- Editing ~/.hermes/, ~/Library/LaunchAgents/, cron/plist/SOUL.md outside hermes-deploy-pipeline.
- Trusting statusCheckRollup alone (must hit /check-runs).
- Disabling design-doc gates or skipping /es for $PROJECT_ROOT/** production.
- Calling --merge without user approval.

Output: post in Slack <channel> thread <thread> using HERMES_SLACK_BOT_TOKEN. Use colored status sections (Healthy/Risky/Blocked/Next actions). Always append the llm-provenance caveat. If you discover a new non-trivial pattern, run /skillify first.
```

The skill pointers (1-4) cover the long-form recipes; the prompt itself carries only the per-PR state + the per-task hard rules. This is ~3.5KB — under the 4096 cap.

### Spawn command (per PR)

```bash
ao spawn \
  --project <X> \
  --harness claude-code \
  --claim-pr <N> \
  --no-takeover \
  --branch "<original-branch>-green-<N>" \
  --name "pr-<N>-<short-role>" \
  --prompt "<concise prompt above>"
```

- `--claim-pr <N>` — attaches the existing PR to the new session (CodeRabbit review will fire on the new commits).
- `--no-takeover` — refuses if another active session already owns the PR; safer in batch context.
- `--branch <orig>-green-<N>` — keeps the PR's branch as the worktree's HEAD ref so commits land on top, not a parallel branch. The worker pushes with `git push origin HEAD:refs/heads/<orig-branch>`.

### Failure handling during the loop

| `ao spawn` return | Meaning | Action |
|---|---|---|
| `spawned session worldarchitect-N (idle) (claimed https://github.com/.../pulls/<N>)` | Success | Move on to next PR. |
| `failed to claim PR <N>: PR is not open (PR_NOT_OPEN); rolled back session worldarchitect-N` | PR is draft (or closed). The session is auto-rolled back; no cleanup needed. | Note PR as DRAFT, surface to operator for `gh pr ready`. |
| `prompt is too long (PROMPT_TOO_LONG)` | Prompt > 4096 chars | Compress prompt (skill-pointers, not inline recipes). |
| `Internal server error (INTERNAL_ERROR)` | Daemon spawn handler wedged | `ao stop && ao start` (see §1). Retry once. |
| `agent could not be resolved` | Project `worker-agent` unset | `ao project set-config <X> --worker-agent claude-code` (see §2). |

## Post-spawn verification

After spawning N workers, confirm:
```bash
ao session ls --json | python3 -c "
import json, sys
d = json.load(sys.stdin)
spawned = [s for s in d.get('data', []) if s.get('id', '').startswith('<project>-') and not s.get('isTerminated')]
print(f'Live workers: {len(spawned)}')
for s in spawned:
    print(f\"  {s['id']:30s} status={s.get('status', '?'):12s}\")
"
```

Then schedule a one-time status cron per SOUL `one-time-status-cron-after-every-task`:
```bash
hermes cron create "20m" \
  --name '<task-id> status (20m)' \
  --deliver 'slack:<channel>' \
  --repeat 1 \
  'Status check for the N AO workers... [self-cancel-on-merged/closed + report N-green per worker]'
```

`--repeat 1` (NOT `--every`) is mandatory — recurring crons cause notification spam per SOUL `babysit-cron-self-cancel-discipline`.

## Worked example (2026-07-28)

User asked: "find all prompt-focused and difficulty-increasing PRs, run /green + /er + /advice, iterate until it passes." 19 PRs identified. Dispatch loop:

1. Pre-flight: filtered 3 drafts (#8559, #8628, #8531). 16 to dispatch.
2. AO daemon stuck returning 500 → `ao stop && ao start` cleared it.
3. First project `worker-agent` unset → `ao project set-config worldarchitect --worker-agent claude-code --model minimax/MiniMax-M3`.
4. Spawn loop with concise 3.5KB prompts. 18 of 18 claimed successfully after the pre-flight fixes (PR #8559 was draft so excluded from the first 18; later re-checked).
5. Post-spawn: 18 sessions live, all `status=ci_failed` (CI just started on each PR).
6. One-time 20m status cron `677c69e1f337` set; will self-cancel when first PR hits MERGED.

Total time: ~6 minutes for inventory + analysis + 18-worker dispatch + status cron + 2 Slack status messages.

## Anti-patterns

- **Spawning 1 worker per PR and waiting synchronously for each.** Use the parallel batch (max ~5-10 concurrent per host; AO daemon has no hard cap but tmux panes + agent CPU/memory will throttle). Verified: 18 workers in <60s.
- **Sending the full `drive-pr-to-green` v2.5.12 SKILL.md content inline in the prompt.** Hits the 4096-char cap. Always skill-pointer + per-PR state.
- **Skipping the draft pre-flight.** Wastes 1-2 minutes per draft PR with `failed to claim PR <N>` errors and rolled-back sessions.
- **Assuming `ao status` healthz = spawn healthz.** Daemon can report ready while spawn endpoint is wedged. Verified 2026-07-28.

## Cross-references

- `~/.hermes/skills/agento/SKILL.md` — main agento skill, spawn-time model preflight.
- `~/.hermes/skills/workflow/drive-pr-to-green` v2.5.12 — the loop recipe each worker runs.
- `~/.hermes/skills/ao-worker-ground-truth/SKILL.md` — verifies worker progress is real (not just MCP mail fabrication).
- `~/.hermes/skills/babysit-stale-watchdog/SKILL.md` — self-cancel clauses for status crons.
- SOUL `pr-green-dispatch` + `dispatch-on-install` — why this MUST NOT run inline.

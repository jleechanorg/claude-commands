# GHA self-hosted runner pool saturation — recipe (added 2026-07-08)

This is the playbook when **the worker is healthy and polling, but every CI workflow run on the target PR gets cancelled because the org's self-hosted runners are 100% busy**. Distinct from the third failure mode (provider quota block) and from rate-limit-wedge (GH API bucket exhaustion) — this is a runner pool capacity issue, not an agent-side or API-side problem.

## Detection recipe

```bash
# 1. Confirm runners are saturated
gh api 'orgs/<org>/actions/runners?per_page=100' \
  --jq '[.runners[] | {name, status, busy}] | group_by(.status) | map({s: .[0].status, total: length, busy: [.[] | select(.busy==true)] | length})'
# Expected output: [{"s":"online","total":N,"busy":N}]   (busy == total = saturated)
# Or: {"s":"online","total":N,"busy":M} where M < N   (some runners free; retry)

# 2. Confirm the symptom shape — Green Gate cancelled upstream
gh api 'repos/<org>/<repo>/actions/runs?branch=<branch>&per_page=10' \
  --jq '.workflow_runs[] | select(.name == "Green Gate") | {id, status, conclusion, head_sha: .head_sha[0:8], created_at}'
# Expected: every Green Gate run shows conclusion=cancelled, head_sha matches your PR head
# Confirm the upstream cause:
gh api 'repos/<org>/<repo>/actions/runs/<id>/jobs' \
  --jq '.jobs[] | select(.name | contains("Precheck")) | {name, conclusion}'
# Expected: "Green Gate Precheck (Gates 1-6)" conclusion=cancelled
```

The signal is `PRECHECK_RESULT=cancelled` in the downstream Green Gate job log:
```
##[error]GATE 1-6 FAIL: green_gate_precheck job did not complete successfully (result=cancelled)
```

The precheck couldn't dispatch because no self-hosted runner was free within the 20-min window.

## Recovery playbook (verified 2026-07-08, PR #8139)

### Step 1 — Stop re-firing the workflow

`gh run rerun <id>` will keep re-queueing cancelled runs and waste the user's cron/poll budget. Once you've detected runner saturation, **don't call rerun again**. Switch to the local-run contract.

### Step 2 — Run the relevant tests locally + post proof

For PR #8139 (frontend JS only), the worker ran:
```bash
cd ~/.worktrees/worldarchitect/wa-3206
node --test $PROJECT_ROOT/frontend_v1/tests/campaign_wizard_scroll_indicator.test.js
# → 20/20 pass, full TAP output captured
```

Then posted the output as a PR comment with the local-run contract format (per `.cursor/rules/7-green-verification.md` "Local-run command contract"):
```
### local run — CI still pending
- **Git HEAD SHA**: `<sha>`
- **Timestamp**: `<UTC>`
- **Command**: `node --test $PROJECT_ROOT/frontend_v1/tests/...`
- **Output**:
\`\`\`
<TAP / unittest output>
\`\`\`
```

For Python PRs (more common), use the `python -m unittest` pattern from `~/.claude/skills/worldarchitect/`:
```bash
PY="$HOME/projects/your-project.com/venv/bin/python"
TESTING_AUTH_BYPASS=true timeout 90 $PY -m unittest mvp_site.tests.<module>
```

### Step 3 — Refresh visual evidence locally (if applicable)

If the PR ships BEFORE/AFTER screenshots, GIFs, or capture scripts, re-run the Playwright capture script on the current HEAD and commit the refreshed files:
```bash
cd ~/.worktrees/worldarchitect/wa-NNNN
python evidence/capture_scroll_indicator_evidence.py
# → writes evidence/before-*.png, evidence/after-*.png, evidence/scroll-*.gif
git add evidence/
git commit -m "chore: refresh visual evidence on HEAD <sha>"
git push origin feat/<branch>
```

This triggers a fresh CI run for the new SHA — even if it also gets cancelled, the PR's evidence is now provably current.

### Step 4 — Create a babysit cron

```bash
hermes cron create "15m" \
  --name 'PR<NUM> babysit (15m)' \
  --deliver 'slack:<originating_channel>:<thread_ts>' \
  --repeat 1 \
  --delete-after-run
```

Wait — actually for babysit crons you want `--at 15m` (one-time, not recurring). Per `~/.hermes/skills/babysit-stale-watchdog/SKILL.md`, the cron MUST self-cancel on terminal PR state (MERGED or CLOSED). Without `--delete-after-run` and the self-cancel clause in the prompt, the cron leaks forever. Verified broken: `babysit-wa-2366-rev-5deak` cron `728a2ba69e8e` posted every 5 min for 9 days to a PR's thread root.

The babysit prompt should:
1. Poll PR state via `gh pr view`
2. Check check-run conclusions
3. Check runner pool saturation (`gh api orgs/.../actions/runners`)
4. If Green Gate verdict posts = success → post "🟢 GREEN ✅" in originating thread, self-cancel
5. If runners still 100% busy → post one-line "🟡 runners still busy", continue
6. If state == MERGED or CLOSED → self-cancel + single closeout

### Step 5 — Update the bead, don't close it

Per the dispatch-task skill recipe, the bead (`rev-srkvp` etc.) tracks the dispatch, not the merge. Update notes with current state:
- "Code-side GREEN: <test summary>"
- "Infra-side BLOCKED: runner pool saturation, N% busy"
- "Worker: wa-NNNN killed (provider quota OR expiry)"
- "Babysit: cron job_id"

Close only when the babysit cron reports MERGED.

### Step 6 — Kill the dead worker

If the worker has died (provider quota block, OOM, exit) and you've migrated to the babysit cron, kill the worker:
```bash
~/bin/ao session kill wa-NNNN
```

A dead worker still costs nothing on the host but pollutes `ao session ls`.

## Compound failure: quota + saturation

Both can fire in the same drive session. Verified 2026-07-08 on PR #8139:
- Worker hit antigravity quota at 06:09 UTC, reset 43 min later
- After resume, hit quota again at ~08:33 UTC, reset 3h6m later
- Throughout, all 19 self-hosted runners stayed 100% busy

In this state, the worker can't even poll CI to learn the latest gate verdict — it dies before the polling tick. Pivot immediately to the babysit cron path on the FIRST quota hit; don't wait for either quota to recover.

## What NOT to do

- ❌ Keep calling `gh run rerun` — wastes cron/poll budget
- ❌ Wait for the next quota reset hoping it improves — runner saturation is independent
- ❌ Spawn a second worker to "go faster" — adds quota burn, no gain on the actual blocker
- ❌ Post "PR is ready" without the local-run proof — the user-visible blocker is "is CI green", and you must answer that with real evidence, not a hopeful claim
- ❌ Auto-merge the PR "since the code looks right" — that's a merge-safety violation; the green gate exists for a reason
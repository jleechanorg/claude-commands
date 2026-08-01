# Post-Skeptic Green Protocol (v1.5.0)

## TL;DR — Skeptic is RESTORED as a launchd-managed cron (NOT per-repo workflow, NOT a CI check)

As of **2026-07-13** Skeptic is back via [jleechanorg/jleechanclaw#779](https://github.com/jleechanorg/jleechanclaw/pull/779) — but in a different shape than before. **Read this before assuming "skeptic is gone" or "skeptic is a GHA workflow".**

## Status timeline

### Deletion window (2026-07-09)

| Component | Removed by | Status as of 2026-07-13 |
|---|---|---|
| `.github/workflows/skeptic-cron.yml` (per-repo GHA workflow) | commit `1a8c5aef4d` | **replaced by launchd cron** — do NOT re-add per repo |
| `.github/workflows/skeptic-gate.yml` (CI-required check wrapper) | [PR #8217](https://github.com/jleechanorg/jleechanorg/jleechanclaw/commit/384dddceae) | **intentionally absent** — verdict is delivered via PR comment, not a CI check |
| `~/Library/LaunchAgents/ai.hermes.schedule.skeptic-cron.plist` | deleted 2026-07-09 | **replaced by `ai.hermes.schedule.skeptic-auto-merge.plist`** (PR #779) |
| `ao:skeptic-hourly-report` cronjob | disabled 2026-07-09 | still disabled |
| `/skeptic` slash comment trigger | inert 2026-07-09 | **still inert** — verdicts are auto-posted, never in response to a PR comment |

### Restoration (2026-07-13) — what replaced it

| Component | Where | What it does |
|---|---|---|
| `scripts/skeptic_auto_merge.py` | jleechanorg/jleechanclaw ([PR #779](https://github.com/jleechanorg/jleechanclaw/pull/779)) | One launchd-managed cron polls all `jleechanorg/*` repos, dispatches the skeptic review via dark-factory's `runner/skeptic_gate_cli.py` (SHA-pinned, uses AO Go reviewer adapter), auto-merges on `VERDICT: PASS` |
| `runner/skeptic_gate.py` + `runner/skeptic_gate_cli.py` | jleechanorg/dark-factory ([PR #281](https://github.com/jleechanorg/dark-factory/pull/281), branch `feat/issue-278`) | SHA-bound verdict binding library + workflow-facing CLI. Uses the AO Go reviewer adapter at jleechanorg/agent-orchestrator-golang (claudecode/codex/opencode) |
| `ai.hermes.schedule.skeptic-auto-merge.plist` | `~/Library/LaunchAgents/` (installed by operator after PR #779 merges) | 20-min cadence, `KeepAlive.SuccessfulExit=false`, `ThrottleInterval=60` |

## Why this design (not per-repo workflow)

The user explicitly said (2026-07-13, Slack C0BDEAJH8PK):

> "For skeptic cron I dont really wanna install things per repo. Can we have this live in jleechanclaw and use the AO golang reviewer that already exists to redo skeptic and use the AO worker job template to automatically merge PRs?"

The launchd cron + AO Go reviewer pattern satisfies:
- **No per-repo install** — one Python script in jleechanclaw drives all `jleechanorg/*` repos via `gh repo list`
- **Reuse existing AO reviewer** — `jleechanorg/agent-orchestrator-golang/backend/internal/adapters/reviewer/` (claudecode/codex/opencode), invoked through dark-factory's SHA-bound CLI
- **Auto-merge on PASS** — gated on `SKEPTIC_AUTO_MERGE=true` env var (default empty = NO merge, `SKEPTIC_DRY_RUN=true` default = dispatch is also blocked)
- **No CI check required** — verdict is a structured PR comment, not a `Skeptic Gate` check-run. Re-introducing `skeptic-gate.yml` as a required check would re-create the deadlock removed in #8217.

## What "green" means now (post-restore world)

A PR is **7-green merge-ready** when ALL of the following are true:

1. **GH Actions rollups green** — verified via `gh pr checks <N>`:
   - `Green Gate Precheck (Gates 1-6)` → `conclusion: success`
   - `Smoke Gate Wait (Gate 8)` → `conclusion: success`
   - `Green Gate` (the rollup) → `conclusion: success`
   - **Use `.conclusion`, NOT `.state`** — `.state` is null for GH Actions and silently returns 0 failures when CI is red.
2. **CodeRabbit** → `APPROVED` on the latest review (`coderabbitai[bot]` row).
3. **Cursor Bugbot** → no error-severity comments (`cursor[bot]` row).
4. **Merge conflicts** → `gh pr view <N> --json mergeable` returns `MERGEABLE`.
5. **No unresolved non-nit inline review comments** → walk `gh api repos/<owner>/<repo>/pulls/<N>/comments` and confirm zero open items.
6. **Skeptic verdict** → `<!-- skeptic-gate-verdict -->` comment from a trusted author (`github-actions[bot]`, `jleechanao`, `$USER-af`) containing ALL three SHA-pinned markers (`skeptic-cron-trigger-${SHA}`, `skeptic-head-sha-${SHA}`) + `VERDICT: PASS`. **The PR author must NOT be the verdict author (self-approval guard).**

When all six hold, the launchd cron (PR #779) auto-merges IF `SKEPTIC_AUTO_MERGE=true` is set on the daemon env. Otherwise it stays merge-ready pending human `MERGE APPROVED`.

## What babysit cron prompts should do (v1.5.0)

| Aspect | Action |
|---|---|
| Post `/skeptic`? | **No, still inert.** |
| Block waiting for Skeptic verdict? | **No.** Watch for it as a non-blocking event. If the launchd cron has dispatched (visible as `skeptic-gate-verdict` comment with `skeptic-cron-trigger-${SHA}` marker), the verdict may appear in 5-30 min. Report it when it lands. |
| Read `gh pr checks .conclusion`? | **Yes — still required** for gates 1-6. |
| Merge? | **No, requires `MERGE APPROVED`** unless `SKEPTIC_AUTO_MERGE=true` is set on the launchd cron env (the launchd cron owns auto-merge, not the babysit). |
| Detect "skeptic is running"? | **Yes — if `<!-- skeptic-gate-verdict -->` exists for current SHA but verdict is FAIL, post a single-line notice and ask user to `/advice` the verdict.** |

**6-green with no verdict yet (>30 min)?** Post one-liner: "PR #N 6-green ≥30 min, no Skeptic verdict — launchd cron should dispatch soon. If no verdict in 1h, manually run `bash scripts/skeptic_auto_merge.py --repo OWNER/REPO --pr N`."

## Audit recipe — verify Skeptic really is restored (and which shape)

Run this **before** assuming "skeptic is gone" or "skeptic is a per-repo workflow":

```bash
# 1. The launchd cron (the new shape — should exist post-PR #779)
ls ~/Library/LaunchAgents/ | grep -i skeptic
ls ~/.hermes/launchd/ | grep -i skeptic
# Expected: ai.hermes.schedule.skeptic-auto-merge.plist (template + installed)

# 2. The Python driver (should exist)
ls ~/repos/jleechanclaw/scripts/skeptic_auto_merge.py
ls ~/repos/jleechanclaw/tests/test_skeptic_auto_merge.py

# 3. The dark-factory reviewer (the engine — should exist post-PR #281)
gh api repos/jleechanorg/dark-factory/contents/runner/skeptic_gate_cli.py --jq '.download_url'
# Expected: download_url returns (file exists after PR #281 merges to main)

# 4. The legacy per-repo workflow (should NOT exist — 2026-07-09 deletion is permanent)
for repo in jleechanorg/jleechanclaw $GITHUB_REPOSITORY jleechanorg/.github; do
  echo "=== $repo ==="
  gh api "repos/$repo/contents/.github/workflows/skeptic-cron.yml" 2>&1 | head -1
done
# Expected: HTTP 404 (per-repo workflow is GONE, replaced by launchd cron)

# 5. The legacy CI-required check (should NOT exist)
for repo in jleechanorg/jleechanclaw $GITHUB_REPOSITORY; do
  echo "=== $repo ==="
  gh api "repos/$repo/contents/.github/workflows/skeptic-gate.yml" 2>&1 | head -1
done
# Expected: HTTP 404
```

If any of the above shows stale artifacts (e.g. a per-repo `skeptic-cron.yml` workflow re-introduced), escalate — the launchd pattern is the only approved shape.

## Anti-patterns (forbidden by this protocol)

- ❌ **Re-introducing a per-repo `.github/workflows/skeptic-cron.yml`.** The launchd cron (PR #779) is the canonical mechanism. Adding a per-repo workflow file is a regression to the 2026-07-09 deletion and re-creates the runner-queue incident from `your-project.com` bead `rev-z3zus`.
- ❌ **Re-introducing `.github/workflows/skeptic-gate.yml` as a required check.** The Skeptic verdict is delivered via PR comment, not a CI check. Adding a CI check recreates the deadlock removed in #8217 (Skeptic Gate CI waiting for a verdict comment that itself waits for Skeptic Gate to pass).
- ❌ **Posting `/skeptic` to a PR.** The bot that would have responded (`github-actions[bot]`) does not have that trigger wired in the new architecture — verdicts are auto-posted by `dark-factory/runner/skeptic_gate_cli.py`, never in response to a PR comment.
- ❌ **Reading `gh pr checks` `.state` instead of `.conclusion`** — silently returns green when CI is red.
- ❌ **Auto-merging when green** from a babysit. Even with skeptic restored, $GITHUB_REPOSITORY requires explicit `MERGE APPROVED` from the operator unless `SKEPTIC_AUTO_MERGE=true` is set on the launchd cron env. For jleechanorg/jleechanclaw the same default applies — the cron only auto-merges when both `SKEPTIC_AUTO_MERGE=true` AND `SKEPTIC_DRY_RUN=false`.
- ❌ **Self-approval**: a PR author who is also a trusted verdict author cannot satisfy the gate via their own verdict. The SHA-pinned markers + author allowlist + non-self-approval triple guards against this.

## What "red" looks like (real PR-blockers on your-project.com PRs)

Empirical reading from PR [#8290](https://github.com/$GITHUB_REPOSITORY/pull/8290) on 2026-07-09 (branch `feat/daily-level-up-2026-07-08`, MERGEABLE):

| Check | `.conclusion` | Run | What it means |
|---|---|---|---|
| `Green Gate Precheck (Gates 1-6)` | `success` | … | Gates 1-6 individually green |
| `Green Gate` (rollup) | `failure` | runs/29053835894/job/86244776006 | The rollup itself failed — investigate Smoke Gate |
| `Smoke Gate Wait (Gate 8)` | `failure` (25m 11s) | runs/29053835894/job/86240846288 | **Real blocker.** Smoke Gate is the gate the Skeptic verdict used to back-stop. Needs root-cause + fix, not babysit babysitting. |
| `Evidence Gate` | `success` | … | Layer 2 evidence verified |
| `CodeRabbit` | `success` (`Review completed`) | … | Latest review APPROVED |
| `Cursor Bugbot` | `skipping` | … | Optional gate; skipping is benign |

**Action on babysit tick when Smoke Gate fails:** do NOT loop forever. Post ONE summary in the babysit thread naming the failing gate + run URL + a 1-line root-cause hint, then **escalate to a human** (or dispatch `drive-pr-to-green` / `finish-the-job`). Babysits are observe-only — they don't fix CI red.

## Provenance

- **Skeptic deletion (2026-07-09):** `~/.hermes` git log: `54e8ddc70f`, `4594f76502`, `24cf760a4b` are the last install-era commits. PR #8217 (commit `384dddceae`) removed the Skeptic VERDICT poll from Green Gate. commit `1a8c5aef4d` removed the per-repo `skeptic-cron.yml`. Trigger: Jeffrey 2026-07-09 in `C09GRLXF9GR` thread — "Didn't we delete skeptic?" — while a 30-min babysit cron for PR #8290 was still templating the obsolete "awaiting skeptic verdict (≤30 min cadence) and MERGE APPROVED" copy. v1.3.0 lands the same day.

- **Skeptic restoration (2026-07-13):** [jleechanorg/jleechanclaw#779](https://github.com/jleechanorg/jleechanclaw/pull/779) replaces the per-repo workflow with a launchd-managed cron that uses dark-factory PR #281's SHA-bound verdict library + jleechanorg/agent-orchestrator-golang's reviewer adapter. Trigger: Jeffrey 2026-07-13 in Slack C0BDEAJH8PK — "I dont really wanna install things per repo. Can we have this live in jleechanclaw and use the AO golang reviewer that already exists to redo skeptic."

## Related skills

- `~/.hermes/skills/devops/babysit-ao-pr-loop/SKILL.md` — this skill's parent; the canonical babysit cron contract + Phase 0/1/2/3 lifecycle.
- `~/.hermes/skills/babysit-stale-watchdog/SKILL.md` — companion watchdog that reaps babysit crons whose PR is MERGED/CLOSED (defense against terminal-state leak).
- `~/.hermes/skills/finish-the-job/SKILL.md` — end-to-end finish protocol for any task that requires auto-merge.
- `~/.hermes/skills/skills/workflow/always-pr-never-local-edit/SKILL.md` — never stop at local edits; create a GH issue + bead + PR.

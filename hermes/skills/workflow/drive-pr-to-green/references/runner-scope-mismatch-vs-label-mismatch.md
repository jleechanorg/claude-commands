# Runner-scope-mismatch vs label-mismatch — orch-qon7 incident

**Date:** 2026-07-09
**Bead:** `rev-xpr7q`
**Slack thread:** C0BGM3A4ZC0 / 1783645656.590779
**Affected repo:** `$GITHUB_REPOSITORY`
**Hypothesis rule:** "label mismatch" is what an LLM guesses when CI is stuck pending on self-hosted. The actual class is **scope** — repo has zero registered runners despite org having many.

## Symptoms

- Green Gate precheck poller outputs `GATE-1 CHECK-RUNS: pending=["Directory tests (core-mvp-1(self hosted))","Directory tests (core-mvp-2(self hosted))","Directory tests (core-mvp-3(self hosted))","Harness autonomy checks (self hosted)", ...]` for 30 × 5min before `GATE-1 FAIL: CI=pending`.
- `gh api repos/jleechanorg/<repo>/actions/runs?status=queued` shows the named jobs stuck `pending` indefinitely; no failure, no runner pickup, no timeout.
- Workflows reference `runs-on: ${{ fromJson(vars.SELF_HOSTED_RUNNER_LABELS || '["self-hosted"]') }}`.
- Repo-scoped runner count is 0 (`gh api repos/jleechanorg/<repo>/actions/runners --jq '.total_count'`).
- Org runner count is high and all runners `status: online` carrying `[self-hosted, self-hosted-mikey, ezgha]` — they look fine in `gh api orgs/jleechanorg/actions/runners`.
- Repo variable `SELF_HOSTED_RUNNER_LABELS` resolves to `["self-host]"` (1-element) — matches the label, so it's NOT a label problem.

## Root cause

The per-repo ao-runner daemon (`~/.local/share/ao-runner/launchd-start.sh` + `~/.local/share/ao-runner/start-runner.sh`) iterates `~/.ao-runner.d/jleechanorg--*/.env` to spawn repo-scoped runners. The canonical onboarding step for new repos is to add both:

- `~/.config/ao-runner/jleechanorg--<repo>.yaml` (config — labels + image + count)
- `~/.ao-runner.d/jleechanorg--<repo>/.env` (env — REPO_URL + ACCESS_TOKEN + LABELS)

`$GITHUB_REPOSITORY` was bootstrapped into the org after Mar 30 (the latest sibling `.env` mtime) but the onboarding step was not run for it. Existing YAMLs covered: `ai_universe_living_blog`, `jleechanclaw`, `mctrl_test`, `worldai_claw`. `your-project.com` was missing.

Then ~17 of the repo's workflows migrated to `runs-on: ${{ fromJson(vars.SELF_HOSTED_RUNNER_LABELS || …) }}` at different dates. The repo var got set 2026-07-05. After that, every workflow triggered sat pending forever.

## Diagnostic commands (in order)

```bash
# 1. Confirm the symptom is CI=pending, not CI=fail
gh pr checks <PR> --repo jleechanorg/<repo>                    # look for "pending" jobs

# 2. Confirm the gap is runner count, not label
gh api repos/jleechanorg/<repo>/actions/runners --jq '.total_count'            # 0 = scope gap
gh api repos/jleechanorg/<repo>/actions/variables/SELF_HOSTED_RUNNER_LABELS    # value
gh api orgs/jleechanorg/actions/runners --jq '[.runners[] | {name, labels: [.labels[].name], status}] | length'  # N total runners

# 3. Confirm the daemon config is missing
test -f ~/.config/ao-runner/jleechanorg--<repo>.yaml          # should exist; if missing → onboarding skipped
test -f ~/.ao-runner.d/jleechanorg--<repo>/.env               # should exist; if missing → onboarding skipped
ls ~/.ao-runner.d/                                              # what's actually wired
```

## The 3-layer fix (durable; all three required)

```bash
# LAYER A — inline, ~3 minutes, no PR
mkdir -p ~/.ao-runner.d/jleechanorg--<repo>/
TOKEN=$(grep '^ACCESS_TOKEN=' ~/.ao-runner.d/jleechanorg--<closest-sibling>/.env | cut -d= -f2-)
cat > ~/.ao-runner.d/jleechanorg--<repo>/.env <<EOF
ACCESS_TOKEN=$TOKEN
RUNNER_SCOPE=repo
REPO_URL=https://github.com/jleechanorg/<repo>
LABELS=self-hosted,<unique-repo-label>
RUNNER_COUNT=2
RUNNER_IMAGE=myoung34/github-runner:ubuntu-noble
EPHEMERAL=true
DISABLE_AUTO_UPDATE=true
RUNNER_NAME_PREFIX=ao-runner
EOF
chmod 600 ~/.ao-runner.d/jleechanorg--<repo>/.env

cp ~/.config/ao-runner/jleechanorg--<closest-sibling>.yaml ~/.config/ao-runner/jleechanorg--<repo>.yaml
chmod 600 ~/.config/ao-runner/jleechanorg--<repo>.yaml

RUNNER_ENV_FILE=~/.ao-runner.d/jleechanorg--<repo>/.env ~/.local/share/ao-runner/start-runner.sh

# Verify
gh api repos/jleechanorg/<repo>/actions/runners --jq '.total_count'   # now 2
docker ps --filter "name=ao-runner-jleechanorg--<repo>" --format '{{.Names}}\t{{.Status}}'

# LAYER B — dispatch via ao spawn on jleechanclaw (unprotected, self-merge)
# Add probe function to ~/.hermes/scripts/doctor.sh
# Add daily 09:30 PT launchd plist
# Pattern verified by 2026-07-09 babysit watching jc-2009

# LAYER C — dispatch via ao spawn, lands on protected repo via skeptic-cron
# Author ~/.hermes/skills/jleechanorg-self-hosted-runner-registration/SKILL.md
# Add rule to the repo's AGENTS.md
```

## Anti-patterns

- ❌ Stopping after Layer A — the next new repo will hit the same gap (no harness check exists yet).
- ❌ Conflating with pool exhaustion (see drive-pr-to-green pitfall on Skeptic Gate 8) — pool exhaustion shows runners carrying no `pending` jobs because all runners are busy; scope gap shows `pending` jobs because no runner will ever pick them up. Different fix surface.
- ❌ Editing `~/.ao-runner.d/` without mirroring `~/.config/ao-runner/*.yaml` (or vice versa) — launchd-start.sh iterates `.env` files; start-runner.sh reads the YAML only if invoked directly. Symmetry required for daemon-driven restarts.
- ❌ Using a fresh ACCESS_TOKEN per repo — all `jleechanorg/*` runner PATs share the same perms scope. Mirror the sibling's PAT exactly; do not regenerate.
- ❌ Reporting "fixed" before `total_count > 0` AND a real CI run unblocks for the first time. Two-phase verification — config-level (immediately) then end-to-end (next push).

## Provenance

- Green Gate run `29067785614`, precheck job `86283024278`, log line `GATE-1 FAIL: CI=pending` after `poll 30/30` (5min × 30).
- Affected branches at time of fix: `feat/provenance-narrow` (#8292), `worktree_llm_ignore`, `fix/8022-combat-agent-not-activating`, `refactor/process-action-unified-phase-split`, ~10 others.
- Follow-up bead: `rev-xpr7q` (P1 chore). Worker: `ao spawn -p jleechanclaw --bead rev-xpr7q` → `jc-2009` (then self-cancel via babysit cron).
- User instruction that triggered the 3-layer pattern: "Fix it and /harness to root cause how it happened".

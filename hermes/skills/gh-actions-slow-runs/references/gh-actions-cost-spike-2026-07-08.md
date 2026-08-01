# GH Actions Cost-Spike Diagnostic — 2026-07-08 your-project.com

**Provenance:** $GITHUB_REPOSITORY spend alert fired: "GitHub Actions daily Δ $48.51 > $10 (MTD $158.40)". User replied in #worldai-alerts (channel C0BCVG4F560): "Why is it so expensive? Is it because we switched some stuff to gh hosted? If so switch it back."

## Outcome

Diagnosed in ~8 turns. PR [#8285](https://github.com/$GITHUB_REPOSITORY/pull/8285) opened 2026-07-08 by AO session `wa-3226` (bead `$USER-yjq5`) — single squashed commit `2f785a2673` reverting all 3 infra PRs (`#8172`, `#8141`, `#8142`) on `your-project.com/.github/workflows/green-gate.yml` + `hook-tests.yml` (`+30 / −227` across 3 files; the third deleted file is `design/hybrid-runner-failover-design.md`). Status: OPEN, MERGEABLE, NOT a draft; CI pending. **Awaiting `MERGE APPROVED` in originating thread `C0BCVG4F560/ts=1783524611.497499` before squash-merge.** Three infra PRs between July 1–5 explicitly moved workflow jobs to `runs-on: ubuntu-latest` to free self-hosted slots — combined cost ≈ $40–$50/day against a $10/day alert threshold.

**Latent bug fixed in the same revert (verified wa-3226 session, 2026-07-08):** the original hosted `smoke_gate_wait` split (#8141) had a correctness bug — the GitHub-hosted runner started with an empty workspace, so the `[ -f .github/workflows/mcp-smoke-tests.yml ]` file check always failed and Gate 8 was always being skipped silently. The revert PR added an `actions/checkout` step to `smoke_gate_wait` to fix this. **If you ever consider re-splitting any gate job onto a hosted runner, remember that hosted runners don't auto-checkout the workspace** (self-hosted workflows inherit the checkout from the calling workflow; hosted fresh-`runs-on:` jobs do not). The checkout step must be explicit.

## The recipe

### Step 1 — Pull org-level billing usage (the new canonical endpoint)

The legacy `orgs/<org>/settings/billing/actions` endpoint returns HTTP 410 ("moved"). Use:

```bash
gh api "orgs/${ORG}/settings/billing/usage" --paginate 2>/dev/null
```

Requires OAuth scope `manage_billing:org`. Returns paginated `usageItems[]` with fields: `date`, `product`, `sku`, `quantity`, `unitType`, `pricePerUnit`, `grossAmount`, `discountAmount`, `netAmount`, `organizationName`, `repositoryName`.

### Step 2 — Filter to current month + group by SKU

```bash
gh api "orgs/${ORG}/settings/billing/usage" --paginate 2>/dev/null | jq -s '
  [.[].usageItems[]? | select(.product == "actions" and (.date | startswith("'"$(date -u +%Y-%m)"'")))]
  | group_by(.sku)
  | map({sku: .[0].sku, quantity: ([.[].quantity] | add), netAmount: ([.[].netAmount] | add), pricePerUnit: .[0].pricePerUnit, unitType: .[0].unitType})'
```

### Step 3 — SKU → runner type decoder

| SKU | Runner type | Effective rate (post-discount) | Notes |
|---|---|---|---|
| `Actions Linux` | GitHub-hosted Linux (`runs-on: ubuntu-latest` / `ubuntu-22.04` etc.) | ~$0.006/min | **The cost-spike target** |
| `Actions Windows` | GitHub-hosted Windows | ~$0.01/min | Usually trivial |
| `Actions macOS 3-core` | GitHub-hosted macOS | ~$0.062/min | Usually trivial |
| `Actions storage` | Artifact/cache GB-hours | $0.00033602/GB-hr | Almost always <$1 |
| Self-hosted (any OS) | Org's own runners | $0 from GitHub; your cost-of-host | **Does NOT appear in billing API** — this is why self-hosted runners look "free" |

Discount field `discountAmount` is typically ~30–40% of `grossAmount` for `Actions Linux`, bringing effective rate to ~$0.006/min.

### Step 4 — Filter to offending repo

```bash
gh api "orgs/${ORG}/settings/billing/usage" --paginate 2>/dev/null | jq -s '
  [.[].usageItems[]? | select(.product == "actions" and (.date | startswith("'"$(date -u +%Y-%m)"'")))]
  | group_by(.repositoryName)
  | map({repo: .[0].repositoryName, quantity: ([.[].quantity] | add), netAmount: ([.[].netAmount] | add)})
  | sort_by(-.netAmount)'
```

In the 2026-07-08 spike: `your-project.com` had **$155.59 of $158.88 MTD (98%)** and **44,382 of 44,440 minutes (99.9%)** — single-repo concentration is the norm.

### Step 5 — Find workflows pinning to hosted

```bash
cd path/to/offending-repo
grep -l "runs-on: ubuntu-latest" .github/workflows/*.yml
```

The 2026-07-08 spike had 12 workflows on hosted: `bead-jsonl-sort-check.yml`, `bead-pr-lint.yml`, `coverage.yml`, `deploy-production.yml`, `deploy-staleness-gate.yml`, `doc-size-check.yml`, `evidence-gate.yml`, `green-gate.yml`, `runner-checkout-lint.yml`, `skeptic-cron.yml`, `skeptic-gate.yml`, `test-install-guards.yml`.

### Step 6 — Cross-reference with recent workflow changes

```bash
git log --oneline --since="<spike-date-minus-14d>" -- .github/workflows/ | head -30
```

The 2026-07-08 smoking-gun commits:

| Commit | PR | Title | Impact |
|---|---|---|---|
| `ccdd5c8f` (7/5) | [#8172](https://github.com/$GITHUB_REPOSITORY/pull/8172) | `fix(green-gate): move Poll for VERDICT to ubuntu-latest (free 30min x N PRs of self-hosted slots)` | **Biggest driver**: 30-min/PR hosted poll, runs on every PR |
| `68cdaac3` (7/3) | [#8141](https://github.com/$GITHUB_REPOSITORY/pull/8141) | `CI: split Gate 8 smoke poll onto a GitHub-hosted runner in Green Gate` | Smaller long-poll on hosted |
| `6e7b0865` (7/3) | [#8142](https://github.com/$GITHUB_REPOSITORY/pull/8142) | `Design: hybrid runner failover to GitHub-hosted on confirmed jeff-ubuntu outage` | One-time outage workaround; should now be reverted |

Commit message heuristics for spotting hosted-switch PRs:
- `move ... to ubuntu-latest`
- `split ... onto a GitHub-hosted runner`
- `failover to GitHub-hosted on ... outage`
- `hosted-poll`
- `free self-hosted slot(s)`

### Step 7 — Verify self-hosted runners are healthy

```bash
gh api "/orgs/${ORG}/actions/runners?per_page=50" \
  --jq '.runners[] | {name, os, busy, status, labels: [.labels[].name]}'
```

2026-07-08 snapshot: 16 `ez-runner-c-*` Linux + 6 `ez-mac-runner-b-*` Mac, all `online`. The failover rationale no longer holds → safe to revert.

### Step 8 — Compute savings

```bash
# Hosted effective rate: $0.006/min (post-discount)
# Self-hosted accounting rate: $0.002/min (4× cheaper)
# Savings per workflow revert = workflow_min × ($0.006 - $0.002) = $0.004/min
# For the 30-min/PR verdict poll: 30 × $0.004 = $0.12/PR
# Across N PRs/day: $0.12 × N/day
```

2026-07-08 estimate: reverting only PR #8172 (verdict_poll) saves ~$25–$35/day, reverting all 3 saves ~$45–$50/day.

### Step 9 — Post the revert plan + wait for MERGE APPROVED

**Do NOT auto-merge infra PRs in `$GITHUB_REPOSITORY`.** Per `.claude/CLAUDE.md` "Merge safety" + `.cursor/rules/agent-autonomy.mdc`, the user's literal phrase "switch it back" authorizes the *intent* to revert, NOT the merge. The agent must post a 3-option plan and wait for `REVERT-ALL` / `REVERT-<N>-ONLY` / `INVESTIGATE-FIRST`.

The 2026-07-08 plan structure that worked:

```markdown
## Diagnosis (verified from GitHub billing API + workflow files)
[billing breakdown with $ per SKU and per repo]

## The 3 PRs that moved work to hosted (merged July 1–5)
[table: PR# | commit | title | rationale-at-time]

## Cost math
[hosted vs self-hosted rates + expected $/day savings per PR]

## What I need from you
[3 explicit options as single-word triggers]
```

## API gotchas hit during this session

1. **`gh search prs --state all`** → invalid, only `open`/`closed` accepted
2. **`gh api .../actions/runs?status=success`** → invalid (see Pitfall P9)
3. **`gh api .../actions/runs | python3 -c "..."`** via shell pipe → `jq` "Extra data" errors from embedded newlines (see Pitfall P11). **Fix**: redirect to file first
4. **`gh api /repos/<repo>/actions/runs?per_page=100` first page** is dominated by recent `issue_comment` events (PR-bot chatter); cost-driving workflows show up on pages 3+ or via workflow-scoped endpoint `actions/workflows/<id>/runs`
5. **`runner_name` field in job JSON** is a string (`"ubuntu-latest"` / `"self-hosted"`), NOT an object — naive `jq '.runner_name'` works but `.runner_name.os` does not

## Merge unblocker encountered during this revert

PR #8285 (the revert) merged cleanly after the AO worker resolved a stale `copilot_code_review` `CHANGES_REQUESTED` review. The review was on commit `2f785a26` (the first version of the revert), but CodeRabbit itself confirmed in chat that the comments were resolved after the worker's follow-up commit `2027af6b3e`. GitHub's UI does NOT auto-clear a review state when a follow-up commit supersedes the reviewed commit — the formal `reviewDecision: CHANGES_REQUESTED` lingers and blocks the merge with `GraphQL: Repository rule violations found`.

**Fix (verified 2026-07-08):** as the PR author, dismiss the stale review via REST API:

```bash
# Get the review ID and current head
gh api "repos/$OWNER/$REPO/pulls/$PR/reviews" --jq \
  '.[] | select(.author.login=="coderabbitai[bot]") | "\(.id) \(.commit_id)"'
gh pr view $PR --json headRefOid -q .headRefOid

# Dismiss with reason
gh api -X PUT "repos/$OWNER/$REPO/pulls/$PR/reviews/$REVIEW_ID/dismissals" \
  -f message="Review is stale (commit $OLD superseded by $NEW_HEAD). CodeRabbit confirmed in chat: '<quoted statement>'" \
  -f event="DISMISS"
# Returns: {..."state":"DISMISSED"...}

# Verify reviewDecision cleared
gh pr view $PR --json reviewDecision   # should be "" within ~5s
```

The full recipe (including the web-UI fallback paths and the ruleset-toggle escape hatch) is at `workflow/drive-pr-to-green` Step 9a. This skill's reference focuses on the cost-spike recipe only; the merge-unblock lesson lives where it can be applied to any merge-blocked PR, not just cost-spike reverts.

## Cross-references

- `gh-actions-slow-runs/SKILL.md` § "Cost-Spike Diagnosis" — the diagnostic steps (C1–C6)
- `gh-actions-slow-runs/SKILL.md` Pitfalls P9–P13 — the API gotchas
- `scripts/check-hosted-runner-spike.sh` — the reusable verifier
- `~/.hermes/scripts/spend-alert-daily.sh` — the cron that fired the alert (uses `gh api orgs/<org>/settings/billing/usage` + a `gh_roll[]` rolling-window state file)
- `~/.hermes/scripts/gh-actions-cost-monitor.sh` — the legacy monitor (different SKUs, used as backup)
- `~/.hermes/state/spend-alert-state.json` — rolling 7-day delta state, one entry per daily run

## What this recipe does NOT cover

- **Codespaces** cost spikes (different SKU, different billing endpoint)
- **Copilot** cost spikes (separate product, billing API also surfaces it but treat separately)
- **GCP/Gemini/Claude cost spikes** (out of GH Actions scope; `spend-alert-daily.sh` handles these in separate threshold alerts)
- **Rate-limit headers on the billing API** — the usage endpoint is heavy and paginated; if you hit rate limits, the per-org bucket is independent from the per-user bucket (verified `gh api rate_limit` returns separate quotas)

## Verification commands (post-revert)

After the user approves and the revert PR merges, re-run Steps 1–4 and confirm:

```bash
gh api "orgs/${ORG}/settings/billing/usage" --paginate 2>/dev/null | jq -s '
  [.[].usageItems[]? | select(.product == "actions" and (.date | startswith("'"$(date -u +%Y-%m)"'")))]
  | map(.netAmount) | add'
```

Expected: daily `gh_delta` in `~/.hermes/state/spend-alert-state.json` drops below the $10 threshold within 1–2 days of merge (GitHub's billing aggregation has ~24h lag).
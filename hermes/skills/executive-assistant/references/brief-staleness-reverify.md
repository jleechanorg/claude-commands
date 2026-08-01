# Brief-Staleness Re-Verification (added 2026-07-24 08:10 PT sweep)

When a morning brief lands in #ai-general and the operator replies "anything you want me to act on?", the items listed as 🔴 Blocked may have already moved. This reference captures the re-verification protocol + the cross-channel checks that turn a stale brief into an accurate delta.

## The pattern in 90 seconds

A cron-generated brief is composed at minute T and delivered to Slack at minute T+N (where N is the runtime overhead). Between composition and operator-read, anything can happen: a worker can finish a bring-to-green loop, a reviewer can hit "Approve", a CodeRabbit CR can fire. The brief is **not** an authoritative state snapshot — it is a **point-in-time prior session's perspective**.

Operator's expectation when they reply to a brief:
- "tell me what's actually happening right now"
- "do not waste my attention on items that already moved"
- "give me the work that actually needs to be done"

## Re-verification protocol (mandatory)

Before composing a "yes, here's what I'll do" reply to a brief:

### 1. Re-pull every cited PR with `gh pr view`

```bash
gh pr view <N> --repo <org>/<repo> --json number,state,title,mergedAt,headRefName,additions,changedFiles
```

The exact JSON field name is `changedFiles` (NOT `changed_files`). Using the wrong name returns a confusing error like `Unknown JSON field: "changed_files"`. Verified 2026-07-24 08:10 PT.

Classify each cited PR:
- `state=MERGED` → **already done**, cite `mergedAt` and `headRefName` in the reply
- `state=CLOSED` (not merged) → **superseded** — check if a clean replay merged instead; cite the replacement PR number
- `state=OPEN` + `mergeable=MERGEABLE` → **ready for review**, surface in 🟡
- `state=OPEN` + `mergeable=CONFLICTING` → **needs rebase** — surface in 🟡 with a recommended action
- `state=OPEN` + failing Green Gate → **actionable** — surface in 🟡 with the specific failure mode

### 2. Re-pull every cited Slack thread

```bash
curl -fsS -H "Authorization: Bearer ${HERMES_SLACK_BOT_TOKEN}" \
  "https://slack.com/api/conversations.replies?channel=<chan>&ts=<thread_ts>&limit=10"
```

For each operator ask ("did we make X?" / "is Y working yet?"), check whether the most recent message is the operator's question OR an agent's reply. If a reply with PR number / evidence already landed, surface as "answered at ts=..." — DO NOT re-answer.

### 3. Render the reply with three sections

```
🟢 Already done (brief was stale)
• <PR #> — <what moved + proof: mergedAt + head SHA>

🟡 Open, ready for review (all MERGEABLE)
• <PR #> — <one-line state summary + recommended action>

🔴 Real blockers
• <only the items that genuinely need operator attention right now>
```

This three-section format is the **delta against the brief**, not a regurgitation. It explicitly tells the operator "the brief was stale, here is what is actually true now".

## What to NOT do

- **Do NOT spawn AO workers for items the brief flagged as "blocked" without first verifying they are still blocked.** A worker spawned on a merged PR is wasted compute + clutter.
- **Do NOT re-answer an already-answered Slack thread.** Reply to the latest message, not the operator's original.
- **Do NOT paste the brief back at the operator.** They already have it; the value-add is the delta.

## Cross-channel GCP cost verification (when the brief flags a spend alert)

When the brief flags "GCP billing 333%" or similar, get the real breakdown BEFORE recommending fixes:

```bash
# Step 1: get an access token (the bq CLI is broken on Python 3.14 / macOS brew)
TOKEN=$(gcloud auth print-access-token)

# Step 2: BQ REST query (replace worldarchitecture-ai with the actual project)
#         Common gotcha: gcp-cost-diagnosis-bq-billing-export skill points at
#         `worldarchitect-ai` — many orgs use `worldarchitecture-ai` (with the "ure").
curl -fsS -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT service.description as svc, SUM(cost) AS cost FROM `worldarchitecture-ai.billing_export.gcp_billing_export_v1_*` WHERE _PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY) GROUP BY service.description ORDER BY cost DESC LIMIT 8",
    "useLegacySql": false,
    "maxResults": 8
  }' \
  "https://bigquery.googleapis.com/bigquery/v2/projects/worldarchitecture-ai/queries"
```

Then propose 2-3 specific PRs that would directly address the top-line cost driver (in the 2026-07-24 case: rate-limit #8551 + per-user tagging #7314 + cost-reports #8074 to make Gemini API rate-limited per-bucket).

## Worked example: 2026-07-24 08:10 PT triage

Brief flagged 6 items as "🔴 Blocked / needs you":
1. dark-factory #470 → **already merged as #474** (`e7882ecf`)
2. worldai #8488 → **already merged at 12:49 UTC** (V3 overlay replaced pre-V3 file)
3. worldai #8139 → **CONFLICTING; clean replay at #8561 ready** (move from 🔴 to 🟡)
4. ratelimit / difficulty questions → **answered in threads at 1784896196 / 1784896069** with PR numbers #8551 / #8559
5. $PROJECT_ROOT/prompts compaction → **answered at ts=1784898354 with PR #8564**
6. worldai-alerts response_text → **PR #8462 merged at 13:39 UTC** but alerts keep firing — different problem (deployment lag or alert threshold wrong)

Net effect: 2/6 items were real blockers (GCP cost spike + the worldai-alerts flapping alert); 4/6 were stale. The delta-rendered reply gave the operator the real work, not a re-litigation of the brief.

## Cross-references

- `references/asymmetric-bot-channel-access.md` — bot-locked-out fallback for the Slack reads
- `references/github-pr-state-when-rate-limited.md` — `gh pr view` rate-limit fallback when REST is exhausted
- P96 in `SKILL.md` — the canonical pitfall statement

---
name: wa-daily-cron-failure-diagnosis
description: Diagnose daily cron FAILs for Your Project (Dice Audit, Level Up Test, and any future GCP cron job in the `wa-*-daily-*` family). Triggers when a `[GCP Cron] ... - FAIL (...-YYYY-MM-DD)` email arrives, when the `worldai:daily-level-up-and-dice-test-watcher-12h` cron (`8ccfba727015`) posts a FAIL to Slack `#worldai`, when the user says "Daily Dice Audit failed again" / "the daily cron is failing" / "look at my email and fix using /a", or when an AO worker receives a `fix the GCP cron` brief without further context. Classifies failures into FOUR buckets (infra, audit assertion, data-class regression, watcher pipeline), identifies the matching PR fix surface (existing-open vs needs-reopen vs needs-new), and produces a named end-state per `diagnosis-requires-followthrough-or-handoff`. v1.0.0 (2026-07-09) captures the 4-bucket classification, the "PR #7695 was closed instead of merged" recurring trap, and the campaign-fingerprint technique for tracking failure class evolution across days.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [worldarchitect, daily-cron, dice-audit, level-up, gcp-cron, failure-diagnosis, debugging, devops]
    related_skills: [wa-cloud-run-deploy-failure-debug, convergent-bug-triage, dispatch-task, drive-pr-to-green, always-pr-never-local-edit, advice]
---

# WorldArchitect Daily Cron Failure Diagnosis

When a Your Project daily GCP cron job (`wa-daily-dice-audit`, `wa-daily-level-up-test`, or a sibling) produces an exit=1 email, the dispatcher is staring at a **recurring multi-class failure surface** that has already consumed 5+ consecutive days of debugging cycles across multiple sessions. This skill encodes the fast-path triage: classify into one of four buckets, identify the right PR fix surface, and produce a named end-state.

## When this skill fires

- **Email arrives:** `[GCP Cron] Daily Dice Audit - FAIL (daily-dice-audit-YYYY-MM-DD)` (subject format `[GCP Cron] <Job Name> - FAIL (<work-name>-<date>)`) from `$USER@gmail.com`.
- **Slack alert fires:** `:rotating_light: <U09GH5BR3QU> Daily Dice Audit: FAIL (work=daily-dice-audit-YYYY-MM-DD, exit=1)` in `#worldai` (C0AH3RY3DK6), posted by the `worldai:daily-level-up-and-dice-test-watcher-12h` cron (`8ccfba727015`).
- **User requests:** "Daily Dice Audit failed", "the daily cron is failing", "look at my email and fix using /a", "dice audit cron FAIL again", or any class-level equivalent. Bare "Investigate" (no slash trigger) is in-scope — diagnose, name the end-state, do not auto-dispatch.
- **AO worker brief contains** "fix GCP cron" / "green the daily dice audit" / "daily-level-up-test failing" without further context — load this skill FIRST before reading the brief.

## The four failure buckets — classify BEFORE doing anything

Always classify the failure into ONE of these four buckets before recommending a fix. The bucket determines the right PR surface.

### Bucket A: Infra (cron job itself broke)

**Symptom markers** (look for these in the email body):
- `Container called exit(2)` before any audit logs
- `Default STARTUP TCP probe failed`
- `OOM`, `SIGKILL`, `Worker (pid:NNN) was sent SIGKILL`
- `Error: Could not create cloud SQL proxy`, missing service-account env var
- `ModuleNotFoundError`, `ImportError` before audit script runs
- Cloud Run revision logs show the container never started, not the audit output

**Fix surface:** Docker / Dockerfile / Cloud Run job config. NOT in `scripts/audit_dice_rolls.py`. Reference `wa-cloud-run-deploy-failure-debug` skill for the canonical infra-debug protocol.

**Open PRs in this bucket:** None as of 2026-07-09 (most infra PRs already merged).

### Bucket B: Audit assertion (audit script ran, integrity check failed)

**Symptom markers:**
- Email body contains `[FAIL] Visenya v7 (<campaign_id>)` with `[Integrity Failure]` lines
- "impossible values", "unparseable dice notation", "suspicious pattern", "Wrote scenario checkpoint results" / "Wrote summary results" all appear in the log tail
- `=== Results: 0/1 passed` or `0/2 passed` (script ran, audits failed)
- Audit summary block includes `[Integrity Failure]` lines AND `[Ignored Warning]` lines (mixed severity)

**Sub-buckets (further classify):**
- **B1: Same campaign, same failure shape as yesterday** — PR #7605, #7812, #7729, #7607 already shipped benign-skip / brand-new-skip / watermark-empty fixes. The campaign is now stale-data the audit can't triage. Fix surface: backfill or campaign skip.
- **B2: Different campaign, same failure shape as prior weeks** — The audit heuristic is buggy regardless of campaign. Fix surface: open new PR hardening the audit script.
- **B3: Different campaign, NEW failure shape never seen before** — The audit script's regex/parser can't handle a NEW class of dice notation the LLM started emitting. This is the 2026-07-09 case (`xK3fp5XrV24oarIINTF7` / Visenya v7 with concatenated `1d8+3 + 2d6` notation). Fix surface: reopen the structural fix that was merged in pieces but never completed.

### Bucket C: Data-class regression (LLM behavior changed)

**Symptom markers:**
- Same campaign as yesterday, but DIFFERENT failure shape (e.g. yesterday was `1d20=22` impossible values, today is `1d20+10+1d15` concatenated notation on the same campaign)
- New notation types appearing in `dice_audit_events` that weren't there before
- The number of integrity failures per campaign is INCREASING across consecutive days
- Recent prompt-schema-merge PRs in `$PROJECT_ROOT/prompts/shared/` (especially `dice_notation_contract.md`)

**Fix surface:** Re-examine the prompt contract — LLM may have started emitting a NEW notation style after a contract clarification. Two-pronged:
- Audit script: handle the new notation (backwards compat)
- Prompt contract: anti-examples for the new notation (forward-looking)

### Bucket D: Watcher pipeline (cron succeeded, but Slack alert didn't fire)

**Symptom markers:**
- GCP cron exec = `success` in GCP console, but Slack did not get the formatted alert
- `8ccfba727015.next_run_at` is stuck in the past
- `~/.cache/wa_daily_test_watcher/<job>/YYYY-MM-DD.posted` marker file MISSING
- Gateway `~/.hermes/logs/gateway.error.log` shows `Slack API error: message_limit_exceeded` around the time of the cron fire

**Fix surface:** Launcher / cron-scheduler / Slack channel-routing. NOT in audit script. Reference `dropped-messages` and `slack-thread-routing-investigation` skills for the canonical recovery.

## The 7-step investigation protocol (always run in order)

### Step 1 — Verify the watcher fired (or didn't)

```bash
python3 -c "
import json
d = json.load(open('$HOME/.hermes/cron/jobs.json'))
for j in d.get('jobs', []):
    if 'dice' in j.get('name','').lower() or 'wa-daily' in j.get('name','').lower():
        print(f\"id={j.get('id')} last_run={j.get('last_run_at')} next_run={j.get('next_run_at')} enabled={j.get('enabled')} repeat={j.get('repeat')}\")"
```

Also check the marker file:
```bash
ls -la ~/.cache/wa_daily_test_watcher/dice/<TODAY>.posted 2>/dev/null && cat ~/.cache/wa_daily_test_watcher/dice/<TODAY>.posted
```

If the watcher didn't fire, you're in Bucket D. Stop; route to watcher-pipeline fixes.

If the watcher fired and wrote `FAIL` to the marker — go to Step 2.

### Step 2 — Pull the GCP cron email body

```bash
gog gmail search 'subject:"[GCP Cron] Daily Dice Audit" newer_than:3d' --max 3 --no-input
gog gmail get <message_id> --no-input
```

(or whichever job: `Daily Level Up Test`, etc.)

Capture: **execution ID**, **target URL** (stable vs dev), **exit code**, **GCS evidence path**, **results block**, **log tail**.

### Step 3 — Classify into one of the four buckets

Read the email body's `=== Results:` block and the `=== Log Tail (last 80 lines)` block. Apply the bucket markers above. Most failures are Bucket B — within Bucket B, classify into B1/B2/B3.

### Step 4 — Campaign-fingerprint the failure

Use `gh pr list --search "<campaign_id>"` to find which PRs already touched this campaign. Pattern:

```bash
gh pr list --repo $GITHUB_REPOSITORY --state all \
  --search "<campaign_id OR campaign-name>" --json number,title,state,mergedAt,url
```

This answer has three parts:
- **Which PRs already addressed this campaign** (and whether they merged or closed) — tells you what's already been tried.
- **Whether the structural fix is open/merged/closed** — for the dice audit family, this is **PR #7695** (`fix/dice-audit-modifier-guard`). As of 2026-07-09 it is **CLOSED not merged**, which is the most-likely cause of any new B3-class failure.
- **Adjacent open PRs that could absorb this fix** — e.g. #7873 (`cron-exit-semantics-and-oom-watchdog`) for infra-vs-assertion separation, #7596 (emailer-scenario-loader) for the email render bug.

### Step 5 — Identify the right fix surface

| Bucket | Right fix surface |
|---|---|
| A | Dockerfile / Cloud Run config — see `wa-cloud-run-deploy-failure-debug` |
| B1 | New PR: campaign-skip / backfill (~30 lines) |
| B2 | New PR: hard-code the auditor's regex to reject the bad input before chi-square |
| B3 | **Reopen PR #7695** (or equivalent structural fix) + ship tactical stop-gap |
| C | Two PRs in parallel: (1) audit script backwards compat, (2) `dice_notation_contract.md` anti-examples |
| D | `dropped-messages` + `slack-thread-routing-investigation` skills |

When B3 hits and PR #7695 was closed without merging, the fix recipe is: open a NEW PR off `origin/main` with the structural audit refactor + ship a smaller parallel PR for the tactical stop-gap. **Do NOT rebase #7695 onto main** — recreate the branch from `origin/main`, cherry-pick the valuable commits, drop the stale parts, push.

### Step 6 — Produce a named end-state

Per `diagnosis-requires-followthrough-or-handoff`, every diagnosis must end with one of these explicit names:

1. **"apply now"** — fix is ≤10 lines, single-file, reversible, NOT in audit script (e.g. add a campaign-skip rule). Apply inline in same turn. Reply: "Diagnosis complete. Applied the fix inline — <summary + file:line + verification>."

2. **"dispatch now"** — multi-file or >10 lines or needs PR (the B3 reopen case, or any B2). `ao spawn` with a one-line brief OR `bring-to-green` babysit cron. Reply: "Diagnosis complete. Dispatched <worker> on branch <branch> with the recipe."

3. **"hand off explicitly"** — fix is destructive/expensive (data migration, schema, billing, prod deploy) OR user has been upset by auto-fixes. Paste exact 3-5 line shell block + offer to dispatch. Reply: "Diagnosis complete. NOT applying because <reason>. To finish: <shell block>."

Bare "Investigate" / "look at this email" (no `/a`, `/finish`, `/auto`) means **diagnose-then-hand-off**: do NOT auto-dispatch. Reply with the diagnosis + end-state ask: "Reply `/a` to spawn AO worker on the recipe; `apply now` to do the inline fix; `hand off` to paste the exact shell block for you to run."

### Step 7 — Always create a status-cron

Per `one-time-status-cron-after-every-task`, after posting the diagnosis reply, immediately create exactly ONE one-time hermes cron at +20m targeting the same Slack thread:

```
hermes cron create "20m" --name '<job-name> daily-cron FAIL (20m)' \
  --deliver 'slack:<channel>:<thread_ts>' --repeat 1
```

CRITICAL: `--at 20m` (one-shot, fires once); `--delete-after-run`; **NEVER `--every`** (recurring spams the thread). Include the cron job ID in the reply.

## Pitfalls (do NOT do these)

### Pitfall 1: Treating today's FAIL as the same bucket as yesterday's

Bucket B1 and Bucket B3 look similar in the email log tail — both show `[Integrity Failure]` lines and `[Integrity Failure] Campaign ... has unparseable dice notation`. The discriminator is the **campaign ID and shape**: if it's a NEW campaign or NEW notation shape, you're in B3 (structural), not B1 (data stale). Misclassifying B3 as B1 means shipping another partial fix that closes without addressing the parser.

**Detection:** in the email body, look at `=== Results: 0/N passed` — if the failing campaign ID is NEW (search `gh pr list --search "<campaign_id>"` and get ≤1 prior result), it's B3.

### Pitfall 2: Assuming PR #7695 will get reopened automatically

PR #7695 (`fix/dice-audit-modifier-guard`) has been the structural answer since June 2026 but was CLOSED without merging on every reopen cycle. The fix recipe does NOT include "go look at #7695" — it includes "open a NEW structural PR off `origin/main` with the disjoint-union of #7695's commits + tactical stop-gaps." Searching for "#7695" surfaces it; expecting it to be actionable is the trap.

### Pitfall 3: Mistaking a Deploy FAIL for an Audit FAIL

If the GCP cron email shows `Container called exit(2)` or `OOM` BEFORE any audit-script output, it's Bucket A (infra). The audit script never ran. Don't waste cycles reading `scripts/audit_dice_rolls.py`. Hand off to `wa-cloud-run-deploy-failure-debug` and ask whether `Dockerfile` / `requirements.txt` / Cloud Run job memory was changed recently.

### Pitfall 4: Dispatching on bare "Investigate" without an explicit trigger

`no-confirmation-gate`: bare "Investigate" / "look at my email" / "fix this" are NOT dispatch commands. Only `/a`, `/fullrun`, `/finish`, `/auto`, `/f`, `/fin` bypass the confirmation gate. If the user's message is bare, diagnose and name the end-state — let the user invoke the dispatch command. Posting "Should I spawn an AO worker? Y/N" is a SOUL.md violation.

### Pitfall 5: Skipping the "named end-state" — finishing with "want me to fix?"

Every diagnostic reply must end with ONE of: "apply now" / "dispatch now" / "hand off" named explicitly. A reply ending with "Want me to ...?" or "Should I ...?" is a SOUL.md `no-pick-one-menus` violation. The user explicitly opted into autonomous execution by building this skill family, but a structured diagnosis with a named handoff lets them pick precisely.

### Pitfall 6: Bundling Bucket B + Bucket C fixes into one PR

If you're in Bucket C (data-class regression — LLM is emitting a new notation shape), the fix is two PRs in parallel: (1) audit-script backwards-compat (treat new notation as parseable + add to integration test), (2) `dice_notation_contract.md` anti-examples (forward-looking prevention). Bundling them into one PR forces the reviewer to accept both or neither and stalls on review.

### Pitfall 7: Claiming the cron "passed" because no GCP email arrived

The cron can FAIL with exit=1 and the email can be silently dropped (Gmail quota, sandbox block, etc.). Always check `~/.cache/wa_daily_test_watcher/<job>/<TODAY>.posted` AND `gog gmail search 'subject:"[GCP Cron] <Job>" newer_than:3d'`. If the marker file is missing but the email exists, the Slack-alert pipeline died silently. If both are missing, the GCP cron job itself died (Bucket A).

### Pitfall 8: Trusting prior-session PR state instead of re-verifying live (added 2026-07-14)

When a prior session's diagnosis recorded `mergeStateStatus: CLEAN, mergeable: MERGEABLE, CodeRabbit APPROVED`, the next session MUST re-verify those values via REST (`curl -fsS -H "Authorization: Bearer $(gh auth token)" https://api.github.com/repos/<owner>/<repo>/pulls/<N>`) — NOT inherit them as truth. Concrete failures observed 2026-07-14 on PR #8290: the prior session on 2026-07-11 recorded `mergeable: MERGEABLE, mergeStateStatus: CLEAN` on head `7822304264b`. By 2026-07-14T20:19Z, the actual state was `state: OPEN, mergeable: False, merge_state_status: None, head: f81c860e` (new push invalidated the prior head), with the underlying cause being **main drift** — main HEAD advanced from `658445f2` (the PR base) to `69282e01` over the week the PR was open, putting the PR 197 commits behind `origin/main`. Additionally, the evidence bundle authored at `7822304264b` became stale when the new head `f81c860e` was pushed (Evidence Staleness Tolerance rule requires the bundle be re-issued). The symptom was that **3 prior investigation reports** all claimed #8290 was "ready to merge" but the live state was 1-fail/20-pass/9-pending with `mergeable: False` and a stale evidence gate. **Generalizes**: never inherit `mergeable`, `mergeStateStatus`, `headRefOid`, check counts, OR verdict-line text from a prior session's claim — always curl the API and parse the response in the current turn. Treat prior-session conclusions as *leads*, not *facts*. This rule is universal across PR-fix surfaces, not specific to the daily-cron path.

### Pitfall 10: Trusting an EA-sweep telemetry number instead of querying live (added 2026-07-21)

EA sweeps (`memory/briefings/YYYY-MM-DD/<time>-ea-sweep.md`) capture telemetry at brief-time (e.g. 12:00 PT) and reference it again at 16:00 PT. **The numbers in the sweep are not the numbers the user sees now.** Real instance 2026-07-21: sweep reported `is_test IS NULL` Gemini rows went 134 → 161 in 24h and was still "firing daily"; the live `bq query` on `worldarchitecture-ai.llm_forensics.llm_payloads` for the same 24h window returned **0 new NULL rows** (1372 Gemini rows, 0/1372 = 0.00%), and `is_test` populated climbed 67.54% → 82.10% → 92.23% → 93.36% over 4 days. The sweep's "still firing daily" was the watcher's alert-history-count (stale burst from 2026-07-20 17:00 UTC), not live 24h data.

When an EA-sweep BQ/telemetry number drives a Dice Audit action item:

1. Run the live query the sweep referenced: `bq query --project_id=worldarchitecture-ai --use_legacy_sql=false "<the sweep's SQL>"`.
2. Report the live count alongside the sweep's count, named explicitly: "Sweep reported X (12:00 PT); live 24h count is Y (16:30 PT)."
3. If the live number is healthier than the sweep, say so — do not surface the sweep number as the action item without the live qualifier.

This complements Pitfall 8 (PR-state staleness) — both are "session-of-record drift" bugs where a prior snapshot was re-reported as current state. The fix is the same shape: re-derive in the current turn from the canonical source (REST API for PR state; BQ for telemetry; `df -h` for disk), and label any prior number as historical.

### Pitfall 9: Posting the diagnostic via MCP without probing the bot-token scope first (added 2026-07-14)

When the slack-mcp `conversations_add_message` API returns `not_in_channel` (Failure 5f per `slack-thread-routing-investigation`), do NOT stall on the error. Probe `auth.test` with `HERMES_SLACK_BOT_TOKEN` from `~/.bashrc` and `SLACK_USER_TOKEN` from `~/.profile` (`grep '^export SLACK_USER_TOKEN=' ~/.profile | sed 's/^export SLACK_USER_TOKEN=//;s/"//g'`), then `conversations.info?channel=<chan>` with both tokens — the one that returns `is_member: true` is the working path. In practice on `jleechanorg/*` channels, the XOX-P user token (`~/.profile`) is the working path; the XOX-B bot token is workspace-scoped and fails. Then post via Path B curl with the user token, include an identity-disclosure note in the body, and verify via `conversations_replies`. The full sub-class 5f recipe lives in `slack-thread-routing-investigation` Failure 5f — but the daily-cron-specific lesson is: **the diagnostic reply IS the durable artifact**; if you post the diagnosis as a home-channel orphan instead of in-thread, the user will treat the home-channel post as "your reply" and re-ask in-thread. Always verify `ThreadTs == correct_ts` on the verification call.

## Reference and cross-links

- `references/2026-07-09-dice-audit-failure-buckets.md` — session-specific evidence: the GCP cron email body, the four corrupted dice sequences, the d6/d8 impossible value table, and the campaign fingerprint for `xK3fp5XrV24oarIINTF7` (Visenya v7).
- `references/2026-07-14-pr-8290-stale-state-xoxp-fallback.md` — session-specific evidence: 5th-consecutive-day Level Up FAIL (4/8) + Dice Audit (1/2), PR #8290 live state re-verified (head `f81c860e`, base `658445f2`, main HEAD `69282e01`, Evidence Gate FAIL run 29356796837 step "Validate evidence bundle structure"); Pitfall 8 (never trust prior-session PR state) and Pitfall 9 (XOX-P fallback when bot token has no channel scope) — both operationalized here. 2 NEW failure classes (`POST_FINISH_FALLBACK_CHOICES` + `claudem_review 300s timeout`) not in #8290; Visenya V8 (`8Q3ipgQIxRs2YvK1flng`) dice failure linked to PR #8398 /repro evidence.
- `references/2026-07-20-sariel-compound-notation.md` — **NEW** — Sariel Valyria × 2 (`EROaUnSbmDhqBedTbJMg` + `Cg2m2TkGFFez7XBynEah`) FAILED 0/2 with the *same* sequence numbers (96, 296, 486, 488, 832), proving the upstream is the LLM's compound notation class (`1d6+8+2d6+2d8`, `5x 1d20+8`, `54d6+2d8+24`, `Contested Insight (Tully 25 vs ...)`), not the audit script's regex alone. Captures the **two-defect coupling** that today's FAIL surfaces: (D1) `_is_single_die` / `dice_pattern` rejects compound notation → emits "unparseable dice notation" warnings; (D2) when `individual_rolls[]` is missing on a modifier-bearing d20, `_bucket_d20_from_structured` at `audit_dice_rolls.py:613-619` and the chi-square path at `:1283-1299` fall back to using the modified total as the face → emits "impossible values" with samples like [25, 27, 37] / [9, 13, 216] / [6]. The d4 impossible=6 is the same defect — modifier-bearing d6/d8/d20 totals landing in the d4 bucket. Generalizes: **any time "unparseable notation" and "impossible values" both appear in the same audit run, suspect this coupled defect, not two separate bucket failures.** Includes the GCS-evidence fetch recipe (`%2F` URL-encoded path under `download/storage/v1/b/.../o/<encoded-name>?alt=media`), the campaign-fingerprint proof that same-sequence-numbers → same-upstream-cause, and the concrete fix shape (compound-notation expander + skip-not-bucket on modifier totals). Pairs with `hermes-deploy-pipeline` for the orphaned-plist aspect that let this 12:00 UTC FAIL sit 9h silent.
- `~/.hermes/skills/worldarchitect/wa-cloud-run-deploy-failure-debug/SKILL.md` — Bucket A (infra failures) and the Cloud Run revision log discipline.
- `~/.hermes/skills/software-development/convergent-bug-triage/SKILL.md` — sibling-investigation pattern when 3+ issues pile up on one campaign in 24h (a different but adjacent class).
- `~/.hermes/skills/hermes-imports/dispatch-task/SKILL.md` — AO worker dispatch mechanics for the "dispatch now" end-state.
- `~/.claude/skills/drive-pr-to-green/SKILL.md` — for driving the resulting PR through to merge.
- `~/.claude/skills/advice/SKILL.md` — for `/advice` second-opinion on Bucket B3 reopen PRs (the recipe has a history of failing review).
- `~/.cursor/rules/pr-hyperlink.mdc` — for the PR-hyperlink rule when reporting PR list to the user.
- Your Project repo `CLAUDE.md` "Merge safety" section — `MERGE APPROVED` gate on `$GITHUB_REPOSITORY` PRs.

## One-line summary

**Classify into one of four buckets, identify whether PR #7695-class structural fix exists and was merged (or was closed), name the end-state explicitly, do not auto-dispatch on bare "Investigate" — produce diagnosis + named handoff.**

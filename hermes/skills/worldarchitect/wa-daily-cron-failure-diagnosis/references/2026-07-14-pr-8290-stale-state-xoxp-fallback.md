# Daily Cron FAIL — 2026-07-14 — PR #8290 stale-state + XOX-P fallback

## TL;DR

Daily Level Up Test failed 4/8 on 2026-07-14 (5th consecutive day of the same shape), Dice Audit failed 1/2. PR [#8290](https://github.com/$GITHUB_REPOSITORY/pull/8290) is the canonical fix — but **live state had drifted** since the prior session's diagnosis. Three lessons from this session: (1) never trust a prior-session PR-state claim, (2) PR #8290's evidence bundle became stale on a new head SHA, (3) the diagnostic Slack reply needs XOX-P fallback in this workspace.

## Live state at 2026-07-14T20:19Z (REST, Bearer = `gh auth token`)

```
PR #8290:
  state: OPEN, merged: False, mergeable: False, merge_state_status: None
  head SHA: f81c860e0100c6063a906b81f0fe20f046dbfa0e (NEW since 7822304264b on 07-11)
  base SHA: 658445f22403cf46d2a498ff03db3ce89d022fcb
  main HEAD (origin/main): 69282e011d2b5f5b5940c1e5341d66875eb64686
  → PR is ~197 commits behind origin/main
  30 checks: 20 PASS, 1 FAIL (Evidence Gate), 9 PENDING
    - FAIL: Evidence Gate at run 29356796837, step "Validate evidence bundle structure"
    - PASS: Green Gate, Bugbot Gate Wait (Gate 4), Smoke Gate Wait (Gate 8),
            Green Gate Precheck (Gates 1-6), deploy-preview, Real E2E MCP Smoke
  CodeRabbit: APPROVED on prior head 7822304264b
  Bugbot: usage-limit (skipping, not blocking)
  6 commits on feat/daily-level-up-2026-07-08 (chronological):
    6b6a2ac65822 fix(rewards): suppress level_up_available when concluding level-up modal
    8cd5f1fbe219 fix(stream): tolerate 200 OK responses with JSON content type in stream parser
    f52444ca960b Merge remote-tracking branch 'origin/main' into feat/daily-level-up-2026-07-08
    7822304264b5 [fixpr codex-automation-commit] fix PR #8290 lint and tests
    d41d26d4f142 Merge remote-tracking branch 'origin/main' into local-pr8290-work
    f81c860e0100 fix(test): update deploy.sh capability-probe contract test for PR #8381 format
```

## Prior-session state (recorded by 2026-07-11 investigation — now stale)

```
PR #8290:
  state: OPEN, mergeable: MERGEABLE, merge_state_status: CLEAN
  head SHA: 7822304264b5357f529582a7fbb56848ed805e47
  30 checks: 30/30 PASS
  /er verdict: PASS at 12:26:14Z (supersedes 10:33Z FAIL)
  /skeptic: posted 12:26:36Z, awaiting verdict
  CodeRabbit: APPROVED 2026-07-11T21:50:14Z
```

The 2026-07-11 report said "fully N-green, awaiting your merge." That was true AT THE TIME. By 2026-07-14T20:19Z, the head had advanced (commit `f81c860e` pushed today) and main had moved on (`69282e01` vs base `658445f2`). The new push invalidated the evidence bundle (authored at `7822304264b`) and the merge state became `mergeable: False`.

**Pitfall 8 (added 2026-07-14)**: never inherit `mergeable`, `mergeStateStatus`, `headRefOid`, check counts, OR verdict-line text from a prior session. Always REST-curl and parse in the current turn.

## Today's failures (mapped to PR #8290 patches)

| # | Scenario | Root cause | PR #8290 patch |
|---|---|---|---|
| 1 | `real_llm_classifier_exit_path` (campaign `qFr6c5Sj`) | `classifier_exit_free_text_finish: immediate response has rewards_box.level_up_available=true without canonical level-up planning choices` | commit `6b6a2ac` — `canonicalize_rewards` suppresses `level_up_available` when same-response closes the modal |
| 2 | `single_organic_level_up` (campaign `MSDGbtLe`) | `process_action stream path: malformed or missing done payload. An unexpected error occurred while streaming. Chunk events received: 0.` | commit `8cd5f1f` — `collect_route_stream_events` Content-Type check + synthesized `done_payload` on `application/json` |
| 3 | `projected_level_up_button_text` (campaign `hmxp4Igg`) | Same `level_up_available=true` + NEW secondary `POST_FINISH_FALLBACK_CHOICES (RED): post-finish story turn has only server-generated fallback choices (continue_story); model must return real gameplay choices after level-up finish` | commit `6b6a2ac` covers PRIMARY. SECONDARY is NEW failure class — needs follow-up PR. |
| 4 | `multi_level_organic_progression` (campaign `H3tTMn2`) | `multi_level_organic_progression_final: claudem leveling review timed out after 300 seconds` | NOT in #8290. NEW failure class — Gemini review gemini-bot hits 5min timeout on multi-level scenarios. |

Plus Dice Audit (1/2 FAIL):
- Visenya V8 (`8Q3ipgQIxRs2YvK1flng`): `Campaign 8Q3ipgQIxRs2YvK1flng has unparseable dice notation at sequence 714: Auto-Success...`
- **This campaign was the SAME one I /repro'd into PR #8398 earlier today** (SHA `53ea9d30ad`, scene 466 dupe, HISTORICAL RED ARTIFACT verdict). Sibling symptom on `dice_audit_events`.
- PR #7695 (`fix/dice-audit-modifier-guard`, structural audit refactor) was **CLOSED on 2026-07-13, never merged**. Today's dice failure is the same shape as 2026-07-13's `Bg3 Nocturna good (6IL5OTf3RpPrXA5yDu42)` FAIL — Bucket B1.

## Pitfall 9 — the XOX-P fallback in action

The `mcp__slack__conversations_add_message` API returned:
```
{"error":"not_in_channel"}
```

That's Failure 5f per `slack-thread-routing-investigation`. The probe sequence that worked:

```bash
# 1. Discover the working token. ~/.bashrc has SLACK_MCP_XOXP_TOKEN (not the one we want);
#    ~/.profile has SLACK_USER_TOKEN (the one we want).
TOK="$(grep '^export SLACK_USER_TOKEN=' ~/.profile | sed 's/^export SLACK_USER_TOKEN=//' | sed 's/"//g')"

# 2. auth.test — confirm the token resolves
curl -fsS -X POST "https://slack.com/api/auth.test" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/x-www-form-urlencoded"
# → {"ok":true,"url":"https://jleechanai.slack.com/","user":"$USER","user_id":"U09GH5BR3QU"}

# 3. conversations.info — confirm $USER is a member of the channel
curl -fsS "https://slack.com/api/conversations.info?channel=C0AH3RY3DK6" \
  -H "Authorization: Bearer $TOK"
# → is_member: True

# 4. Post via Path B (curl chat.postMessage) — see slack-thread-routing-investigation Path B
#    Body uses Python heredoc to construct JSON safely (the body is large, ~3KB):
python3 -c "import json; print(json.dumps({...}))" > /tmp/slack_payload.json
curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @/tmp/slack_payload.json
# → {"ok":true,"channel":"C0AH3RY3DK6","ts":"1784060458.290349",...}

# 5. Verify via conversations.replies — pass criteria: new MsgID ThreadTs == original thread_ts
curl -fsS "https://slack.com/api/conversations.replies?channel=C0AH3RY3DK6&ts=1784030452.318509&limit=5" \
  -H "Authorization: Bearer $TOK"
# → new ts 1784060458.290349, user=U09GH5BR3QU ($USER, not bot)
#   text starts with ":mag: *Daily Level Up Test (2026-07-14..."
```

**Identity disclosure**: the body included *"(Posted via XOX-P fallback path — bot token has no scope on this channel; reply appears under @$USER user, not the bot)"* as the second paragraph so the user wouldn't be confused by the identity switch.

## Recommendations from this session

1. **MERGE APPROVED on PR #8290** — dispatch an `ao spawn` worker to drive rebase + re-evidence + re-skeptic + merge. ETA 2-4h wall-clock with babysit cron pattern. Cannot do this inline (per `env-preferences.mdc` and repo `AGENTS.md`).
2. **Open follow-up beads** for the 2 NEW failure classes:
   - `POST_FINISH_FALLBACK_CHOICES` (`projected_level_up_button_text` secondary) — prompt-contract patch
   - `claudem leveling review timed out after 300 seconds` (`multi_level_organic_progression`) — increase timeout in `testing_mcp/lib/claudem_review.py` or rate-limit the scenario
3. **NEW structural dice-audit PR off `origin/main`** — PR #7695 was closed. The Visenya V8 "Auto-Success..." notation class on `8Q3ipgQIxRs2YvK1flng` is the same shape as PR #8397's `/repro` scene 466 dupe from today.

## Status cron

`a03415c0105e` — one-time `+20m` per `one-time-status-cron-after-every-task`. Self-cancels.
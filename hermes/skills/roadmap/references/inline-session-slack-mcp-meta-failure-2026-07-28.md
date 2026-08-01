---
name: inline-session-slack-mcp-meta-failure-2026-07-28
description: Verified detection recipe + degradation contract for inline `/roadmap` invocations in operator DM sessions where Hermes canonical Slack bot tokens are `invalid_auth`. Detected 2026-07-28 18:30Z in `C09GRLXF9GR` thread `1785284642.327189`. Companion to SKILL.md Step 0.
---

# Inline-session Slack MCP meta-failure — detection + degradation

**Detected:** 2026-07-28 18:30Z
**Thread:** `C09GRLXF9GR / 1785284642.327189` (operator `/roadmap` invocation)
**Audit scope:** inline-session partial audit pushed to `jleechanorg/roadmap` at commit `1ae742423ccaf4a520d50b22157c1cb612512e1c` ([report](https://github.com/jleechanorg/roadmap/blob/main/reports/2026-07-28-1830Z-roadmap-report.md))

## The trap

The `/roadmap` skill is designed for two invocation surfaces:

| Surface | Slack MCP available? | Hermes-bot identity authed? |
|---|---|---|
| **Cron-launched** (`launchd` at 9am/5pm PT) | Yes (`mcp__slack__conversations_history`, `_replies`, `chat.postMessage`) | Yes (`U0AEZC7RX1Q`) |
| **Inline** (user types `/roadmap` in operator DM) | **No** (tool list doesn't include `mcp__slack__*`) | **No** (`invalid_auth` for `HERMES_SLACK_BOT_TOKEN`) |

The skill's existing SKILL.md assumed Surface 1 by default. When Surface 2 fires (inline), Steps 2-4 (Slack thread classification) and Step 8 (post URL back to thread) cannot run. Steps 1, 5, 6, 7 (window resolve, `gh api graphql` PR inventory, report build, push to roadmap repo) **can** run — they use `gh` + `git`, not Slack. The result: a polished report that looks authoritative because § A/B/D/E look real but § C is missing/carry-over.

This is a NEW class of meta-failure that the existing Step 2.5 (thread-classification logic) didn't anticipate. Step 2.5 addressed: "given the Slack data, how to classify it correctly". This new pitfall addresses: "what if Slack data isn't reachable at all?".

## Diagnostic recipe (run BEFORE Steps 1-8)

Five checks — pass all 5 = full audit (cron surface); fail any = degraded audit (inline surface).

### Check 1 — `auth.test` for Hermes-bot identity

```bash
curl -fsS -X POST "https://slack.com/api/auth.test" \
  -H "Authorization: Bearer ${HERMES_SLACK_BOT_TOKEN:-}" 2>&1
```

**Expected outcomes:**

| Result | Interpretation |
|---|---|
| `{"ok":true,"user_id":"U0AEZC7RX1Q","bot_id":"B...","team":"$USER AI"}` | Cron surface — full audit |
| `{"ok":false,"error":"invalid_auth"}` | Inline surface — degraded audit |
| `{"ok":true,"user_id":"U0A4G7LDJ4R","bot_id":"B0A3MS7G08P"}` | `mcp_agent_mail` identity only — cross-workspace fallback for some channels but NOT operator channels |

**Verified 2026-07-28 18:30Z:**
```
$ curl -fsS -X POST "https://slack.com/api/auth.test" \
    -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" 2>&1
{"ok":false,"error":"invalid_auth"}
```

### Check 2 — `mcp__slack__*` tool reachability

The runtime tool list (visible in session header / system prompt) should include `mcp__slack__conversations_history`, `mcp__slack__conversations_replies`, `mcp__slack__conversations_add_message`. If none are listed → inline surface.

**Verified 2026-07-28 18:30Z:** tool list contains `terminal`, `read_file`, `write_file`, `patch`, `search_files`, `execute_code`, `web_search`, `web_extract`, `browser_navigate`, `vision_analyze`, `cronjob`, `memory`, `skill_*`, `session_search`, `delegate_task`. **No `mcp__slack__*` tools.**

### Check 3 — `SLACK_USER_TOKEN` fallback (XOX-P path)

Per SOUL.md `slack-cross-workspace-fallback-xoxp`: when `mcp__slack__conversations_add_message` is NOT in tool list AND session is cross-workspace-scoped, fall back to `SLACK_USER_TOKEN` ($USER XOX-P identity) via `curl -X POST https://slack.com/api/chat.postMessage`. **Verified 2026-07-28: `printenv SLACK_USER_TOKEN` returned empty in this session** — the XOX-P fallback path is also unavailable. Reason: the bashrc-source pattern (`launchd-env-wrapper.sh`) sources tokens only when invoked from a launchd job context; inline sessions skip that wrapper.

### Check 4 — `agento` worker surface

`~/bin/ao spawn` works in both surfaces (verified). Steps 8.5 #1 (AO dispatch) can still run if needed.

### Check 5 — git + gh auth (for the push half)

```bash
git -C ~/roadmap rev-parse HEAD origin/main
gh auth status
```

**Verified 2026-07-28:** both work. The push-half (Steps 5, 6, 7) of the pipeline is unaffected by Slack auth state.

## Degradation contract (when any of Checks 1-3 fail)

```markdown
## A. Executive Summary

- **Coverage caveat (READ FIRST):** This run was triggered inline by the
  user in #all-$USER-ai. The Hermes canonical Slack bot (`U0AEZC7RX1Q`)
  tokens are not authed in this session (verified `auth.test → invalid_auth`).
  Only the `mcp_agent_mail` identity is authed, cross-workspace-scoped.
  **Steps 2-4 + 8 of the /roadmap pipeline were NOT executed.**
  Sections below are derived from `gh api graphql` PR data + carry-over
  from the most recent cron-launched report.
```

**Specific actions:**

1. **Skip Steps 2-4** entirely. Do NOT attempt `mcp__slack__conversations_history` or `curl ...conversations.history`.
2. **Skip Step 8** (post URL back to thread). Replace with inline-fallback: emit the report URL + 4-section Slack-native reply in the assistant channel. Surface `CRON-NOW` + `POST-TO-CURRENT-THREAD` triggers.
3. **Carry over § C** from `reports/<latest-timestamp>-roadmap-report.md` — read the prior cron-launched report and pull items still in `pending` / `needs-human-decision` / `STUCK` state.
4. **§ B / § D / § E** are real (from `gh api graphql search(...)`). § B table MUST show `mergeStateStatus` for every entry (verified 2026-07-28: `dark-factory#252` returned `UNSTABLE` — needs API merge path, not `gh pr merge`).
5. **§ A MUST start with the `Coverage caveat` banner.** No exceptions. Polished § B/D/E without the banner is exactly the trap that Step 0 prevents.

## Recovery paths

### Path A — Cron-tick nudge (preferred)

Trigger the next cron-launched run immediately:

```bash
launchctl kickstart -k gui/501/ai.hermes.schedule.roadmap-audit
```

Cron surface has Hermes-bot identity + `mcp__slack__*` tools + writes to `#ai-general` (per SOUL.md `slack-channel-routing-policy`). Result: full audit posted to Slack within ~30s of kickstart.

### Path B — Wait for next scheduled tick

Cron cadence: 9am PT + 5pm PT Mon-Fri. If the inline invocation is at 18:30Z (11:30 PT), the next tick is 17:00 PT same day (00:00Z next day, 5.5h wait). Surface as `CRON-WAIT` trigger if user wants the canonical full sweep instead of the partial now.

### Path C — Operate in `mcp_agent_mail` identity only

`mcp_agent_mail` is the agent-to-agent coordination mailbox. It can post to its own workspace channels but NOT operator channels (`#all-$USER-ai`, `#worldai`, `#ai-general`). Not a viable recovery for inline `/roadmap` since the user's source thread is operator-channel.

## Verified instance — 2026-07-28 18:30Z (this thread)

**Inline audit commit:** `1ae742423ccaf4a520d50b22157c1cb612512e1c` on `jleechanorg/roadmap` `origin/main`. Report file: `reports/2026-07-28-1830Z-roadmap-report.md`. Section A opened with the `**Coverage caveat**` banner. § B populated from `gh api graphql search(...)` (181 open PRs across 5 repos). § C carry-over from `reports/2026-07-27-0122Z-roadmap-report.md` (`ee31839`).

**§ B candidates live-verified APPROVED:**
- `jleechanorg/jleechanclaw#803` — MERGEABLE + APPROVED + CLEAN (`mergeStateStatus=CLEAN`)
- `jleechanorg/claude-commands#340` — MERGEABLE + APPROVED + CLEAN
- `jleechanorg/dark-factory#252` — MERGEABLE + APPROVED + **UNSTABLE** (API merge required)

**Slack reply delivery:** NOT posted (Step 8 failed). Reply body drafted at `/tmp/roadmap-reply-body.md` (3477 chars, 4 GitHub URLs, no `*` adjacent per `no-trailing-asterisk-pr-urls`). Posted to assistant channel only — user reads the reply as the in-session assistant turn.

**Park branch:** `sidekick-parking-2026-07-28-1830Z` holds 4 prior sidekick commits that were rebased off `main` before the report push. Stash `stash@{0}: pre-roadmap-2026-07-28-1830Z` holds user's local WIP. Both recoverable post-audit.

## Pitfalls to share with sibling skills

- **`hermes-agent`** — should document the inline-vs-cron surface distinction for any other skills that depend on `mcp__slack__*` (e.g. `dropped-messages`, `slack-thread-token-watch`, `dark-factory-slack-ops`). The general lesson: inline sessions in operator DMs lose Hermes-bot Slack auth; cron sessions retain it.
- **`agento`** / **`dispatch-task`** — `gh` + `git` + `ao` work in both surfaces. Don't add Slack-tool prerequisites to AO spawn recipes unless you've verified the auth.
- **`slack-thread-routing-investigation`** — this skill already encodes the `mcp__slack__conversations_history` reachability failure mode; the Step 0 recipe here is a generalization of that pattern for any skill that uses `mcp__slack__*`.

## Verified anti-patterns

- ❌ "I'll attempt the audit anyway and see how far I get." → produces a polished partial report without a banner. The user reads § B/D/E as authoritative and acts on carry-over § C without knowing it's stale.
- ❌ "I'll retry the Slack API a few times." → token is `invalid_auth`, not transient. Retry waste.
- ❌ "I'll spawn an AO worker to do the audit." → AO workers spawn in fresh sessions without the user's session context. They'd do the same degradation dance from a different tool set.
- ❌ Silently dropping Steps 2-4 from the report without the banner. → the audit looks complete.
- ✅ Run Check 1-3 first, then either defer (`CRON-NOW` / `CRON-WAIT`) OR run Steps 1+5-7 with the banner. Reply is honest about coverage gaps.
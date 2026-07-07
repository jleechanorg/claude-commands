---
name: dropped-messages/daily-escalation-thread-reply
description: Reply shape for `mcp_agent_mail`'s "Dropped-thread escalations | YYYY-MM-DD — daily thread" — distinguishes false-positive (work landed) from genuine (work incomplete) escalations and proposes durable cron fixes. Verified 2026-06-20 on 2-thread daily summary.
type: reference
---

# Daily escalation thread reply (2026-06-20)

> **Verified 2026-06-20 (`C09GRLXF9GR/1781943718.882359` "Dropped-thread escalations | 2026-06-20 — daily thread"):** 2 escalations from today's batch, both false-positive drops where the work was actually complete. Reply landed at `ts=1781944392.117119` with classified list + 4 durable-fix options as a single-decision prompt.

## The pattern

`mcp_agent_mail` posts **one daily escalation thread** in `#all-$USER-ai` (channel `C09GRLXF9GR`) with the title `*Dropped-thread escalations* | YYYY-MM-DD — daily thread`. The body of that thread is a series of `[Dropped-thread escalation] Gave up after 3 nudges with no resolution — needs your review: <slack-url>` messages, one per thread that the dropped-thread-followup cron has now permanently `gave_up=true`'d on.

This is **not the same as a top-N redrive**. The user did not ask for a ranking — the cron is the one asking, and the agent's job is to:
1. Read each escalated thread to determine if the work is actually incomplete (genuine escalation) or already done (false positive).
2. Reply once per day with the classified list + durable fixes the cron needs.

## Step 1 — Find today's escalations in the log

The `dropped-thread-followup.sh` log is the source of truth:

```bash
# All "ESCALATED + GAVE UP" events
grep "ESCALATED + GAVE UP" ~/.hermes/logs/dropped-thread-followup.log
# Today's only
grep "ESCALATED + GAVE UP" ~/.hermes/logs/dropped-thread-followup.log | grep "$(date +%Y-%m-%d)"
```

Each line is `[ISO_TS] ESCALATED + GAVE UP (max nudges 3): <channel> <thread_ts>`. From there, you have the channel + ts of every thread that hit `gave_up=true` today.

## Step 2 — Classify each escalation (false positive vs. genuine)

For each thread, run `mcp__slack__conversations_replies(channel_id=<chan>, thread_ts=<ts>, limit=30)` and check:

| Signal | Means |
|---|---|
| **Original message is RFC 2606 / `fake-` / `nonexistent-` / `placeholder` host** | **False positive** — the alert is from a deliberate test fixture. The cron's "Action: ssh <host>" can never succeed because the host doesn't resolve. No work is missing. |
| **Agent replied with "this is intentional / a test / your own monitor" + PR(s) open or merged** | **False positive** — the work is shipped, the cron just can't tell. |
| **PR open for the fix + agent posted status reply with the PR URL** | **False positive** — the work landed in the thread, the cron's lookback just expired before the agent's long-turn reply finished. |
| **Original message asks a diagnostic question, agent answered it, user has not replied** | **Borderline** — the work is done, but the user might want a follow-up. Classify as "false positive, no action needed" unless the user re-pinged. |
| **Original message is a real task, agent never replied, no PR/work exists** | **Genuine** — the work is actually missing. Surface as a real escalation. |
| **Agent replied with timeout / 401 / 2064 / "high load"** | **Genuine (infrastructure)** — the message was never delivered to a model. Diagnose the platform storm. |

The 2 verified cases from 2026-06-20:

1. **`C09GRLXF9GR/1781811316.528099` "Ubuntu runner health DOWN: nonexistent-test-host-fake-abc-zzz.invalid"** → false positive. Hostname has `.invalid` (RFC 2606 reserved) + `fake-` baked in. Original message was from Jeffrey's own test of his new monitor `self-hosted-oss/ubuntu-runner-health.sh`. Work shipped: PR [$GITHUB_REPOSITORY#7666](https://github.com/$GITHUB_REPOSITORY/pull/7666) merged (monitor), [PR #7699](https://github.com/$GITHUB_REPOSITORY/pull/7699) open (followup filter fix).

2. **`C0ALSKLU9KM/1781865483.314139` "Why is agy not installed / shouldn't be default CLI for AO"** → false positive. Agent's long turn shipped [jleechanorg/jleechanclaw#649](https://github.com/jleechanorg/jleechanclaw/pull/649) (surgical 9-line fix: `worldarchitect.agent: claude-code`) before the reply landed in the thread. The cron's lookback window expired between the work landing and the agent's status post.

## Step 3 — Reply shape for the daily summary

The user is reading **one message that covers all of today's escalations**. The shape:

```
**Dropped-thread audit | YYYY-MM-DD (daily)**

Found **N escalations** today + M older thread(s) still being polled.
[N] are false-positive drops from the cron not recognizing "work complete" replies.
[M] are genuine (if any).

---

**1. `<chan>/<ts>` — <short summary of the original ask>** (escalated <time>)

- **Origin:** <one line: who asked, what was the actual context>
- **Status of the work:** Complete. <PR link + state>. <what the work landed, in 1 line>
- **Why the cron kept firing:** <one specific cron heuristic that misfired>

---

**2.** ... (repeat)

---

**Pattern:** <one-sentence description of the systemic cron failure mode that produced the false positives>

**Proposed fixes** (pick one, or none):

1. **Add a `gave_up_after_work_landed` rule** — if the thread contains a PR link or `## User Stories` completion marker, treat as resolved regardless of parent text.
2. **Patch the cron to detect RFC 2606 / `fake-` / `nonexistent-` targets** in the "Action" field and skip them as obvious test fixtures.
3. **<thread-specific durable fix>** — e.g. "Drive PR #7699 to green so the followup is done and the test-alert thread can be archived."
4. **Leave as-is** — the daily escalation thread is doing its job (giving you a single place to see what's stale).

Standing by — say which.
```

Length: 30-50 lines for 2 escalations. Scales linearly with escalation count.

## Step 4 — Post the reply (which bot?)

The daily escalation thread's parent message is from `U0A4G7LDJ4R` (MCP Agent Mail bot), so the reply is from a bot, not from Jeffrey. The natural choice is **Hermes** (`U0AEZC7RX1Q`, the agent), since the user is reading a thread that the agent will work on. Use `mcp__slack__send_message` with the 3-part `target=slack:CHAN:THREAD_TS` form, OR `curl chat.postMessage` with explicit `channel=C09GRLXF9GR` + `thread_ts=1781943718.882359` + `text=...` in the JSON payload.

Do NOT post as MCP mail bot (`U0A4G7LDJ4R`) here — that identity is reserved for redrive replies where the bot itself is the source of the prompt. The daily escalation thread is a `mcp_agent_mail` thread, but the *content* of the reply is the agent's classification + proposed fixes, not a redrive ordering.

## Step 5 — Durable fixes (if the user picks option 1, 2, or 3)

The 4 proposal options are pre-classified:

| Option | Fix lives in | Effort |
|---|---|---|
| 1. `gave_up_after_work_landed` rule | `~/.hermes/scripts/dropped-thread-followup.sh` (line ~89, `was_nudged_recently`) + new `has_work_landed()` check on PR URLs / completion markers in the thread | ~30 lines bash |
| 2. RFC 2606 / test-fixture detector | Same script, new `is_test_alert()` heuristic on the "Action" field | ~10 lines bash |
| 3. Thread-specific durable fix | Specific PR (e.g. PR #7699 bring-to-green) | existing `drive-pr-to-green` skill applies |
| 4. Leave as-is | None | 0 |

For options 1 and 2, follow the staging-vs-prod patch discipline: edit `~/.hermes/scripts/dropped-thread-followup.sh` (staging, git-tracked), verify with `DRY_RUN=1 bash <script>`, then `cp` to `~/.hermes_prod/scripts/dropped-thread-followup.sh` to catch up prod. Launchd runs staging, so the cron picks up the fix on the next tick. See `references/cron-staging-prod-drift-2026-06-17.md` for the full pattern.

## Tool-call budget

- 1 `grep` for today's `ESCALATED + GAVE UP` events
- 2 `mcp__slack__conversations_replies` (one per escalated thread, to read context)
- 1 `mcp__slack__send_message` or `curl chat.postMessage` to post the daily summary
- = **4 tool calls total** for a 2-escalation day. Scales linearly.

## Anti-patterns

- **Reply with one of these menus per escalated thread** (e.g. "Thread 1: want me to (a) ... (b) ... (c) ...? Thread 2: want me to (a) ... (b) ... (c) ...?"). The user gets a daily escalation thread specifically to avoid N menus. The reply must be ONE consolidated message with N classified items + 4 proposed durable fixes.
- **Skip the cron-side analysis.** "Work landed, moving on" without naming the cron's specific heuristic that misfired leaves the systemic bug in place. The user reads the daily summary specifically to see patterns, not just the per-thread status.
- **Patch the script without verifying the dry-run first.** `bash -n` + `DRY_RUN=1 bash <script>` are mandatory before claiming the fix is live. Launchd runs staging; prod is stale by default.
- **Post as the MCP mail bot** (`U0A4G7LDJ4R`). That's for redrive replies. The daily summary is the agent's classification, not a redrive.
- **Skip the chronological ordering of the 3rd "gave up" being the final one.** A new agent reading the daily summary might think the cron is still misbehaving on a thread. Note explicitly: "3rd 'gave up' was the script's INTENDED final escalation per the existing `gave_up=true` short-circuit."

## What this is NOT

- **Not a redrive ranking.** The user did not ask for top-N. The cron is asking, and the agent classifies.
- **Not a per-thread recovery reply.** Each escalated thread already has its own prior agent replies; the user is reading the daily summary specifically to *avoid* re-opening each one.
- **Not a "what's the status" status read.** The work is either done or not; the daily summary classifies, it doesn't speculate.

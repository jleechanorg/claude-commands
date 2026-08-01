# 2026-07-15 — Failure 5h: xoxb token can POST but cannot READ on the same channel (asymmetric bot-scope on read surfaces)

## TL;DR

The Slack `xoxb-...` bot token is asymmetrically scoped on `conversations.replies` (read) vs `chat.postMessage` (write). On the same channel, in the same session:

| Surface | xoxb (bot) | xoxp (user) |
|---|---|---|
| `chat.postMessage` | ✓ `ok: true` returned, message lands | ✓ same |
| `conversations.replies` | ✗ `{"ok": false, "error": "not_in_channel"}` | ✓ returns full thread JSON |
| `conversations.history` | ✗ same `not_in_channel` | ✓ same |

This is **NOT Failure 5f** (which is "bot cannot POST" — different error path). It's the read-side complement: same workspace, same channel, but the bot was installed in the channel with `chat:write:user` (write scope) but **not** `channels:read` / `groups:read` (read scope) for THAT specific channel. The asymmetry is silent — you only discover it when you try to verify your post.

## The exact pattern observed (2026-07-15 cron check-back, thread `C09GRLXF9GR / 1784162993.289959`)

The cron prompt was a one-shot check-back on PR #17 of `jleechanorg/disk_magician`. After collecting PR state via `gh api`, the script needed to (1) post the +20m report to Slack and (2) verify the post landed.

```bash
source ~/.bashrc 2>/dev/null
TOKEN="${HERMES_SLACK_BOT_TOKEN:-$SLACK_BOT_TOKEN}"  # resolves to xoxb-... in this env

# Step 1: post the report
curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"channel":"C09GRLXF9GR","thread_ts":"1784162993.289959","text":"..."}'
# → ok:true, ts:1784164631.183479, bot_id:B0A3MS7G08P   ✓ post landed

# Step 2: verify the post landed in the right thread
curl -fsS "https://slack.com/api/conversations.replies?channel=C09GRLXF9GR&ts=1784162993.289959&limit=20" \
  -H "Authorization: Bearer $TOKEN"
# → {"ok":false,"error":"not_in_channel"}              ✗ read blocked

# Step 3: try the MCP layer
mcp__slack__conversations_replies(channel_id="C09GRLXF9GR", thread_ts="1784162993.289959")
# → {"error": "not_in_channel"}                         ✗ same

# Step 4: pivot to user token
USER_TOKEN="${SLACK_MCP_XOXP_TOKEN}"
curl -fsS "https://slack.com/api/conversations.replies?channel=C09GGLXF9GR&ts=1784162993.289959" \
  -H "Authorization: Bearer $USER_TOKEN"
# → ok:true, 45 messages in thread, newest has ts 1784164631.183479 ✓ verified
```

The KEY observation: **xoxb returned `not_in_channel` on the EXACT channel where `chat.postMessage` from the same xoxb just succeeded.** A naive read of the 5f literature would assume that means the bot isn't in the channel at all — but the post proves it is.

## Why this matters

Verification is mandatory after every Slack post (per SKILL.md "Verifying a post landed correctly"). The verification path is **separately scoped** from the write path. Code that assumes "post worked, so verify will work" is wrong.

When the verification fails, the natural fallback ladder is:
1. Re-post with the same xoxb — WRONG, the post landed but verification didn't work
2. Fall through to Path A (MCP `conversations_add_message`) — WRONG, MCP `conversations_replies` returns the same `not_in_channel`
3. Fall through to xoxp — RIGHT, xoxp has user-side read scope that xoxb lacks

Discovering this empirically costs 1-2 extra curl calls (one to discover xoxb fails, one to try xoxp). The right skill capture is: **after the post call, prefer xoxp for verification by default when the channel is the operator-direct line or the home channel** — these are the highest-likelihood candidates for the asymmetric-scope case.

## Root cause hypothesis (why Slack does this)

A Slack bot installed in a workspace can be granted channel-level read scope on a per-channel basis (via `/invite @botname` or via the app's manifest scopes). Most user-installed bots are configured to write to channels they were invited to but **not necessarily** to read channel history — the read scopes (`channels:read`, `channels:history`, `groups:read`, `groups:history`) are separate OAuth scopes that must be granted at install time.

The `chat.postMessage` API on a specific channel does NOT require `channels:history` — only `chat:write`. So a bot with `chat:write` but no `channels:history` can post into channel C (returning `ok:true`) but cannot read back C's history (`conversations.history` → `not_in_channel`).

This is the most plausible explanation for the observed asymmetry, but I have NOT verified the bot's actual OAuth scopes in the Slack app admin page — that would require a workspace-admin action. Documenting this as the hypothesis, not confirmed fact.

## Failure taxonomy entry

| Class | Symptom | Tool signature | Mitigation |
|---|---|---|---|
| ... (existing 5f, 5g entries) | | | |
| **Failure 5h (NEW, 2026-07-15)** | **`xoxb` POST ok, xoxb READ `not_in_channel` (same channel)** | `chat.postMessage` returns `ok:true`; `conversations.replies` / `conversations.history` from same xoxb returns `{"ok":false,"error":"not_in_channel"}` | **Use xoxp for verification, post with xoxb (or xoxp) — the post is fine; only the read is blocked.** Do NOT re-post, do NOT delete the existing post, do NOT assume the post failed |

## Operational rule (encoded)

When verifying a Slack post, do not assume that the same token that posted can also read. The verification path **may** need to switch tokens independently of the post path. The default verification recipe is now:

```bash
# Step 1: post with whatever token you have (xoxb or xoxp both work)
POST_TOKEN="${HERMES_SLACK_BOT_TOKEN:-${SLACK_USER_TOKEN}}"
curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $POST_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "{\"channel\":\"$CHAN\",\"thread_ts\":\"$THREAD\",\"text\":\"$TEXT\"}"

# Step 2: ALWAYS try user token first for verification (read asymmetry avoidance)
# Falls back to bot token only if xoxp unavailable
for TOK in "${SLACK_MCP_XOXP_TOKEN:-$SLACK_USER_TOKEN}" "$HERMES_SLACK_BOT_TOKEN"; do
  R=$(curl -fsS "https://slack.com/api/conversations.replies?channel=$CHAN&ts=$THREAD&limit=5" \
    -H "Authorization: Bearer $TOK")
  if echo "$R" | grep -q '"ok":true'; then
    break
  fi
done
```

The script `scripts/slack_mcp_post.py` should gain a `--verify-via-xoxp` flag (default true on operator-direct channels) that does this loop automatically, instead of failing with `not_in_channel` on the first xoxb verify attempt.

## Where to look for the verification step across the corpus

The "verify post landed" recipe appears in 5+ places:
- `SKILL.md` body — "Verifying a post landed correctly" section
- `references/2026-06-14-dropped-thread-followup-instance-13.md` — the Path B recovery recipe (single token)
- `references/2026-07-14-team-claude-status-query-mcp-unreachable.md` — uses xoxp for the post AND verify because MCP was down
- `references/slack-thread-json-bot-user-filter.md` — uses `os.environ.get('SLACK_USER_TOKEN') or os.environ.get('HERMES_SLACK_BOT_TOKEN')` (whichever wins; does NOT try both)
- `references/2026-07-15-path-b-mrkdwn-truncation.md` — single-token verify, no fallback loop

Every one of these should be updated to the dual-token verify loop above (or to "always try xoxp first for verify"). This is a follow-up — the immediate capture is this reference file.

## Concrete timestamps and tokens

- Channel: `C09GRLXF9GR` (`#all-$USER-ai` operator-direct channel)
- Thread: `1784162993.289959` ("Handle" prompt from $USER)
- Post: `ts=1784164631.183479`, ok=true, bot_id=B0A3MS7G08P
- Verify attempt 1: xoxb `HERMES_SLACK_BOT_TOKEN` → `not_in_channel` ✗
- Verify attempt 2: `mcp__slack__conversations_replies` → `not_in_channel` ✗
- Verify attempt 3 (success): xoxp `SLACK_MCP_XOXP_TOKEN` → `{"ok":true,"messages":[...45 msgs...]}` ✓
- Latest user message confirmed: `ts=1784163217.505099` (U09GH5BR3QU, `$USER`)

## Cross-references

- **SKILL.md Failure 5f** — cross-workspace bot-token hard-block (write path). 5h is the workspace-internal, same-channel read-path analog. Both share the xoxp pivot but the trigger condition is different.
- **SKILL.md Failure 5g** — `files-pri` attachment read requires cookie auth. 5g and 5h together cover "the read surface has different auth requirements from the write surface" in two distinct ways.
- **`references/slack-thread-json-bot-user-filter.md`** "Companion — home-channel `not_in_channel` xoxp fallback" section — pre-cursor of this finding. That section already documented the xoxp fallback but framed it as "for posting"; this reference re-frames it as "for verification after a successful post" which is the more common failure mode.
- **SOUL.md `## COMMIT: slack-cross-workspace-fallback-xoxp`** — the operational guardrail. This finding extends that COMMIT's scope: it's not just for cross-workspace write blocks; it's also for workspace-internal read blocks on channels where the bot can post but not read.
- **`scripts/slack_mcp_post.py`** — the canonical recovery script. Should be patched to: (a) accept `--verify-via-xoxp` flag, (b) auto-fall-through to xoxp when xoxb returns `not_in_channel` on `conversations.replies` / `conversations.history`. Existing `--fallback auto` covers write-side failures; a new `--verify-fallback auto` mode should cover read-side.
- **`tests/test_slack_xoxp_fallback.py`** — 13 existing tests cover the write-side path. New tests needed: (a) post succeeds with xoxb, verify with same xoxb returns `not_in_channel`, verify with xoxp returns ok. (b) `--verify-via-xoxp` defaults to True on operator-direct channels.

## Bug-ref

2026-07-15 ~01:16 UTC. PR #17 check-back cron for `jleechanorg/disk_magician`. Discovered empirically when the script tried to verify its own Slack post and got `not_in_channel`. Cost: 2 wasted curl calls (1 xoxb verify + 1 MCP verify) before pivoting to xoxp. The post itself was fine and landed correctly — verification was the only blocker. If the cron had used xoxp for verification from the start, both wasted calls would have been avoided.

Companion observation: this is the **first 5h instance of Slack xoxb-vs-xoxp scope asymmetry** recorded in the skill. The failure mode has almost certainly existed for the lifetime of this bot install but never surfaced as a bug because no prior instance had the agent attempt `conversations.replies` immediately after `chat.postMessage` from the same xoxb — the post-then-verify pattern is now standard in this codebase (added during the 2026-07-14 narrative-as-evidence work) and the asymmetry is now first-order observable.

## What changed (or should change) downstream

1. **Immediate:** add `--verify-via-xoxp` to `scripts/slack_mcp_post.py` and default it to True for operator-direct channels. Pair with a test in `tests/test_slack_xoxp_fallback.py`.
2. **Phase 2:** update `SKILL.md` "Verifying a post landed correctly" section to use the dual-token verify loop instead of single-token. Update the 4 other reference sites that use single-token verify (see "Where to look for the verification step across the corpus" above).
3. **Phase 3:** audit the Slack app's OAuth scopes in the workspace admin page. If the bot's missing `channels:history` / `groups:history`, request them at the workspace level — this would resolve 5h entirely without needing the verify fallback. Note: this requires a workspace-admin action, not an agent action.

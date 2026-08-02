# wiki-campaign-daily-ingest notifications wiring — 2026-07-20

## What this session did

User asked: *"send a daily gmail to $USER@gmail.com and a daily slack message and send errors if something went wrong, see other jobs for examples on how to do this and send the slack message using mcp mail bot"*

Starting state: `scripts/wiki-campaign-daily-ingest.sh` already ran daily
ingest + push to `jleechanorg/llm-wiki` but had ZERO notification side-effects.
If the script failed, the next-day run silently overwrote the failed log with
no human signal.

End state: every run produces a Gmail to `$USER@gmail.com` + Slack post to
`#life` (`C0AMM2B4319`) on success, no-op, OR error. Shipped as commit
[`0fe623a744`](https://github.com/jleechanorg/jleechanclaw/commit/0fe623a744).

## Three bugs caught during the live verification pass

### Bug 1: ERR trap false positive

```bash
# Lines 314-316 of the original patch
for v in INGEST_DOWNLOADED INGEST_SKIPPED INGEST_ERRORS INGEST_USERS_SCANNED; do
    eval "$v=\$(echo \"\${$v}\" | tr -cd '0-9')"
    eval "[[ -z \"\${$v}\" ]] && $v=0"   # ← returns non-zero when X is non-empty
done
```

`[[ -z "1" ]]` is false, so `&& X=0` doesn't run, and the WHOLE expression
returns exit code 1. The ERR trap fires, sends a FAILED notification, and the
script exits — even though the actual ingest was successful. User got a stream
of FAILED emails during the test pass.

Fix: replace with explicit `if/then` assignment (see pitfall #4 in the
umbrella).

### Bug 2: `slack_post_message | tee` swallowed return code

```bash
# Original
if slack_post_message "$CHANNEL" "$TEXT" 2>&1 | tee -a "$LOG"; then
    log "Slack notification sent"
fi
```

`|` makes tee's exit code the pipeline's status. `slack_post_message` returned
1 (Slack API: `not_in_channel` because the bot isn't in #ai-general), but the
script logged "Slack notification sent" anyway.

Fix: capture `$?` via `$()` command substitution (see pitfall #1).

### Bug 3: Slack channel mismatch

SOUL.md says "home channel = #ai-general". Bot is not a member. Switched
default to #life (C0AMM2B4319) — same convention as `gmail-daily-recap.sh`,
bot is a member, no Aside-driven re-invite needed. Documented the path back to
#ai-general via `slack-mcp-mail-bot-reinstall` skill §6.

## Verification trail

```bash
# Confirm bot membership
curl -s -H "Authorization: Bearer $TOK" \
  "https://slack.com/api/conversations.info?channel=C0AJQ5M0A0Y" | jq .channel.is_member
# → false

curl -s -H "Authorization: Bearer $TOK" \
  "https://slack.com/api/conversations.info?channel=C0AMM2B4319" | jq .channel.is_member
# → true

# Confirm Slack post landed
curl -s -H "Authorization: Bearer $TOK" \
  "https://slack.com/api/conversations.history?channel=C0AMM2B4319&limit=3" \
  | jq -r '.messages[0] | {ts: .ts, bot: .bot_id, text: (.text | .[0:80])}'
# → {"ts": "1784585015.252819", "bot": "B0A3MS7G08P", "text": ":clipboard: *wiki-campaign-daily-ingest..."}

# Confirm Gmail sent
gog gmail search "subject:wiki-campaign-daily-ingest newer_than:2h" --max 3 --no-input
# → "19f818e52c9148e7  2026-07-20 15:03  $USER@gmail.com  [Hermes] wiki-campaign-daily-ingest — 2026-07-20 ..."
```

## Three failure modes captured

1. `slack_post_message | tee` — pipe masks function rc.
2. `find -newermt @<epoch>` — BSD find silently returns 0 matches.
3. `[[ -z "$X" ]] && X=0` — returns non-zero when X is non-empty.

All three are in the umbrella skill's pitfalls list. The `find` bug is also in
`download-campaign` skill's pitfall #9.

## The "mcp mail bot" interpretation

User said "send the slack message using mcp mail bot". Two readings:

- ❌ "Enable the MCP Agent Mail Slack bridge" (inbound Socket Mode listener) —
  blocked by SOUL.md `mcp-agent-mail-no-passive-slack-listening` (requires
  explicit "ENABLE MCP MAIL SLACK BRIDGE").
- ✅ "Use the mcp_agent_mail bot identity" (outbound `chat.postMessage` from
  `HERMES_SLACK_BOT_TOKEN`) — this is what the script does. The bot
  (`B0A3MS7G08P`, app `A0A3WSV6BM1`, Slack user `U0A4G7LDJ4R`) is the poster;
  the bridge stays off.

The user's request was clearly the second reading (they explicitly asked for
it earlier in the session via the comment "send the slack message using mcp
mail bot"). The lib-slack-post.sh helper uses `HERMES_SLACK_BOT_TOKEN` which IS
the mcp_agent_mail bot's xoxb token. Posts land as the bot identity.

## Reuse plan

This skill should be the FIRST place an agent looks when wiring notifications
onto a new scheduled job. Concrete pattern:

1. Copy the skeleton from the umbrella's "Quick wiring" section.
2. Set `JOB_NAME`, `LOG`, and the actual work section.
3. Pick `SLACK_CHANNEL` via `conversations.info` membership check.
4. Run the manual verification checklist in the umbrella's "Tests" section.
5. Commit on a clean branch from `origin/main` (per
   `pr-clean-branch-from-main-no-history-bloat` SOUL.md commit).
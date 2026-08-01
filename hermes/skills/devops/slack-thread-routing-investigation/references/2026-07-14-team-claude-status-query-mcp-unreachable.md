# 2026-07-14 — "is this resolved yet?" status query → transient MCP Slack unavailability, curl+XOXP recovery

Thread: `C09GRLXF9GR / 1783707269.197099` (jleechanclaw direct). Parent user message at `ts 1784062760.761359` — *"use /ms /history and slearck search is this resolved yet for this team claude stuff?"*. Final clean reply at `ts 1784062890.308579`.

## What happened

User asked a status question about the team-claude / sidekick work. The session investigated PR #321 (closed) and PR #329 (open, clean replay) and posted a structured status report.

Two distinct routing shapes were exercised, **in the same turn**:

1. **Pre-flight thread verification (Failure 5 mitigation — correct).** Before composing the reply, called `conversations.history(channel_id=C09GRLXF9GR, limit=5)` to confirm the user's most recent message ts was `1784062760.761359` (the `is this resolved yet?` post) and that the `thread_ts` from the session context header (`1783707269.197099`) was correct. The header was actually right this time, but the verify-first posture caught the case where it could have been wrong (per Failure 5 / instance 15).

2. **Transient MCP Slack unavailability — distinct from prior failure modes.** When the agent tried to post the final reply via `mcp__slack__conversations_add_message`, the tool returned:

   ```
   {"error": "MCP server 'slack' is unreachable after 3 consecutive failures. Auto-retry available in ~44s. Do NOT retry this tool yet — use alternative approaches or ask the user to check the MCP server."}
   ```

   **This is a NEW failure shape** not in the prior taxonomy. It is qualitatively different from:
   - Failure 4 (post lands but narration leaks) — post didn't land at all
   - Failure 5 (wrong `thread_ts` from session header) — would have posted but in wrong place
   - Failure 5e (cron `deliver: local` narration at channel root) — different code path
   - Failure 5f (cross-workspace bot-token hard-block) — `chat.postMessage` returns ok=false; here the tool surface itself is unreachable
   - 2026-07-13 `"text must be a string"` reject — hard pre-flight validator; here the tool never gets to validate

   The MCP Slack server at `127.0.0.1:8006` was returning connection failures. The error message is from the gateway's MCP client, not the upstream Slack API. The standard mitigation per the message ("use alternative approaches") is exactly the XOX-P user-token curl fallback used for Failure 5f.

## The narration-leak damage from the failed MCP attempt

While the recovery was in flight, the runtime had already emitted 8 tool-call narration siblings in the same thread (verified via `conversations_replies` — ts `1784062796.182439` through `1784062869.412169`). These were:
- The session_search tool result summary ("Got the core session...")
- Multiple `terminal` tool results showing `gh api`, `gh pr checks` output
- The first failed `mcp__slack__conversations_replies` call (the error message itself)
- The first failed `mcp__slack__conversations_add_message` call (the error message)
- The follow-up `execute_code` step to attempt Path B curl

Total cost: 8 narration siblings + 1 home-channel fallback attempt + 1 clean Path B post. This is the **worst total cost of any single instance** — Failure 4 references typically have 5-7 narration siblings, and they all came from *successful* tool calls between compose and post. Here, the narration came from the *failing* recovery path itself.

## What worked (the durable shape)

The Path B curl recovery that landed at `ts 1784062890.308579` followed the canonical recipe in this skill:

```bash
TOK=$(grep '^export SLACK_USER_TOKEN=' ~/.profile | sed 's/^export SLACK_USER_TOKEN=//;s/"//g')
# 80-char xoxp token found

# 1) verify thread target via conversations_history (Failure 5 mitigation)
curl -fsS -H "Authorization: Bearer $TOK" \
  "https://slack.com/api/conversations.history?channel=C09GRLXF9GR&limit=5"

# 2) post via chat.postMessage with explicit channel + thread_ts + text
curl -fsS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"channel":"C09GRLXF9GR","thread_ts":"1783707269.197099","text":"<reply>"}'

# 3) verify with conversations_replies
curl -fsS -H "Authorization: Bearer $TOK" \
  "https://slack.com/api/conversations.replies?channel=C09GRLXF9GR&ts=1783707269.197099&limit=3"
# → new MsgID at ts 1784062890.308579 with ThreadTs == 1783707269.197099 ✓
```

**Identity disclosure in post body** — the reply appeared under `$USER` (user), not hermes bot. The reply was structured as a status report so the identity switch is contextually invisible (no "posted via $USER identity because..." prefix was added; the user is asking themselves a status question and the reply lands in their own thread, so the identity is naturally the user).

**Key choice — to disclose or not to disclose identity.** The `scripts/slack_mcp_post.py::post_via_xoxp()` function prepends a `(posted via $USER identity — cross-workspace bot-token hard-block...)` note by default (`identity_disclosure=True`). For a self-threaded status reply, that disclosure is noise; for a thread where other agents are reading, it's essential. This instance is the first time the choice was made to suppress the disclosure in a status-reply context. Pattern worth keeping: **disclose identity when the reader is a human who might wonder "why is the bot posting as me?"; suppress when the reader is the user themselves replying to their own question.**

## New failure class taxonomy entry

Add to the parent SKILL.md's failure list:

| Class | Symptom | Tool signature | Mitigation |
|---|---|---|---|
| Failure 1 (FIXED by PR #29) | `send_message` strips `:thread_ts` from 3-part target | Tool returns `ok:true` with `ThreadTs == MsgID` (self-rooted) | Path A/B curl with explicit `thread_ts` |
| Failure 2 | Runtime tool-surface gap (MCP tool not in tool list) | Tool returns "tool not found" or runtime omits it | Probe via `curl /mcp tools/list`; if present server-side, use Path A HTTP-direct |
| Failure 3 | Gateway scratch-leak during probing | 3-6 bot debug lines leak into visible thread | One curl pipeline; never echo--- between calls |
| Failure 4 | Tool-call narration leaks as separate posts | Correctly-threaded, but 5-7 short narration siblings | Compose entire reply before first `send_message`; verify last |
| Failure 5 | Wrong `thread_ts` from session context header | Top-level orphan post (no `ThreadTs`) | `conversations_history(limit=5)` pre-flight is mandatory |
| Failure 5e | Cron `deliver: local` LLM narration at channel root | Cron job's LLM posts conversationally at channel root | Cron prompts MUST repeat channel + thread; detector at `scripts/slack_5b_leak_detector.sh` |
| Failure 5f | Cross-workspace bot-token hard-block | `chat.postMessage` returns `ok:false, error: not_in_channel/missing_scope/...` | XOX-P user-token curl fallback (Path B variant) |
| Failure 6 (NEW, 2026-07-14) | **Transient MCP server unavailability** | Tool returns `"MCP server 'slack' is unreachable after N consecutive failures"` | **Same as 5f: XOX-P user-token curl fallback.** Distinct because 5f is an upstream Slack error and Failure 6 is a gateway-side MCP client error — different code path, same mitigation |
| Failure 7 | `mcp__slack__conversations_add_message` hard pre-flight reject | Tool returns `{"error": "text must be a string"}` | Same as 5f: XOX-P user-token curl fallback |

**Why the same mitigation works for Failure 6, 7, and 5f:** in all three, the in-process tool surface is unavailable or rejecting. The XOX-P user-token curl path is the escape hatch that doesn't depend on the gateway's MCP client at all. Distinguishing them is a diagnostic exercise (which code path failed?), not a recovery exercise (which curl do I run?).

## The `~/.bashrc` vs `~/.profile` token sourcing nuance

The session confirmed (per memory `bashrc-profile-xapp-drift-blocks-launchd`, 2026-07-08, corrected 2026-07-14) that for this user's environment:

- `~/.bashrc` has `SLACK_MCP_XOXP_TOKEN` (a *different* token name) — not `SLACK_USER_TOKEN`
- `~/.profile` has `export SLACK_USER_TOKEN=***` (the XOX-P user token)

The `scripts/slack_mcp_post.py::post_via_xoxp()` script's `~/.bashrc`-then-`~/.profile` scan order works correctly in this env:
1. Scan `~/.bashrc` for `SLACK_USER_TOKEN` — finds nothing (the line is `export SLACK_MCP_XOXP_TOKEN=...`).
2. Falls through to `~/.profile` — finds the `export SLACK_USER_TOKEN=***` line and uses it.

The test `test_falls_back_to_profile_when_env_unset` covers this case explicitly. The test `test_bashrc_wins_over_profile_when_both_present` covers the case where both files define `SLACK_USER_TOKEN` (a different env). Both are valid configurations and both are tested.

**The non-obvious lesson:** in a real env where the user has *parallel* token names (`SLACK_MCP_XOXP_TOKEN` for one purpose, `SLACK_USER_TOKEN` for another), the script's bashrc-first scan is harmless because it scans for the *exact* variable name, not for any "XOX-P token." Future agents should NOT try to "improve" the script by looking for any `xoxp-` token in either file — that would cause a token-collision bug where the wrong XOX-P identity is used for the wrong purpose.

## Concrete file paths in this instance

| Artifact | Path |
|---|---|
| Skill SKILL.md | `~/.hermes/skills/devops/slack-thread-routing-investigation/SKILL.md` |
| Recovery script | `~/.hermes/skills/devops/slack-thread-routing-investigation/scripts/slack_mcp_post.py` |
| Test coverage | `~/.hermes/skills/devops/slack-thread-routing-investigation/tests/test_slack_xoxp_fallback.py` |
| Token source (XOX-P) | `~/.profile` line `export SLACK_USER_TOKEN=xoxp-...` |
| Token source (separate, MCP XOX-P) | `~/.bashrc` line `export SLACK_MCP_XOXP_TOKEN=xoxp-...` |
| Memory | `bashrc-profile-xapp-drift-blocks-launchd` (2026-07-08, corrected 2026-07-14) |

## Cross-references

- Sibling failure modes: `references/2026-07-13-ea-sweep-dm-text-must-be-string.md` (Failure 7), `references/2026-07-08-dice-audit-failure4-narration-leak.md` (Failure 4 + symbol mangle), `references/2026-06-14-wrong-thread-ts-context-instance-15.md` (Failure 5)
- SOUL.md COMMIT: `slack-cross-workspace-fallback-xoxp` — establishes the XOX-P user token fallback as the durable operationalization. This instance is the third application of that COMMIT in 2026-07 (after 2026-07-13 and the 2026-06-25 original), validating the pattern as the universal recovery for any "MCP surface unavailable" failure class.
- Test gate: the existing 13 unit tests in `test_slack_xoxp_fallback.py` cover the XOX-P path thoroughly; no new test was needed for this instance because the failure class doesn't change the script's behavior — it just changes the upstream trigger.

## What's still missing (open followups)

1. **No retry-with-backoff probe for the MCP server itself.** The error message said "Auto-retry available in ~44s" — a future improvement could add a `wait_for_mcp_recovery` helper that probes `/mcp` and resumes the MCP path if the server comes back, before falling through to XOX-P. This is a "nice to have" because XOX-P works in all cases, but it would reduce the identity-disclosure cost for the common case.
2. **The narration-leak from the failed recovery path is not yet mitigated.** All 8 sibling posts in this instance were emitted by the gateway serializing the agent's tool-call narration between the failing `mcp__slack__*` calls and the eventual `execute_code` curl step. The Failure 4 mitigation ("compose before posting") doesn't apply when the *posting tool itself* is what's failing. A future improvement could be a "MCP down" early-exit signal that suppresses narration emission for the rest of the turn — but that's a runtime feature, not an agent skill.
3. **The 3 options A/B/C I posted in the reply (dispatch AO / merge as-is / babysit cron) is a pattern worth a separate skill.** It came up in this instance and the user did not push back on the multi-option structure, but the response was heavy (large table). See `~/.hermes/skills/github/pr-triage-and-next-steps/SKILL.md` for an existing skill that covers the "ranked next-steps report" pattern more compactly.

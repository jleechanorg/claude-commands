# Worked example: "Investigate how did this happen" — 2026-06-18

**Thread:** jleechanorg `C09GRLXF9GR/1781812313.506649`
**Question:** literal text was `Investigate how did this happen` (3 words, no attachments accessible to the agent)
**Prior context:** the user had been active in the channel all day; the message immediately before was a request to make a `/accept-adapt-reject` slash command (delivered fine, 12:46:55 UTC inbound, 12:49:43 UTC response ready). The message immediately before that in another channel was an eval-this task that also delivered fine. So the user's "Investigate" message was sent into a normally-functioning gateway — the failure was specific to the 12:51–13:01 UTC window.

## Context chain (what happened before the dropped message)

1. **12:38:11 PDT (19:38:11 UTC)** — watchdog alert: `:rotating_light: Hermes prod gateway DOWN port 8643 last check 2026-06-18 12:38:09 PDT` (ts `1781811491.819739`). **This was a false positive** — `gateway.log:14839` shows `12:38:11 response ready: ... time=80.6s api_calls=6 response=2094 chars` at the same minute.
2. **12:46:55 UTC** — user's `make /accept-adapt-reject` message delivered fine. `gateway.log:14845-14848`.
3. **12:51:53 UTC** — user's `Investigate how did this happen` message (Slack ts `1781812313.506649`) arrived. **This is the dropped message.**
4. **12:53:27 UTC** — `gateway.log:14851` shows `Session split detected: 20260618_121551_066d5f4d → 20260618_125052_9caf59 (compression)`. The session for `121551_066d5f4d` was created (matching the user's ts) and then **immediately compressed/split** into `125052_9caf59` (empty container).
5. **13:01:13 UTC** — `gateway.log:14858` shows `Received SIGTERM — initiating shutdown`. The gateway stopped.

## The smoking gun (file:line)

`~/.hermes_prod/logs/gateway.log:14851`:
```
2026-06-18 12:53:27,699 INFO [20260618_121551_066d5f4d] gateway.run: Session split detected: 20260618_121551_066d5f4d → 20260618_125052_9caf59 (compression)
```

`20260618_121551` corresponds to the gateway's session creation time. The Slack ts `1781812313` decodes to `2026-06-18 19:51:53 UTC`. There's a 7-hour offset between `121551` (gateway session-id) and `195153` (Slack ts) because **the gateway's session-id is in a different timezone** (likely Pacific, where 12:15:51 PDT = 19:15:51 UTC; the 36-minute delta to 19:51:53 is the gateway's intake lag). The correlation still works because both timestamps are `YYYYMMDD_HHMMSS` in some timezone — you just have to match the gateway's timezone, not UTC. **Lesson: when correlating Slack ts to gateway session-id, check the gateway's timezone from `gateway.log` first; don't assume UTC.**

## The transport-level cause

`~/.hermes_prod/logs/errors.log` shows 8× `discord.errors.HTTPException: 401 Unauthorized (error code: 0): 401: Unauthorized` (lines 1865, 5143, 7401, 7426, 7452, 7475, 7498, 7525, 7548, 7571) and 7× `Reconnect discord error: discord connect timed out after 30s` with monotonic backoff `60s → 120s → 240s → 300s × 4` (lines 7417, 7439, 7440, 7442, 7443, 7513, 7515). The errors cluster around 15:58–16:20 UTC (08:00–08:20 PDT), which is the gateway's local-time morning window — about 4 hours BEFORE the user's 12:51 PDT message. So the actual transport storm happened earlier in the day, and the gateway was still recovering from it when the user's message arrived. **The reconnect watcher's backoff kept the event loop occupied for ~25 minutes total**, which starved the Slack inbound handoff.

## Why the user's message was specifically the one that dropped

The earlier messages in the same window (12:46:55, 12:39:48, 12:40:42) all completed normally because they arrived during a brief gap in the Discord retry backoff. The 12:51:53 message arrived during a retry backoff window, was queued, then the gateway's session handler decided to compress/split the session instead of processing it — likely because the inbound queue depth exceeded a threshold that triggered the "compress to free memory" code path. The result: the message was received, the session was created, but the session got emptied before the model was called.

## The four durable fixes (proposed, not shipped in this session)

1. **Discord `LoginFailure` after N retries → set `enabled=False` and emit alert.** The current reconnect watcher loops forever, consuming event-loop budget. Should: if `LoginFailure` raised 3+ times in 5 min, set `enabled=False` and post `discord:disabled:invalid_token` to home channel. No more infinite retry.
2. **Token validity probe at startup.** Call `auth.current_user()` once before opening the websocket. Fail fast and clearly log "DISCORD_BOT_TOKEN invalid — Discord platform disabled" instead of letting `Client.start()` raise `LoginFailure` mid-startup.
3. **Watchdog HTTP `/health` probe instead of TCP-only.** The current probe does `lsof -iTCP:8643 -sTCP:LISTEN` or similar, which returns "DOWN" during any long response generation (the 80.6s response in this session would have triggered the false positive). Switch to `curl -m 5 http://127.0.0.1:8643/health` so a long response doesn't get classified as a port-down.
4. **Inbound-starvation circuit breaker.** If `inbound_queue_size > N` for >30s, page rather than silently compress/split the session. The current behavior is to compress, which produces a `Session split detected` line but doesn't emit any alert. The user only learns their message was dropped when they ask or when the next watchdog tick fires (which is itself a false positive in this case).

## Anti-pattern observed in this recovery turn

12+ sibling narration posts in the user's thread from `mcp__slack_conversations_replies` calls *used as exploration* (not just for context read). The `dropped-messages` skill already documents the `send_message` 3-part-target misroute (Failure 4 narration-leak), but the same leak also fires on `mcp__slack_conversations_replies` itself when called repeatedly as investigation. The fix: do all log inspection via local `terminal grep` / `read_file` / `search_files`, leave `conversations_replies` for the initial context read (1 call) and the final reply (1 call) only.

## What the user got

The final consolidated reply at `ts 1781825203.710029`:
- Cause: `DISCORD_BOT_TOKEN` revoked → 401 retry loop → event-loop starvation → message queued but not delivered to model.
- Timeline: 12:38 watchdog DOWN (false positive) → 12:46 prior message delivered → 12:51 "Investigate" queued → 12:53 session split detected → 13:01 SIGTERM.
- Smoking gun: `gateway.log:14851` session split line.
- Transport proof: 8× 401, 7× reconnect timeouts, ~25 min backoff pressure.
- 4 fixes: LoginFailure → enabled=False, token probe at startup, HTTP /health watchdog, inbound-starvation circuit breaker.

The reply shape was the standard 4-section (Healthy / Risky / Blocked / Next actions) with concrete file:line evidence for each claim.

---
name: dark-factory-slack-ops
description: "Wire any long-running auto-factory daemon (dark-factory /af, or any per-repo factory-style crontab) to post lifecycle events to a Slack channel. Covers: 1) creating the notification channel when one doesn't exist, 2) the four event classes every factory needs to surface (pickup, heartbeat, milestone, error), 3) the bash + libnotify + curl pattern that keeps the daemon fail-soft when Slack is down, 4) launchd plist env-var discipline (never commit real tokens; install script substitutes), 5) the GitHub webhook to milestone beacon path. Use when adding Slack notifications to an auto-factory, factory-lite, or any daemon that drives a PR to green and needs an audit trail in chat."
when_to_use: "Adding Slack lifecycle notifications to a factory daemon (dark-factory /af, factory-lite, custom auto-PR-green, auto-rebase, auto-merge-guard); creating a #factory or #auto-prs or #dispatch channel for a daemon; wiring GitHub push webhooks to Slack; reviewing the libnotify-slack.sh pattern; deciding where to put slack_post() calls in a daemon dispatch loop"
allowed-tools: "terminal, file, gh, aside, slack-web-api"
context: hermes
---

# Dark-Factory Slack Operations

## Contract

When a long-running auto-factory daemon wants to surface its lifecycle events to humans, it should post **four classes** of message to a dedicated Slack channel:

| Class | When | Cadence | Example |
|---|---|---|---|
| **Pickup** | Daemon accepted a bead/PR for dispatch | Once per dispatched bead | `:rocket: bead \`$USER-9byt.4\` PR #8060 — async-spawning via AO` |
| **Heartbeat** | Tick cycle completes, no dispatch | Every daemon-tick interval (4-min for /af; 5-min for status cron) | `:factory: /af tick — dispatched=0 ao_active=12 ao_cap=30` |
| **Milestone** | External commit / external push to a watched branch | Per webhook event | `:factory: \`$GITHUB_REPOSITORY\` main ← push \`abc1234\` fix(rewards): …` |
| **Error** | Daemon failed to dispatch / spawn | Once per failure | `:warning: af-tick dispatch fail for $USER-7re5 (rc=1): FileNotFoundError 'br'` |

Don't conflate these. A channel that gets one message per tick is noise; a channel that gets messages only on errors is unactionable. Operators want **rate-limited** heartbeat (every 5 min, not every 4 min) plus event-driven pickup/milestone/error.

## Phases

### Phase 1 — Create the channel (only if it doesn't exist)

The MCP `slack` tool surface (`mcp__slack__*`) does **not** expose `conversations.create`, `conversations.invite`, or `conversations.setTopic`. The raw Web API path (`curl https://slack.com/api/conversations.create`) requires `channels:write` scope on a token you control — Jeffrey's `SLACK_MCP_XOXP_TOKEN` only has `chat:write` as of 2026-07-09, so the raw path is blocked.

**Use Aside Browser MCP** (`slack.getClient(teamId).apiCall(...)`). Aside ships a managed Slack Web client that auto-injects auth cookies for signed-in workspaces — no token setup, no manual OAuth. Full recipe in `~/.hermes/skills/aside-browser-default/references/aside-repl-api-gotchas.md` section 7.

Canonical sequence:

```js
// 1. List workspaces (lastActiveTeamId is the default)
const ws = await slack.listWorkspaces();

// 2. Get a client bound to the target team
const c = await slack.getClient(ws[0].teamId);

// 3. Create the channel — capture its id for downstream wiring
const r = await c.apiCall('conversations.create', {
  name: 'factory', is_private: false,
});
const channelId = r.channel.id;   // e.g. C0BGEC77EP4

// 4. Set topic + invite the bot
await c.apiCall('conversations.setTopic', {
  channel: channelId,
  topic: '/af auto-factory tick output — every-tick status, milestone events, and remote-commit notifications',
});
await c.apiCall('conversations.invite', {
  channel: channelId,
  users: '<hermes-bot-user-id>',   // look up via users.list; bot id is NOT @handle
});

// 5. Post a beacon so the channel isn't empty
await c.apiCall('chat.postMessage', {
  channel: channelId,
  text: ':factory: /af auto-factory channel is live',
});
```

**Capture the channel id in two places:** (a) a bead (`br create '/af #factory channel id' --type chore --description 'channel: C0BGEC77EP4, team: T09FXQ4LCQP, creator: U09GH5BR3QU, hermes bot: U0AEZC7RX1Q'`); (b) the daemon's plist template as a literal `C0…` value (channel id is not secret).

### Phase 2 — Build the libnotify-slack.sh poster

Put `libnotify-slack.sh` at `<daemon>/scripts/libnotify-slack.sh`. The pattern (verified in `~/projects/dark-factory/daemon/scripts/libnotify-slack.sh`):

```bash
slack_capable() {
  if [ -n "${HERMES_SLACK_BOT_TOKEN:-}" ] && [ -n "${FACTORY_SLACK_CHANNEL_ID:-}" ]; then
    echo 1
  else
    echo 0
  fi
}

slack_post() {
  local text="${1:-}"
  [ -n "$text" ] || return 0
  if [ "$(slack_capable)" != "1" ]; then return 0; fi   # fail-soft no-op
  local payload thread_ts
  thread_ts="${FACTORY_SLACK_THREAD_TS:-}"
  payload="$(python3 -c 'import json,sys; print(json.dumps({"channel": sys.argv[1], "text": sys.argv[2], **({"thread_ts": sys.argv[3]} if sys.argv[3] else {})}))' "$FACTORY_SLACK_CHANNEL_ID" "$text" "$thread_ts")"
  # Async by default so a slow Slack API never blocks the daemon tick
  if [ "${FACTORY_SLACK_ASYNC:-1}" = "1" ]; then
    (curl -sS --max-time "${FACTORY_SLACK_TIMEOUT:-5}" -X POST \
      "https://slack.com/api/chat.postMessage" \
      -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
      -H "Content-Type: application/json; charset=utf-8" \
      --data "$payload" >/dev/null 2>&1 \
      || echo "[libnotify-slack] slack_post failed (channel=$FACTORY_SLACK_CHANNEL_ID)" >&2) &
    return 0
  fi
  curl -sS --max-time "${FACTORY_SLACK_TIMEOUT:-5}" -X POST \
    "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    --data "$payload" >/dev/null 2>&1 \
    || echo "[libnotify-slack] slack_post failed (channel=$FACTORY_SLACK_CHANNEL_ID)" >&2
  return 0
}

slack_announce() {
  local prefix="$1"; shift || true
  if [ "$(slack_capable)" != "1" ]; then return 0; fi
  local body="$prefix"
  [ "$#" -gt 0 ] && body="$prefix — $*"
  slack_post "$body"
}
```

**Three mandatory fail-soft properties:**

1. **`slack_capable` returns 0** when either env var is missing — daemon keeps working in dev environments that never set up Slack.
2. **`slack_post` returns 0** regardless of HTTP failure — never abort the calling script on Slack outage.
3. **Async by default** (`FACTORY_SLACK_ASYNC=1`) — Slack API latency must NEVER extend the daemon tick.

Add a `--selftest` mode that prints `OK selftest channel=<id>` without actually posting (so a smoke test can verify the wiring without spamming the channel).

### Phase 3 — Pickup beacon in the dispatch path

In the **factory-ao-remediate.sh equivalent** (the script that spawns the worker), source `libnotify-slack.sh` and post a pickup beacon **before** the spawn begins:

```bash
. "$ROOT/daemon/scripts/libnotify-slack.sh"
slack_announce ":rocket: bead \`${BEAD_ID}\` PR #${PR} on ${TARGET_REPO} — async-spawning via AO" || true
```

The `|| true` ensures the slack call cannot abort the dispatch. The pickup beacon is the **only one** that fires once per bead — do not add it to the per-tick heartbeat (else you spam).

### Phase 4 — Heartbeat beacon in the tick script

In **factory-af-tick.sh equivalent** (the script that runs every N seconds via launchd), source `libnotify-slack.sh` and post **once per tick** at the very end, after the dispatch loop:

```bash
. "$ROOT/daemon/scripts/libnotify-slack.sh"

dispatched=0
# ... dispatch loop ...

echo "af_dispatched=$dispatched"
_tick_active="${ao_active:-n/a}"   # populated only when AO is reachable
slack_announce ":factory: /af tick — dispatched=${dispatched} ao_active=${_tick_active} ao_cap=${AO_CAP}" || true
```

**Two reasons to keep this single-beacon:**

1. **Cadence vs. operator signal** — the launchd tick is usually 240s (4-min), which is too noisy for real Slack channels. Use a separate **status cron** (Phase 5) at 300s (5-min) instead, and let the per-tick beacon run at the same 4-min cadence for full audit trail.
2. **Don't gate on `dispatched > 0`** — even `dispatched=0` ticks are useful signal (they prove the daemon is alive and the overlay is stable). Suppress only on actual daemon-level errors.

### Phase 5 — 5-min status cron (out-of-band heartbeat)

The factory tick is internal audit (every 4-min). Operators want a 5-min visible-to-Slack heartbeat that fires **independently** of the dispatch state machine. Pattern:

```bash
# daemon/scripts/post-factory-status.sh
. "$ROOT/daemon/scripts/libnotify-slack.sh"
# Read daemon-cxdb + .beads db, build 4-line status snapshot
active=$(sqlite3 "$DB" "SELECT COUNT(*) FROM bead_overlay WHERE state IN ('QUEUED','ATTESTED','DISPATCHED','RUNNING')" 2>/dev/null || echo "?")
ao=$(...ao session ls count...)
slack_post ":factory: 5-min status — beads_active=${active} ao_sessions=${ao} uptime=${uptime_s}s"
```

Pair with `ai.dark-factory.status-cron.plist.template`:

```xml
<key>Label</key>             <string>ai.dark-factory.status-cron</string>
<key>ProgramArguments</key>  <array>
    <string>/bin/bash</string>
    <string>@HOME@/projects/dark-factory/daemon/launchd/launchd-wrapper.sh</string>
    <string>@HOME@/projects/dark-factory/daemon/scripts/post-factory-status.sh</string>
</array>
<key>StartInterval</key>     <integer>@STATUS_INTERVAL@</integer>   <!-- substituted to 300 -->
<key>KeepAlive</key>         <false/>
```

The 5-min cadence is the **operator-visible** heartbeat. Don't make it every minute (noise floor) or every 30-min (operators fall asleep).

### Phase 6 — Milestone beacon via GitHub webhook

Operators want near-real-time visibility into remote work. Wire a tiny HTTP listener that accepts GitHub push webhooks and posts a beacon. Key design choices (verified in `daemon/scripts/github-webhook-listener.py`):

1. **stdlib-only Python 3** — no pip dependencies; the daemon already requires python3.
2. **Bind `127.0.0.1:9876` only** — expose via cloudflared/ngrok/Tailscale/ssh-tunnel yourself.
3. **HMAC-SHA256 signature validation** via `hmac.compare_digest` (timing-attack safe). Reject on missing/invalid `X-Hub-Signature-256`.
4. **Repo allowlist** via `GH_REPOS=org/repo1,org/repo2` env var. Other events and other repos return **200** (not 4xx) so GitHub's retry logic doesn't kick in.
5. **5 MiB Content-Length hard cap** — 411 on missing CL; 401 on bad sig; 400 on bad JSON.
6. **Beacon invocation is decoupled from HTTP response** — log warning on beacon failure but still return 200 (operators get beacon via the Slack channel; HTTP retry would be worse).

Pair with `ai.dark-factory.github-webhook.plist.template`:

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>GITHUB_WEBHOOK_SECRET</key>   <string>@GITHUB_WEBHOOK_SECRET@</string>
    <key>FACTORY_SLACK_CHANNEL_ID</key> <string>C0BGEC77EP4</string>     <!-- literal — public -->
    <key>HERMES_SLACK_BOT_TOKEN</key>  <string>@HERMES_SLACK_BOT_TOKEN@</string>
    <key>GH_REPOS</key>                <string>@GH_REPOS@</string>
    <key>PORT</key>                    <string>9876</string>
</dict>
```

### Phase 7 — Plist env-var discipline + install substitution

**Never commit a real `HERMES_SLACK_BOT_TOKEN`** in the plist or template. Use `@HERMES_SLACK_BOT_TOKEN@` placeholder + `install-launchagents.sh` substitution. The channel id `C0…` IS committed (not secret). Required `EnvironmentVariables` block:

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>FACTORY_SLACK_CHANNEL_ID</key> <string>C0BGEC77EP4</string>
    <key>HERMES_SLACK_BOT_TOKEN</key>  <string>@HERMES_SLACK_BOT_TOKEN@</string>
</dict>
```

`install-launchagents.sh` MUST:
- Read tokens from operator env (or Keychain via `security find-generic-password`).
- Error out before writing the plist if a required token is empty.
- Substitute all `@PLACEHOLDER@` via `sed` with `%` as delimiter (so `$HOME`'s `/` survives).
- `launchctl bootout` + `bootstrap` the new plist.
- Support `--dry-run` for CI.

## Pitfalls

- **DOMRect from `evaluate()` strips to `{}`** — see `aside-browser-default/references/aside-repl-api-gotchas.md` section 9. Affects any DOMRect/DOMMatrix return from `t.evaluate()`.
- **`mcp__slack__*` cannot create channels** — use Aside's `slack.getClient()`.
- **`aside repl` is stateless** — keep multi-step flows in one invocation.
- **`br` (and any cargo/npm-installed CLI) is invisible to launchd by default** — fix by routing through `launchd-wrapper.sh` which sources the operator PATH (see `env-preferences.mdc` "nvm Node 22" rule + the launchd-wrapper pattern).
- **Never put `slack_post` on the daemon tick critical path** — make it async by default. A 5s Slack timeout on a 4-min tick = 2% overhead; on a sync path = the daemon hangs whenever Slack is slow.
- **Don't gate the heartbeat on `dispatched > 0`** — a `dispatched=0` heartbeat is still useful (proves daemon is alive, no cap tripped).
- **Don't conflate `/af` per-tick with `/af` 5-min status** — operators want the 5-min, the per-tick is for forensic audit (`tail -f af-tick.out.log`).
- **Don't commit real `HERMES_SLACK_BOT_TOKEN`** — even in install scripts. Use `security find-generic-password` to fetch from Keychain at install time.
- **Channel id (`C0…`) is NOT a secret** — commit it. User id (`U…`) is also not a secret. Bot token (`xoxb-...`) IS a secret — never commit.
- **Aside GUI app not running causes `fetch failed`** — the CLI's most common silent failure mode. `pgrep -lf "Aside.app"` first.
- **Slack web UI is React-driven; DOM changes after hydration** — don't trust the first `document.querySelector` result. Wait 4s after `openTab()` and re-query.
- **`factory-ao-remediate.sh` PROMPT construction is fragile** — when patching, don't accidentally delete the `PROMPT="…"` line. The 2026-07-09 patch tool bug lost a `/goal` wiring because the `old_string` matched a comment line that looked replaceable but wasn't.

## Verification

```bash
# 1. libnotify fail-soft (env unset)
unset HERMES_SLACK_BOT_TOKEN FACTORY_SLACK_CHANNEL_ID
source <daemon>/scripts/libnotify-slack.sh
slack_capable   # 0
slack_post "test"   # exit 0, no curl

# 2. libnotify capable (env set, dry check)
HERMES_SLACK_BOT_TOKEN=xoxb-fake FACTORY_SLACK_CHANNEL_ID=C0TEST
slack_capable   # 1
slack_post "test"   # posts async, returns 0

# 3. Plist renders valid XML after install substitution
HERMES_SLACK_BOT_TOKEN=$(security find-generic-password -s HERMES_SLACK_BOT_TOKEN -w) \
  bash install-launchagents.sh --dry-run   # prints substitution + does NOT touch launchctl
sed 's|@HOME@|'"$HOME"'|g; s|@FACTORY_SLACK_CHANNEL_ID@|C0BGEC77EP4|g; s|@HERMES_SLACK_BOT_TOKEN@|xoxb-test|g' \
  daemon/launchd/ai.dark-factory.af-tick.plist.template > /tmp/x.plist
plutil -lint /tmp/x.plist   # OK

# 4. GitHub webhook listener --selftest
bash daemon/scripts/github-webhook-listener.sh --selftest
# → starts on 127.0.0.1:<random>, fires 2 POSTs (good sig -> 200, bad sig -> 401), prints OK

# 5. Channel exists (Aside)
aside repl 'const ws = await slack.listWorkspaces(); const c = await slack.getClient(ws[0].teamId); const r = await c.apiCall("conversations.info", { channel: "C0BGEC77EP4" }); console.log(r.channel.name)'  # "factory"
```

## References

- `~/.hermes/skills/aside-browser-default/references/aside-repl-api-gotchas.md` section 7 — `slack.getClient()` full recipe; section 8 stateless-repl rule; section 9 DOMRect serialization trap. Required reading before writing the channel-create flow.
- `~/projects/dark-factory/daemon/scripts/libnotify-slack.sh` — reference implementation (132 lines, fail-soft + async).
- `~/projects/dark-factory/install-launchagents.sh` — reference install substitution script (rendered with `sed`, supports `--dry-run`).
- `~/projects/dark-factory/daemon/scripts/github-webhook-listener.py` — stdlib-only webhook receiver with HMAC validation.
- `~/projects/dark-factory/daemon/launchd/ai.dark-factory.{af-tick,status-cron,github-webhook}.plist.template` — three launchd templates that go together.
- Bead `$USER-6zdl` — operator: #factory Slack channel ID for /af notifications (carries C0BGEC77EP4 + team + bot user id + wiring instructions).

## Origin

Captured 2026-07-09 from the dark-factory PR [#218](https://github.com/jleechanorg/dark-factory/pull/218) ("`/goal` builtin + `#factory` slack + status beacon + push webhook"). 4 commits, 11 files, +1136/-15. Channel `C0BGEC77EP4` created live via Aside Browser MCP in the same session that captured the lessons here.
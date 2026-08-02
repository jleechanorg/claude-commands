---
name: executive-assistant
description: "Run a comprehensive morning executive assistant sweep for {{OWNER_NAME}}: check today's calendar, scan Gmail for flagged/important emails, review Slack action items, run system probes (load/disk/gateway), scan infra alert channels (worldai-alerts, mcp-mail, ai-general), and post a concise briefing to {{OWNER_NAME}}'s DM. Use when a cron or direct request triggers the executive assistant sweep."
---

# Executive Assistant Sweep

Produce a concise morning briefing for {{OWNER_NAME}} covering schedule, email, and Slack, then post it to their DM channel.

## Goal

Give {{OWNER_NAME}} one message that covers everything they need to be aware of right now — without fluff. Actionable items get explicit prompts ("Want me to draft a reply?").

## Resolver recovery for scheduled jobs

The library currently contains both this canonical skill and a compatibility overlay under `hermes-imports/executive-assistant`. A bare `skill_view(name='executive-assistant')` can therefore report an ambiguous name, while a scheduled-job preamble may say the skill was skipped.

When that happens, **do not conclude that the sweep workflow or user data is unavailable**. Use the deterministic fallback chain:

1. `skill_view(name='hermes-imports/executive-assistant')` — picks the named overlay (no name collision).
2. `read_file ~/.hermes/skills/executive-assistant/SKILL.md` (full path) — bypasses the resolver entirely and returns the canonical body. **This is the reliable path when the resolver is wedged.** skill_view with a trailing slash (e.g. `executive-assistant/`) is NOT a guaranteed escape hatch and may still return ambiguous.
3. Inspect `hermes-imports/executive-assistant` only as a compatibility overlay — never as the canonical source.

Continue the sweep and retain any runtime-required missing-skill warning in the final report. This is resolver recovery, not a blocker. For a worked example, see `references/2026-07-22-resolver-recovery-recipe.md`.

### Destination override + auto-delivery (refined 2026-07-23)

When the scheduled-job runtime says the final response is automatically delivered, **the cron scheduler's destination is the authoritative sink**. Concretely:

- A caller destination override in the cron prompt (e.g. "Deliver to #ai-general (NOT the operator's DM)") must still be honored in spirit: **post the brief to the prompt-specified channel** via the bot token (or xoxp fallback if the bot is locked out — see `references/delivery-fallback-recipe.md`).
- **Return the same brief as the cron scheduler's final response** so the scheduler's auto-delivery does not produce a duplicate from a different path. Do NOT call `send_message` from the cron session — the runtime's auto-delivery replaces any manual send.
- The two deliveries target the same channel when the prompt-caller's destination matches the scheduler's configured destination; they target different places when they diverge. Follow the prompt's explicit override if one is present, the scheduler's default otherwise.

## Workflow

### 1. Calendar — what's happening today

```bash
gog calendar events --all -a {{ASSISTANT_EMAIL}} --days=1 --max=100 --json --results-only
```

- Pull events from all calendars: `{{PERSONAL_EMAIL}}`, `{{PRIMARY_WORK_EMAIL}}`, `{{SECONDARY_CALENDAR_EMAIL_1}}`, `{{SECONDARY_CALENDAR_EMAIL_2}}`, `{{SECONDARY_CALENDAR_EMAIL_3}}`
- Include family/household events as context (not as action items)
- Group into sections: **Now / Today** (imminent), **Tonight**, **Upcoming** (next 2 days if unusual)
- Format: `HH:MM — event name` in local time (America/Los_Angeles)
- **Filter multi-week carry-forward events client-side** — `--from`/`--to` does NOT filter by event duration, only by start. Drop events whose `start.dateTime` is more than 24h before the window start (catches "Trip to Dublin"-style junk). See `references/calendar-junk-event-filter.md`.

### 2. Gmail — flagged and important messages

Use `gog` (NOT `himalaya` — `himalaya` is not installed by default on macOS; `gog` is what Homebrew provides).

```bash
gog gmail search 'is:starred' -a $USER@gmail.com --max=20 --json --results-only
gog gmail search 'is:important newer_than:1d' -a $USER@gmail.com --max=20 --json --results-only
gog gmail search 'is:unread newer_than:1d' -a $USER@gmail.com --max=30 --json --results-only
```

For each flagged email, include: sender, subject, one-line summary, and offer to draft a reply or pull full content.

**Pitfall — `gog gmail search` returns a top-level array, NOT `{threads: [...]}`:** see `references/gog-cli-commands.md`.

**Pitfall — `gog gmail thread get <id>` returns `{"thread":{"messages":[...]}}` and bodies are nested multipart base64url:** see `references/gog-thread-body-walk-recipe.md`.

### 3. Slack — action items needing {{OWNER_NAME}}

Default monitored channels (override via `~/.config/hermes/config.yaml`):
- `#all-$USER-ai` (`C09GRLXF9GR`) — operator direct line, top-priority unanswered posts
- `#ai-general` (`C0AJQ5M0A0Y`) — home channel, system reports (cmux Surface Report, etc.)
- `#worldai` (`C0AH3RY3DK6`) — your-project.com product / PR activity
- `#life` (`C0AMM2B4319`) — personal reminders (Cindil protein AM/PM, etc.)
- `#mcp-mail` (`C0A0AG6EELB`) — Agent Mail acks needed
- `#worldai-alerts` (`C0BCVG4F560`) — green-gate precheck PASS lines, BQ defect watcher

Look for:
- Open threads where {{OWNER_NAME}} asked a question and the bot hasn't answered yet
- Mentions of {{OWNER_NAME}} with no reply
- Anything marked urgent or pinned since the last sweep
- **Infra-channel stop-monitoring directives** ("we removed X, stop monitoring") need explicit routing — see P89 below.

**Bot-locked-out and channel access:** see `references/asymmetric-bot-channel-access.md` and P86/P87 below. Default to xoxp for reads if the bot returns `not_in_channel` for #ai-general / #worldai-alerts / #needs-jeff.

### 4. Deploys / system status

Check `#deploys` (or `#ai-general` for system reports like cmux Surface Report) for:
- Failed deploys or errors from the past 12h
- Successful deploys worth noting

**PR green-state verification:** `gh pr view` GraphQL is rate-limited on the keyring account — see P90 below and `references/github-pr-state-when-rate-limited.md`. When PR state is unfetchable from cron, surface under "🔴 Blocked / gaps" and cue the operator to cross-check via the GitHub web UI.

### 5. Life / personal reminders

Check `#life` (`C0AMM2B4319`) for:
- Reminders posted since last sweep (Cindil protein AM/PM, etc.)
- Follow-ups posted but not actioned
- Cron `ea-sweep-hourly` self-narration rows — these are scheduled-cron echoes of past briefs; skip the narration but extract any new material change in the same row.

### 6. Compose and post briefing

**Destination (per-sweep overrideable):** Default is `{{OWNER_NAME}}`'s DM channel. If the sweep caller (cron prompt or user message) names a specific channel — e.g. "deliver to #ai-general (NOT the operator's DM)" — use that channel instead. Per SOUL.md `slack-channel-routing-policy`, cron-generated briefs default to `#ai-general` (`C0AJQ5M0A0Y`); user-typed requests default to the originating channel.

**Format:**

For a narrow Gmail + next-24h Calendar cron, use `references/compact-gmail-calendar-digest.md`; it defines incident ranking, cascade deduplication, rolling-window filtering, exact three-section rendering, and automatic-delivery behavior.

**Archive the brief to disk** at `~/.hermes/memory/briefings/YYYY-MM-DD/HHMM-ea-sweep.md` so there's a searchable trail when the DM gets noisy or the bot loses DM access.

## Verified pitfalls (with provenance)

### P86 — Bot-locked-out / asymmetric channel access
Bot may be a member of `#all-$USER-ai` but locked out of `#worldai` / `#ai-general` / `#worldai-alerts`. Channel-read fallback chain: (1) bot token `conversations.history`; (2) xoxp user token; (3) cheap `reply_count` probe via `conversations.history` parent messages instead of `conversations.replies` when xoxp thread visibility is broken. See `references/asymmetric-bot-channel-access.md`.

### P87 — DM dedup via bot token is reliable even when bot is locked out of monitored channels
DM is always channel-scoped to the user-bot pair — `not_in_channel` does NOT apply. Bot can still `conversations.open(users=U09GH5BR3QU)` and `chat.postMessage` to DM. Use xoxp fallback for the post ONLY if the bot `chat.postMessage` itself returns `account_inactive` / `token_revoked`. See `references/bot-locked-out-dedup-probe.md`.

### P88 — Slack API JSON control chars break `json.loads`
`conversations.history` / `conversations.replies` responses contain raw `\n` (0x0a) in message text strings. Strip raw control bytes via `re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b'', raw)` before parsing. `json.loads(s, strict=False)` is NOT enough. See `references/slack-api-json-parse.md`.

### P89 — Operator "stop monitoring X" directives in infra channels (added 2026-07-17 20:08 PT sweep)
A top-level post like "We removed hermes staging so stop monitoring for it" in `#openclaw-health` is NOT a Q&A — it is an ops directive that needs follow-through (prune the watcher, kill the launchd plist, audit dependent scheduled crons). Don't surface it as just another Risky item; pair with a recommended next action. Sender is often workflow handle `U0AEZC7RX1Q` (unresolvable via `users_search`) rather than `U09GH5BR3QU` — treat as real operator intent regardless. Quote verbatim and propose an action.

### P90 — `gh pr view` GraphQL rate-limited → REST requires `repo`-scoped token (added 2026-07-17 20:08 PT sweep)
When `gh pr view` returns `GraphQL: API rate limit already exceeded for user ID 13840161`, the keyring account's GraphQL budget is exhausted. REST via `gh pr view --json` ALSO fails (same endpoint). `curl -H "Authorization: token ..."` requires a `repo`-scoped PAT for `jleechanorg/*`. If `GH_TOKEN_AGENTF` is empty in this session's bashrc (verified 2026-07-17 20:08 PT — agentf PAT not sourced), PR state is `unfetchable` from cron. Surface under "🔴 Blocked / gaps" with cue "cross-check via GitHub web UI before `MERGE APPROVED`". See `references/github-pr-state-when-rate-limited.md`.

### P91 — `gog calendar events` with `--from`/`--to` returns multi-week carry-forward events
`--from`/`--to` filter by event START, not duration. Multi-week junk events with start-times overlapping the window leak through (e.g. "Trip to Dublin | 2026-06-19 → 2026-08-23" surfaces in a `--from=2026-07-17` query). **Filter client-side by `duration < 48h`** when rendering, OR drop events whose `start.dateTime` is more than 24h before the window start. Verified 2026-07-17 16:04 PT. See `references/calendar-junk-event-filter.md`.

### P92 — All-day events with time-sensitive names need visual flag
`gog calendar events` returns `date` (no `dateTime`) for all-day events; the `HH:MM` formatter strips them to "all-day — Client tech at 11am". Time buried in title is invisible. When rendering all-day events whose title contains a time pattern (HH:MM, "at Xam/pm", "morning", "evening"), prefix with `:warning:` and surface under "Now / Today" or "Upcoming" with the extracted time. Verified 2026-07-14. See `references/all-day-event-time-extraction.md`.

### P93 — Chase balance alerts form a 3-burst cascade
A single Chase transaction generates 3 separate email rows: "sent $X" → "balance below $Y" → "overdrawn". Lead with the highest-severity line; treat as one event. Verified 2026-07-14 08:02 PT.

### P94 — Stacked-asks triage threshold (refined 2026-07-14 20:04 PT)
Ranked-triage format whenever ≥3 unanswered operator asks span ≥2 channels. Every item MUST have `conversations.replies total=1` (truly unanswered). Drop from queue if mid-sweep reply landed. See `references/stacked-asks-triage.md`.

### P95 — Downstream consumers must verify EA-brief asks against live channel history
The brief's "unanswered operator asks" list is a snapshot, not a live query. Re-run `conversations.history` before driving work; cross-check each cited ask; watch for conflation across channels/threads.

### P96 — Briefs decay — re-verify every "blocked" claim against live PR/issue state before acting on it (added 2026-07-24 08:10 PT sweep)
A morning briefing's "🔴 Blocked / needs you" list is a **point-in-time snapshot taken before cron delivery**, not an authoritative state. By the time the operator reads it (or replies to the briefing's "act on this?" prompt), state may have moved: PRs that were open may have merged in the clean-replay wave (e.g. dark-factory #470 → #474), or merged at the same time as the brief was being composed (#8462 cold-replica fix landed while the brief was being drafted).

**Mandatory before driving any item from the brief as "blocked":**
1. **`gh pr view <N> --json state,mergedAt,headRefName`** for each cited PR. If `mergedAt` is non-null, move it from "Blocked" to "Already done" — do NOT spawn AO workers for merged PRs.
2. **`conversations.replies` on each cited thread** with the user's "did we make X?" question. If a prior session already answered with the PR number, do NOT re-answer — surface as "answered at ts=...".
3. **Render a delta section in the reply**: 🟢 *Already done (brief was stale)* — list items that moved; 🟡 *Open, ready for review* — list items still actionable; 🔴 *Real blockers* — only the items that genuinely need operator attention.

**Concrete trigger**: any user message containing "act on this", "anything you want me to act on?", or a direct reply to a morning brief, that includes "🔴 Blocked" items. Re-verify against `gh pr view` BEFORE spawning AO workers.

**Bug-ref**: 2026-07-24 08:00 PT briefing flagged `dark-factory #470` as "clean replay + /green + merge" — actually closed 90 min earlier; clean replay at #474 merged at `e7882ecf`. Operator wasted attention on a non-issue. See `references/brief-staleness-reverify.md` for the full recipe + BQ-cost cross-check.

## Companion references

- `references/env-and-channels.md` — env vars + channel ID mapping (verified quarterly)
- `references/sweep-monitoring-channels.md` — which channels to scan and what they surface
- `references/system-probes-recipes.md` — load / disk / gateway / launchd probes with expected outputs
- `references/gateway-health-probe-recipe.md` — verify the gateway is actually up (`127.0.0.1:8643/health` is a known-bogus false-positive)
- `references/gog-cli-commands.md` — `gog` subcommand surface + pitfalls
- `references/gog-multipart-body-workaround.md` — multipart body issues with `gog gmail send`
- `references/slack-api-json-parse.md` — control-char JSON-parse workaround for `conversations.replies`
- `references/slack-mcp-fallback-recipe.md` — when MCP slack is unreachable, fall back to curl
- `references/slack-delivery-dead-recipe.md` — when Slack itself is dead (token revoked by Slack/Notion/GitHub secret scanner)
- `references/bot-locked-out-dedup-probe.md` — dedup probe must distinguish "no prior brief" from "bot can't read DM"
- `references/asymmetric-bot-channel-access.md` — bot is in some channels but not others; cheap `reply_count` probe via parent messages
- `references/all-day-event-time-extraction.md` — all-day events with time-sensitive names
- `references/stacked-asks-triage.md` — stacked unanswered operator asks; ranking algorithm + render
- `references/ezgha-fleet-failure-classes.md` — `fail_class` taxonomy for `#mcp-mail` ezgha fleet alerts
- `references/«redacted:xox…».md` — bot alive but member of zero channels; use SLACK_MCP_XOXP_TOKEN
- `references/midday-pressure-and-slack-auth-outage.md` — midday partial-sweep recipe for simultaneous load/disk/swap pressure plus Slack credential outage
- `references/dropped-thread-silent-die-evidence-2026-07-15.md` — diagnostic evidence for the dropped-thread-watcher silent-die pattern
- `references/ea-dedup-protocol.md` — 30-min sliding-window dedup discipline + worked examples
- `references/dedup-decision-tree.md` — visual decision tree for dedup hit vs full re-brief
- `references/channel-registry.md` — authoritative channel ID table (verified 2026-07-10)
- `references/$USER-identity.md` — frozen values for `{{OWNER_NAME}}`, `{{ASSISTANT_EMAIL}}` etc.
- `references/sample-brief.md` — reference shape of a well-formed brief
- `references/cron-mis-delivery-fix-recipe.md` — `hermes cron edit --deliver` recipe
- `references/calendar-junk-event-filter.md` — multi-week carry-forward event filter for gog calendar
- `references/github-pr-state-when-rate-limited.md` — `gh pr view` rate-limit fallback recipes (added 2026-07-17 20:08 PT)
- `references/delivery-fallback-recipe.md` — bot-locked-out xoxp user-token fallback when target channel returns `not_in_channel` (added 2026-07-20 sweep)
- `references/2026-07-22-resolver-recovery-recipe.md` — worked example of the `executive-assistant` ↔ `hermes-imports/executive-assistant` resolver collision + 3-step deterministic fallback chain (added 2026-07-23)
- `references/brief-staleness-reverify.md` — re-verify every "🔴 Blocked" item from a morning brief against live PR/thread state before acting on it (added 2026-07-24 08:10 PT)

## Delivery: per-sweep destination override + bot-locked-out fallback

**Default destination:** the operator's DM channel. The user's cron prompt may explicitly override — e.g. "Deliver the resulting briefing to #ai-general (NOT the operator's DM)". Honor the override.

**Bot-locked-out fallback (P95 — added 2026-07-20 sweep):** When the destination channel is one the bot is NOT a member of (`#ai-general` `C0AJQ5M0A0Y`, `#worldai-alerts` `C0BCVG4F560`, etc.), `mcp__slack__conversations_add_message` returns `{"error": "not_in_channel"}`. Per SOUL.md `slack-cross-workspace-fallback-xoxp`, fall back to xoxp user-token via curl — do NOT give up and post nothing. Full recipe with the `bash -l` env-var trap in `references/delivery-fallback-recipe.md`.

**Channel-default for cron briefs (P96):** Per `slack-channel-routing-policy`, cron-generated/system briefs default to `#ai-general` UNLESS the originating request specified a different channel. A cron prompt saying "Deliver to #ai-general (NOT the operator's DM)" is the canonical explicit override — it must be honored even when bot access is blocked (P95 fallback handles that).
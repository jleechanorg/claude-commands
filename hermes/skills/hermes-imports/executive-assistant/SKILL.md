---
name: executive-assistant
description: "Run a comprehensive morning executive assistant sweep for {{OWNER_NAME}}: check today's calendar, scan Gmail for flagged/important emails, review Slack action items, and post a concise briefing to {{OWNER_NAME}}'s DM. Use when a cron or direct request triggers the executive assistant sweep."
---

# Executive Assistant Sweep

Produce a concise morning briefing for {{OWNER_NAME}} covering schedule, email, and Slack, then post it to their DM channel.

## Goal

Give {{OWNER_NAME}} one message that covers everything they need to be aware of right now — without fluff. Actionable items get explicit prompts ("Want me to draft a reply?").

## Workflow

### 1. Calendar — what's happening today

```bash
gog calendar events --all -a {{ASSISTANT_EMAIL}} --days=1 --max=100 --json --results-only
```

- Pull events from all calendars: `{{PERSONAL_EMAIL}}`, `{{PRIMARY_WORK_EMAIL}}`, `{{SECONDARY_CALENDAR_EMAIL_1}}`, `{{SECONDARY_CALENDAR_EMAIL_2}}`, `{{SECONDARY_CALENDAR_EMAIL_3}}`
- Include family/household events as context (not as action items)
- Group into sections: **Now / Today** (imminent), **Tonight**, **Upcoming** (next 2 days if unusual)
- Format: `HH:MM — event name` in local time (America/Los_Angeles)

### 2. Gmail — flagged and important messages

Use the `himalaya` skill or shell email tools to check for:
- Starred / flagged messages
- Messages marked IMPORTANT by Gmail
- Any unread messages in the primary inbox from the last 24h that look high-priority (recruiters, legal, finance, urgent subject lines)

For each flagged email, include: sender, subject, one-line summary, and offer to draft a reply or pull full content.

### 3. Slack — action items needing {{OWNER_NAME}}

Check the channels in `config.yaml` (or the default monitored list). Look for:
- Open threads where {{OWNER_NAME}} asked a question and the bot hasn't answered yet
- Mentions of {{OWNER_NAME}} with no reply
- Anything marked urgent or pinned since the last sweep

Do **not** list every message — only items needing action.

### 4. Deploys / system status

Check `#deploys` or equivalent channel for:
- Failed deploys or errors from the past 12h
- Successful deploys worth noting

### 5. Life / personal reminders

Check `#life` or equivalent personal channel for:
- Reminders posted since last sweep
- Follow-ups that were posted but not actioned

### 6. Compose and post briefing

Post to {{OWNER_NAME}}'s DM channel (`$JLEECHAN_DM_CHANNEL`).

**Format:**

```
:spiral_calendar_pad: **Now / Today**
- HH:MM — event
- HH:MM — event

:email: **Email** (if anything flagged)
- Sender — Subject — one-line summary [offer to draft reply / pull full content]

:pushpin: **Slack action items** (if any)
- #channel — summary of what needs attention

:large_green_circle: **Deploys / system**
- status line

:necktie: **Tonight**
- HH:MM — event

Anything you want me to act on?
```

- Omit sections that have nothing to report
- Keep each line to one line
- Always end with an open offer to take action

## Safety rules

- Never post the briefing twice for the same sweep run (check if a briefing was already posted in the last 30 minutes before sending)
- If calendar access fails, still post what's available and note the failure
- If Gmail access fails, skip that section silently unless it was explicitly requested
- Stay silent on errors that don't affect the briefing content

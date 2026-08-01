---
name: daily-executive-briefing-protocol
description: "Run or fix the exec-assistant daily cron. Covers resolver-recovery (skill_view ambiguity → read_file canonical path), token resolution, channel-routing with cron-override, decay-verify of yesterday's queue (P96), and GitHub-API rate-limit fallback."
---

# Daily Executive Briefing Protocol

Durable knowledge harvested from the `hermes-imports/executive-assistant` sweep — the skill is template-driven and user-owned, so the lessons that survive across sessions belong here.

## Why this skill exists

The `executive-assistant` skill body contains unrendered placeholders (`{{OWNER_NAME}}`, `{{JLEECHAN_DM_CHANNEL}}`, `{{ASSISTANT_EMAIL}}`, `{{PERSONAL_EMAIL}}`, `{{PRIMARY_WORK_EMAIL}}`, `{{SECONDARY_CALENDAR_EMAIL_*}}`) that the agent must resolve at runtime. `config.yaml` does NOT populate them. This protocol documents the canonical resolution + the pitfalls a fresh cron spawn will hit.

## 1. Resolve template variables at runtime

```bash
OWNER_NAME="${OWNER_NAME:-Jeffrey Lee-Chan}"
JLEECHAN_DM_CHANNEL="${JLEECHAN_DM_CHANNEL:-D0AFTLEJGJU}"
ASSISTANT_EMAIL="${ASSISTANT_EMAIL:-$USER@gmail.com}"
PERSONAL_EMAIL="${PERSONAL_EMAIL:-$ASSISTANT_EMAIL}"
PRIMARY_WORK_EMAIL="${PRIMARY_WORK_EMAIL:-$USER@snapchat.com}"
```

Accounts to attempt (the user has multiple — `gog calendar events` accepts `-a <email>`):

| Account | Source | gog auth? |
|---|---|---|
| `$USER@gmail.com` | gmail / calendar owner | YES |
| `$USER@snapchat.com` | work calendar (Snap) | NO — private-only events returned with `(no title)` |
| `jleechanreclaim@gmail.com` | secondary | NO — silently returns "No auth" |
| `family04573895333712838899@group.calendar.google.com` | family | YES (reader) |
| `qclk155rem91cbcg1skco0auc0@group.calendar.google.com` | Fuji | YES (owner) |
| `7vt80l37nnnre3elo9k1g4k7s0@group.calendar.google.com` | Apartment Viewings | YES (writer) |
| `4ogrrv9qf2m96pg0kk27v2okeg@group.calendar.google.com` | jeff PA Scheduling | YES (owner) |

When `--all` includes a non-authed calendar, `gog` silently drops it — surface this in the briefing ONLY if it changes the answer.

## 2. Channel-routing rule — cron override WINS

The skill body says "post to `$JLEECHAN_DM_CHANNEL`." Cron invocations may pass an override (e.g. "Deliver to `#ai-general`"). **Cron override wins, always.** Default target is the DM channel:

| Channel | ID | When |
|---|---|---|
| `#ai-general` | `C0AJQ5M0A0Y` | default for home/digest output |
| `$JLEECHAN_DM_CHANNEL` | `D0AFTLEJGJU` | per-user direct line |
| `#life` | `C0AMM2B4319` | Life Digest variant from `morning-life-digest` |
| Cron override | varies | final word |

If unsure, post to `#ai-general` and link the canonical thread in the briefing body.

## 3. Fetch recipes that actually work

### Calendar (gog)

```bash
gog calendar events --all -a $USER@gmail.com --days=1 --max=100
# `--all` walks every readable calendar on the account.
# `--days=1` = today (00:00 → 24:00 local).
```

`gog calendar event <id>` requires the *exact* calendar ID — cross-account lookup returns 404. If `--all` returns an event with ID `…_20260731T190000Z`, it lives on `$USER@snapchat.com`; pulling it from `$USER@gmail.com` returns 404 (verified 2026-07-31).

### Gmail (gog)

```bash
gog gmail search "is:starred OR is:important newer_than:2d" -a $USER@gmail.com --max=15
```

`is:starred` = user-flagged. `is:important` = Gmail classifier. `newer_than:2d` = within last 48 h (covers overnight emails missed by the 24h filter).

### Slack history (curl, not terminal-spawned)

The `terminal` curl-to-slack.com HARD-BLOCK applies to agent-issued reads. Use direct bash curl:

**Path B — direct load from `~/.bashrc`** (verified working pattern, 2026-07-31):

```bash
TOKEN=$(grep '^export HERMES_SLACK_BOT_TOKEN=' ~/.bashrc \
        | sed 's/^export HERMES_SLACK_BOT_TOKEN=//' \
        | tr -d '"' | tr -d "'")
curl -fsS -H "Authorization: Bearer $TOKEN" \
  "https://slack.com/api/conversations.history?channel=<CHAN_ID>&limit=15"
```

The `launchd-env-wrapper.sh _extract_bashrc_var TOKEN` invocation does **not** export to the parent shell — sub-shell export dies with the wrapper. The direct `grep|sed|tr` recipe always works in cron shell contexts.

### Dedup against same-day prior digests

Before posting, search the target channel for the day's prior digest header and skip if posted within the last 6h.

## 4. Body shape

The `executive-assistant` skill specifies this format — keep it:

```
:spiral_calendar_pad: *Now / Today*
:email: *Email*
:pushpin: *Slack action items*
:large_green_circle: *Deploys / system*
:necktie: *Tonight*
Anything you want me to act on?
```

The `:necktie:` section can be omitted safely. The closing line "Anything you want me to act on?" must be present.

## 5. Pitfalls

- **Template variables unrendered** — every `{{X}}` must be substituted; the skill won't substitute for you.
- **Duplicate skill-name collision** — `executive-assistant` exists in both `~/.hermes/skills/` and `~/.hermes/skills/hermes-imports/`. Bare `skill_view(name='executive-assistant')` returns "Ambiguous". Always pass `hermes-imports/executive-assistant` if you mean the cataloged copy. Run `hermes curator adopt executive-assistant` if you want to unify.
- **Private Snap calendar events** render as `(no title)` — do NOT drop them. Surface as "private meeting" with start/end time.
- **Gmail reminder emails (`#life` cron echoes)** are not the digest — they are raw reminders (Mizraim, Cindil protein, etc.). Don't conflate.
- **AO bot replies (`U0A4G7LDJ4R`)** show as cronjob-confirmation messages — a useful signal, not noise.
- **`clawchief:daily-task-prep` failures** with `provider rate limit` are common morning failures (MiniMax / Anthropic 429). Worth surfacing as a deploys/system line.
- **Outbound secret gate** — briefing body MUST NOT contain any `xoxb-…`, `xoxp-…`, `xapp-…`, `https://user:token@…` token strings.
- **GitHub PR-state fetch often rate-limits from cron** — `gh pr view` GraphQL and `gh api repos/.../pulls/<N>` REST both return rate-limit errors without a `GH_TOKEN_AGENTF` PAT in `~/.bashrc`. Verified 2026-08-01 08:01 PT sweep: curl returned `Expecting value: line 1 column 1 (char 0)` (empty body, keyring account budget exhausted). Fallback: surface PR state as `unfetchable from cron — cross-check via GitHub web UI` and decay-verify on subsequent sweep. Reference `executive-assistant/SKILL.md` P90. Do NOT invent `merged=true/false` from a successful fetch of an unrelated field.
- **`executive-assistant` resolver-ambiguity bypass path** — when `skill_view(name='executive-assistant')` returns "Ambiguous", `read_file ~/.hermes/skills/executive-assistant/SKILL.md` (full absolute path) **always works** and returns the canonical body. The `hermes-imports/executive-assistant` alias path may itself be wedged when the prelude reports the skill was skipped; do not iterate both — go straight to `read_file` of the canonical path. Verified 2026-08-01 08:01 PT.

## 6. P96 — Re-verify yesterday's ask queue before posting

The `executive-assistant/SKILL.md` P96 rule is **mandatory at the top of every sweep**, not a closing cleanup. Before composing the brief body, the agent MUST decay-verify each ask surfaced in the prior brief:

1. For each cited PR: `gh pr view <N> --json state,mergedAt,headRefName,mergeable,statusCheckRollup` (or REST fallback). Move any `merged=true` from "🔴 Blocked" to "🟢 Already done".
2. For each cited Slack thread: `conversations.replies` check; if any earlier session already answered the user's question, surface as "answered at ts=…" (drop from queue).
3. Render the *delta table* at the top of the brief: 🟢 already done → 🟡 still open → 🔴 real blockers. Operator wasted attention (2026-07-24 08:00 PT brief) when `dark-factory #470` was flagged as "needs merge" but had actually closed 90 min earlier. Recipe: `executive-assistant/SKILL.md` references/brief-staleness-reverify.md.

When GitHub API rate-limits from cron (no `GH_TOKEN_AGENTF` PAT), PR state returns `unfetchable`. Mark the row with `unfetchable from cron — verify via web UI` in the delta table instead of guessing.

## 7. Memory / cross-links

- See also: `morning-life-digest` skill (variant that posts to `#life`).
- See also: `slack-channel-routing-policy` in SOUL.md (`#ai-general` default).
- See also: `launchd-env-wrapper.sh` quirks in MEMORY.md.
- See also: `executive-assistant/SKILL.md` — canonical sweep body, destination override rule, bot-token + xoxp fallback recipe.
- See also: `executive-assistant/references/brief-staleness-reverify.md` — full P96 recipe + worked-example bug-ref.

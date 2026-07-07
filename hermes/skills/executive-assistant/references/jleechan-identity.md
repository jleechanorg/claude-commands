# Resolved $USER identity (for sweep runtimes)

This file freezes the values that the `{{OWNER_NAME}}`, `{{ASSISTANT_EMAIL}}`, `{{PERSONAL_EMAIL}}`, `{{PRIMARY_WORK_EMAIL}}`, `{{SECONDARY_CALENDAR_EMAIL_*}}` placeholders in SKILL.md resolve to in this cron runtime. Verified 2026-07-04 sweep.

## Owner
- Display name: **Jeffrey Lee-Chan** (handle `$USER`)
- Slack user ID: `U09GH5BR3QU`
- Bot identity (hermes): `U0AEZC7RX1Q` (name `hermes`, app_id `A0AESRKA7L3`)
- DM channel: `D0AFTLEJGJU` (`$JLEECHAN_DM_CHANNEL`)
- Bot token source: `$HERMES_SLACK_BOT_TOKEN` from `~/.bashrc` (verified alive 2026-07-04)
- User/cron home: `$HOME`
- Timezone: `America/Los_Angeles`

## Google account wired through `gog`
- Single account configured today: **`$USER@gmail.com`**
- `gog calendar events --all -a $USER@gmail.com --days=1 --max=200 --json --results-only` works.
- `gog gmail search --account $USER@gmail.com "is:important OR is:starred newer_than:2d" --max=20 --json` works; response shape is `{"threads":[{"id","date","from","subject","labels","messageCount"},…], "nextPageToken"}`.
- No other personal/work accounts are wired; do **not** assume `{{PERSONAL_EMAIL}}` etc. resolves anywhere.

## Cron / hermes CLI quirks (verified 2026-07-04)
- `hermes cron create <schedule> [prompt] --name X --deliver slack:<chan> --repeat 1` is the **only** one-shot pattern that works. `--delete-after-run`, `--keep-after-run`, `--at 20m`, `--every 20m` do NOT exist as flags on the live CLI (verified via `hermes cron create --help`). `--repeat 1` + a single-token schedule string (`"20m"`, `"10m"`) is the canonical one-shot. The cron will fire once and sit idle.
- `hermes cron list` shows scheduled jobs with `Schedule:` + `Next run:` lines.

## Pitfall cross-references
- SKILL.md pitfall **P39** — placeholder substitution gap (this file is the lookup).
- SKILL.md pitfall **P38** — `hermes cron create` flag mismatch (details above).
- SKILL.md pitfall **P37** — Slack API JSON control-char workaround.

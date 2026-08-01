# Resolved $USER identity (for sweep runtimes)

This file freezes the values that the `{{OWNER_NAME}}`, `{{ASSISTANT_EMAIL}}`, `{{PERSONAL_EMAIL}}`, `{{PRIMARY_WORK_EMAIL}}`, `{{SECONDARY_CALENDAR_EMAIL_*}}` placeholders in SKILL.md resolve to in this cron runtime. **Bot identity and DM channel are the values live as of the most recent sweep — always re-verify with `auth.test` + `conversations.open()` at the top of the sweep, do NOT trust frozen values from past sessions.** Last sweep verification: **2026-07-14 16:02 PT**.

## Owner
- Display name: **Jeffrey Lee-Chan** (handle `$USER`)
- Slack user ID: `U09GH5BR3QU`
- **Bot identity (current live): `U0A4G7LDJ4R` (name `mcp_agent_mail`, bot_id `B0A3MS7G08P`, app_id `A0AESRKA7L3`)** — verified 2026-07-14 16:02 PT via `auth.test`
- **DM channel (current live): `D0A418NEHHC`** — verified 2026-07-14 16:02 PT via `conversations.open(users=U09GH5BR3QU)` (`already_open: true` confirms it)
- **DEPRECATED bot:** `U0AEZC7RX1Q` (hermes) was revoked 2026-07-12 after its token leaked via `jleechanorg/claude-commands` commit `10ca1b09`
- **DEPRECATED DM:** `D0AFTLEJGJU` belonged to the revoked `hermes` bot — `conversations.history` against it now returns `{"ok":false,"error":"channel_not_found"}` from any current token. **Do not use.**
- Bot token source: `$HERMES_SLACK_BOT_TOKEN` from `~/.bashrc` (verified alive 2026-07-14; the bashrc may still export `JLEECHAN_DM_CHANNEL=D0AFTLEJGJU` — that value is stale, always re-resolve)
- User/cron home: `$HOME`
- Timezone: `America/Los_Angeles`

## Google account wired through `gog`
- Single account configured today: **`$USER@gmail.com`**
- `gog calendar events --all -a $USER@gmail.com --days=2 --max=200 --json --results-only` works.
- `gog gmail search --account $USER@gmail.com "is:starred OR is:important newer_than:1d OR is:unread newer_than:1d -from:noreply -from:no-reply -from:notifications -from:newsletter -from:bot ..." --max=N --json --results-only` works.
- **`gog gmail search` returns a top-level JSON ARRAY, not a `{threads:[...], nextPageToken}` object.** Iterate the array directly. Verified 2026-07-13 + 2026-07-14.
- **To read a single thread's body:** use `gog gmail search` to find the thread `id`, then `gog gmail thread get <id> -a $USER@gmail.com` (or whatever the current verb is — `gog gmail messages get` does NOT exist as a subcommand). If `thread get` errors, try `gog gmail get <messageId>` with the message ID from the search result.
- No other personal/work accounts are wired; do **not** assume `{{PERSONAL_EMAIL}}` etc. resolves anywhere.

## Cron / hermes CLI quirks (verified 2026-07-14)
- **CORRECT `hermes cron create` syntax (positional, not flag-based):**
  ```bash
  hermes cron create "<schedule>" [prompt] --name X --deliver slack:<chan> --repeat 1
  ```
  - `schedule` is a **positional argument** (e.g. `"20m"`, `"10m"`, `"every 2h"`, `"0 9 * * *"`), NOT `--at` or `--every`. The `$USER-identity.md` 2026-07-04 note that `--at 20m` / `--every 20m` "do NOT exist" was correct in flag-form, but the canonical one-shot pattern uses positional schedule + `--repeat 1` + a one-token string.
  - `[prompt]` is also a positional argument. The current `hermes cron create` CLI **does NOT accept `--prompt` as a flag** — passing `--prompt "..."` produces `error: unrecognized arguments: --prompt` and exits 2 (verified 2026-07-14 16:04 PT).
  - `--name`, `--deliver`, `--repeat` are the only relevant flags for a one-shot cron.
  - `hermes cron list` shows scheduled jobs with `Schedule:` + `Next run:` lines.
  - For `--deliver`, `slack:<CHAN_ID>` (not `slack:#channel-name`) is the safe form — channel names can be ambiguous across workspaces.
- `--repeat 1` + a single-token schedule string (`"20m"`, `"10m"`) is the canonical one-shot. The cron will fire once and sit idle.

## Pitfall cross-references
- SKILL.md pitfall **P39** — placeholder substitution gap (this file is the lookup).
- SKILL.md pitfall **P38** — `hermes cron create` flag mismatch (details above; see P38a for the positional-vs-flag clarification).
- SKILL.md pitfall **P37** — Slack API JSON control-char workaround.

## Operator preference — brief shape (added 2026-07-14, 16:04 PT)
Jeffrey's 15:00 PT feedback ("Why are you giving me this report? I only need `<@U0AEZC7RX1Q>` to do it") is a **first-class style signal** for the brief. Interpretation, since `U0AEZC7RX1Q` is the revoked bot:
- He wants the brief to **drive work**, not just **report work**. Default to: name the action, identify the next dispatcher (AO worker, `bring-to-green` cron, direct API call), and surface concrete action options in the closing line.
- Avoid long opening summaries of "what changed" if no operator action is implied by the change. Lead with the operator-action queue.
- The 30-min dedup + 4-line delta discipline still holds, but a delta brief that only reports state with no operator action is the wrong shape — collapse to a single line or `[SILENT]`.

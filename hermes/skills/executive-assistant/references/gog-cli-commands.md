# `gog` CLI — Verified Commands for Gmail + Calendar

This file captures the actual `gog` (v0.10.0) command surface, verified on **2026-07-05** during an executive-assistant cron run on macOS 15.5. Many older skill drafts reference flags that do not exist on this version — consult this file first when `gog` returns `unknown flag` errors.

## Auth

`gog` stores OAuth tokens in macOS Keychain (`keyring_backend: keychain`).

```bash
gog auth list
# $USER@gmail.com          default                  oauth
# $USER@your-project.com  service-account  ...     service_account
```

- The `default` account is `$USER@gmail.com` (OAuth) — this is what the executive-assistant sweep should use.
- The service-account identity (`$USER@your-project.com`) is for worldarchitecture-ai Firebase admin work and cannot read personal Gmail or primary Calendar.

## DO NOT USE `gws` for personal Gmail/Calendar

`gws` (Google Workspace CLI) is configured with `GOOGLE_APPLICATION_CREDENTIALS` pointing at `~/serviceAccountKey.json` (worldarchitecture-ai Firebase admin SDK). It returns:

```
gws gmail users messages list ...
{"error":{"code":400,"message":"Precondition check failed.","reason":"failedPrecondition"}}

gws calendar events list ...
{"error":{"code":400,"message":"Required path parameter calendarId is missing..."}}
```

The first error means the service account has no Gmail scope. The second is a secondary validation error masking the same root cause. **Use `gog` instead.**

## Calendar

```bash
# List events on primary calendar
gog calendar events primary -a $USER@gmail.com \
  --from "2026-07-05T10:00:00-07:00" \
  --to   "2026-07-06T10:00:00-07:00" \
  --json

# All calendars (note: positional, no --all flag)
gog calendar events all -a $USER@gmail.com --from ... --to ... --json
```

### Verified flags

| Flag | Notes |
|---|---|
| `[<calendarId>]` | Positional. `primary`, an email, or `all`. |
| `-a / --account` | Email of the OAuth account. |
| `--from` | ISO 8601 with timezone offset (`-0700`, `-08:00`, or `Z`). |
| `--to` | Same as `--from`. |
| `--json` | Emit JSON envelope. `--results-only` strips envelope. |
| `--plain` | TSV (no colors). |
| `--select` | Dot-path field projection. |

### Common mistakes (do not write these)

- `gog calendar events --all` → `unknown flag: --all`. The flag is positional: `gog calendar events all`.
- `--days=1` → `unknown flag`. Use `--from/--to` with computed timestamps.
- `--max-results` → `unknown flag`. Use `--max` (number) on `gog gmail search`, but **calendar has no max flag** — paginate with tighter `--from/--to` windows.

### Timezone gotcha

UTC ranges pull in day-prior events. `--from 2026-07-05T00:00:00Z` is `2026-07-04T17:00 PT` — events scheduled for the morning of Jul 4 PT show up. **Always pass a `-0700` (PDT) or `-08:00` (PST) offset** to keep results in local-day boundaries.

## Gmail

```bash
# Plain-TSV search
gog gmail search "is:unread newer_than:2d" -a $USER@gmail.com --plain

# JSON envelope, results-only
gog gmail search "is:unread is:important" -a $USER@gmail.com --json --results-only

# Full message body
gog gmail messages get <messageId> -a $USER@gmail.com --plain
```

### Verified flags

| Flag | Notes |
|---|---|
| `<query>` | Positional. Standard Gmail search operators (`is:unread`, `is:important`, `is:starred`, `newer_than:Nd`, `from:`, `subject:`, `-from:`). |
| `-a / --account` | Email of the OAuth account. |
| `--max <N>` | Max results. |
| `--json` / `--plain` | Output format. |
| `--results-only` | Strip envelope when `--json`. |

### Common mistakes (do not write these)

- `gog gmail search --query "..."` → `unknown flag: --query`. The query is positional.
- `gog gmail search --max-results 10` → `unknown flag: --max-results`. Use `--max 10`.
- `gog gmail get <id>` → `unexpected argument get`. Use `gog gmail messages get <id>`.

## Decision matrix: which CLI?

| Task | Use | Why |
|---|---|---|
| Personal Gmail read/search/send | `gog` | OAuth user tokens in keychain |
| Personal Calendar read/write | `gog` | OAuth user tokens in keychain |
| worldarchitecture-ai Firestore service account | `gws` | Has Firebase admin scope |
| Drive/Sheets/Docs service account ops | `gws` | Service account scopes |
| Personal Drive/Sheets/Docs | `gog` | Same OAuth user tokens work |
| IMAP/SMTP fallback (rare) | `himalaya` | Only if `gog` OAuth breaks |
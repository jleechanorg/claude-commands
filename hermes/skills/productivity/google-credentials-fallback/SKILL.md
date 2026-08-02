---
name: google-credentials-fallback
description: "Use already-installed `gws` or `gog` (gogcli) credentials when Hermes's own Google OAuth setup has not been run. Reuses the refresh token from the working CLI to call Gmail/Calendar/Drive APIs directly via curl, avoiding a full OAuth re-setup. Activates when `$GSETUP --check` returns NOT_AUTHENTICATED but `gws` or `gog` is on PATH and authenticated. Also handles user-shared Google Doc URLs (docs.google.com/document/d/<ID>/edit) — `gws` 403s on personal shared Docs (service-account auth), use `gog docs info` + `gog docs export --format txt` instead."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [google, gmail, calendar, drive, docs, oauth, gws, gog, gogcli, fallback]
    related_skills: [productivity/google-workspace]
---

# google-credentials-fallback

Reuse an already-authenticated `gws` or `gog` (gogcli) install on the same machine instead of running the full Hermes Google Workspace OAuth setup. Useful when:

- `$GSETUP --check` returns `NOT_AUTHENTICATED`.
- The user already has `gws` or `gog` installed and authorized (likely from prior work).
- You only need to read Gmail, list calendar events, or fetch a Drive/Docs file from a cron job or short-lived agent session.

## References

- `references/daily-digest-cron-recipe.md` — verified working recipe for a Gmail + Calendar → Slack morning digest cron (gog v0.10.0, `--from`/`--to` workaround for the `--days` bug).

When this skill applies, the bundled `productivity/google-workspace` skill's `$GAPI` wrapper cannot be used because no `~/.hermes/google_token.json` exists. This skill provides the working alternative.

**Verified 2026-07-09** against a host with both CLIs:
- `gws` is authorized as `firebase-adminsdk-…@worldarchitecture-ai.iam.gserviceaccount.com` (service account, empty calendar).
- `gog` is authorized as `$USER@gmail.com` (personal OAuth).

---

## When to activate

Trigger condition: any task needs Gmail / Calendar / Drive / Docs / Sheets and `$GSETUP --check` says `NOT_AUTHENTICATED`. Before running the 5-step OAuth setup, check if a working CLI is already on the host:

```bash
which gws gog 2>&1
gog auth list 2>&1         # shows accounts + auth type (oauth / service-account)
```

If `gog auth list` shows the user account you need, skip Hermes OAuth setup and read the existing credentials file directly.

---

## 1. Locate the working credentials

```bash
# gws
ls -la ~/.config/gws/ 2>&1
ls -la ~/Library/Application\ Support/gwscli/ 2>&1

# gog (gogcli)
ls -la ~/Library/Application\ Support/gogcli/ 2>&1
cat ~/Library/Application\ Support/gogcli/credentials.json
cat ~/Library/Application\ Support/gogcli/config.json
```

gog's `credentials.json` contains `client_id`, `client_secret`, and a `refresh_token` directly in the JSON — no keychain unlock required. **Treat as a secret; never paste in chat/logs.**

The `services` array and `scopes` array tell you which APIs the refresh token can hit (commonly: gmail, calendar, drive, docs).

---

## 2. Try the native CLIs first (fastest)

### `gog` (gogcli) — preferred for personal Gmail/Calendar

```bash
GOG="-a $USER@gmail.com --enable-commands=gmail calendar"

$gog $GOG gmail search "is:unread newer_than:3d" --max 15
$gog $GOG calendar calendars          # list calendar IDs and roles
```

### `gws` (googleworkspace/cli) — preferred for Workspace / service-account

```bash
gws calendar events list --params '{"calendarId": "primary", "timeMin": "…", "timeMax": "…", "maxResults": 10}'
gws gmail users messages list --params '{"userId": "me", "q": "is:unread newer_than:3d", "maxResults": 10}'
```

### Known bugs (work around with curl below)

- `gog ≤ 0.10.0`: `gog calendar events list --days 2` returns `Google API error (404 notFound)` against the OAuth default account.
- `gws (2026-07)`: `gws gmail users messages list` returns `Precondition check failed` for personal Gmail.
- gog positional arg parsing treats `primary` as a subcommand, not a calendarId.

**Working alternative for the calendar bug (verified 2026-07-12):** use `--from` / `--to` with RFC3339 UTC timestamps instead of `--days N`. Example:

```bash
FROM_TS=$(date -u -v+0H "+%Y-%m-%dT%H:%M:%SZ")
TO_TS=$(date -u -v+24H "+%Y-%m-%dT%H:%M:%SZ")
gog calendar list --from "$FROM_TS" --to "$TO_TS" --json --results-only -a $USER@gmail.com
```

This works on `gog v0.10.0` against personal Gmail and returns full event details (id, summary, start/end, attendees, hangoutLink).

When `gog calendar list` still fails, jump straight to curl — the Google REST API is unaffected.

---

## 3. Direct curl with the stored refresh token

The bypass that always works. Same `refresh_token` as gog, direct to Google's REST endpoints.

### Get an access token

```bash
ACCESS_TOKEN=$(curl -s -X POST https://oauth2.googleapis.com/token \
  -d "client_id=$(jq -r .client_id ~/Library/Application\ Support/gogcli/credentials.json)" \
  -d "client_secret=$(jq -r .client_secret ~/Library/Application\ Support/gogcli/credentials.json)" \
  -d "refresh_token=$(jq -r .refresh_token ~/Library/Application\ Support/gogcli/credentials.json)" \
  -d "grant_type=refresh_token" \
  -d "scope=https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/gmail.modify openid" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token','ERROR'))")

# Always verify length, never log the value
[ "${#ACCESS_TOKEN}" -gt 50 ] && echo "got token len=${#ACCESS_TOKEN}"
```

### Gmail: list + get metadata

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=20&q=is:unread+newer_than:2d+-category:promotions" \
  | python3 -m json.tool

curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages/<MESSAGE_ID>?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date"
```

### Calendar: list events (include or exclude to scope a window)

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/calendar/v3/calendars/$USER%40gmail.com/events?timeMin=2026-07-09T16:00:00Z&timeMax=2026-07-10T16:00:00Z&singleEvents=true&orderBy=startTime&maxResults=25" \
  | python3 -m json.tool
```

`calendarId` in the URL must be URL-encoded (`@` → `%40`). Use `gog calendar calendars` to enumerate the IDs the user can see; the OAuth default may be a service-account calendar that is empty by design — that's not a bug, just not the one you want.

### Drive / Docs / Sheets / People

Same `Bearer` token + the appropriate `https://www.googleapis.com/{drive|docs|sheets|people}/v3/...` endpoints, provided the refresh token's `services` list includes them (it usually does for `drive`, `docs`).

---

## 4. When to write back to Hermes-managed credentials

Use the curl/gog path as a **stopgap**. If the user wants long-term canonical access from Hermes, run the bundled `google-workspace` skill's first-time setup once (Steps 2–5 in that skill's `SKILL.md`). You can speed it up by reusing the `client_id`/`client_secret`/`refresh_token` triple already in `~/Library/Application Support/gogcli/credentials.json` — write it as a Desktop OAuth JSON, then `$GSETUP --client-secret …` against it. Step 4 (auth-code exchange) may not even be needed if the refresh token was minted against the same client_id.

After this, `$GAPI gmail search …` and `$GAPI calendar list …` work normally and should be used in place of the curl fallback.

---

## 5. Drive corpus search (find + read a constellation of Google Docs)

When the user asks "find all my old X campaigns / Y documents / Z shared notes" and the answer lives as a **constellation of Google Docs** (not a single one), use the Drive search pattern. Verified 2026-07-20 against $USER@gmail.com while finding the **god-of-tyranny Aizen campaign corpus** (16+ Google Docs spanning 2025-06-14 → 2026-02-09).

### Drive search — the right `gog` subcommand is `drive search`, NOT `docs search`

```bash
# CORRECT — gog 0.10.0 has no `gog docs search` subcommand
gog drive search --query "Aizen god" --max 20 -a $USER@gmail.com --json
gog drive search --query "campaign nocturne" --max 50 -a $USER@gmail.com --json

# WRONG — returns "unknown subcommand" or empty
gog docs search "Aizen god"
gog drive docs search "Aizen god"
```

### Drive download — Google Docs export as PDF is automatic

```bash
# Google Doc → auto-exports as PDF (preserves structure, fonts, images)
gog drive download --file-id 1L1sOStC7rVjCzE8KHhpMf55TarmvNXNuEx-RH2vwO-0 \
    --output ~/tmp/aizen_origin.pdf -a $USER@gmail.com

# Plain text file (.txt) → downloads as .txt directly
gog drive download --file-id 1HnRXmsl8rcB5_ZNmO7WkDIxhTTZCZw0n \
    --output ~/tmp/aizen_godhood_3.txt -a $USER@gmail.com

# PDF (e.g. "Aizen god campaign book 2.pdf") → downloads as PDF
gog drive download --file-id 1hkW_iJZCy7CoOZfCuuj__Q_qz6IGPEE7 \
    --output ~/tmp/aizen_book2.pdf -a $USER@gmail.com
```

Then `pdftotext <pdf> -` to extract text. Some PDFs (especially older Google Docs) fail `pdftotext` cleanly — fall back to `pdfinfo` for metadata + the Drive `webViewLink` for manual read.

### Field reference for `gog drive search --json` output

| Field | What it is | Use it for |
|---|---|---|
| `id` | Drive file ID (used in `drive download`) | Dedupe, pass to download |
| `name` | Filename incl. extension | Sort, filter, group by topic |
| `mimeType` | `application/vnd.google-apps.document` = Google Doc; `text/plain` = raw text; `application/pdf` = PDF | Decide download path (Google Docs auto-export PDF; raw text stays text) |
| `modifiedTime` | RFC3339 UTC | Sort newest-first / filter by date range |
| `size` | Bytes (only set for non-Google-Docs native files) | Estimate download time |
| `webViewLink` | `https://drive.google.com/file/d/<id>/view` | Share-able URL for the user |

### Recipe: "find and inventory" a constellation

```bash
# 1. Multi-keyword fan-out
for kw in "Aizen god" "campaign nocturne" "noctune bg3" "campaign aizen"; do
    gog drive search --query "$kw" --max 50 -a $USER@gmail.com --json \
        | jq -r '.files[]? | [.id, .name, .mimeType, .modifiedTime] | @tsv'
done | sort -u -k1,1  # dedupe by file id

# 2. For each hit, dump metadata to a manifest
# (id, name, mimeType, modifiedTime, size, webViewLink)
gog drive info --file-id <id> -a $USER@gmail.com --json

# 3. Download all in parallel (gog supports it; xargs -P 4 is fine)
cat ids.txt | xargs -P 4 -I{} sh -c 'gog drive download --file-id {} --output ~/tmp/{}.pdf -a $USER@gmail.com'

# 4. Extract text from PDFs (parallel)
find ~/tmp -name "*.pdf" | xargs -P 4 -I{} pdftotext {} -
```

### Why this exists

`gws` **403s** on personal shared Google Docs (it's authorized to a service account). `gog drive search` + `gog drive download` is the working path for the user's own account, and it preserves the Google-Doc-as-PDF auto-export behavior. Verifying a Google Doc was correctly retrieved means: download size > 50 KB (Google Docs PDFs are ~100KB+ even for short docs) + `pdftotext` returns non-empty output + first paragraph matches the user's recollection.

## Pitfalls

- **Multiple-account confusion.** `gws` and `gog` may be authorized to *different* accounts on the same host (gws → service account; gog → personal). The active credentials vary by CLI. Confirm which account answered by reading the response's `user.email` (Gmail) or `summary` (Calendar) field, not by which CLI you invoked.
- **Service-account calendars show no events.** A "calendarId=primary" call to gws returning `items: []` and a `firebase-adminsdk-…` summary is the service account's empty calendar — not an auth error. Query the user's personal `$USER@gmail.com` calendar instead.
- **gog positional arg gotcha.** `gog calendar events list primary --days 2` parses `primary` as a subcommand. Use no positional arg for the default, or pass `--calendar=…` if supported; fall back to curl.
- **Don't paste the access token into logs.** Echo `ACCESS_TOKEN_LEN=${#ACCESS_TOKEN}` instead of the raw value when running through a logged tool.
- **Don't run the full 5-step OAuth setup** if gog/gws already work — read the stored credentials and use them. The user shouldn't have to re-authorize twice.
- **The bundled `google-workspace` skill is locked.** You cannot patch its `SKILL.md` from a cron session. This skill is the user-editable mirror for the "Hermes not set up but a CLI is" branch.

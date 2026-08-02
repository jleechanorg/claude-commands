# `gog` + `gws` Tool Quirks

Captured 2026-07-22 from live invocations; revised 2026-07-27 after a real
multi-account calendar run surfaced auth/shape bugs.

Binaries (verify before use — they move):

- `gog`: `/opt/homebrew/bin/gog` (homebrew)
- `gws`: `$HOME/.nvm/versions/node/v22.22.0/bin/gws` (nvm node)

## TL;DR — use `gog`, not `gws`, for personal calendar queries

`gws calendar events list` is wired to the
`firebase-adminsdk-fbsvc@worldarchitecture-ai.iam.gserviceaccount.com` service
account by default, NOT to `$USER@gmail.com`. Calling `gws calendar events list`
without an authenticated user returns the SA's empty (or SA-populated)
calendar. `gws` has NO `--account` flag — verified 2026-07-27:

```
$ gws calendar events list --account $USER@gmail.com --params '{...}'
error: unexpected argument '--account' found
```

`gws auth status` returns `"auth_method": "none"` even when cached tokens
let the call succeed — confusing but expected. Use `gog` for end-user
calendar queries.

## `gog gmail search`

```
Usage: gog gmail search <query> ... [flags]
Flags:
  -n, --max=10                Max results          ← NOT --max-results
  -j, --json                  Output JSON
  -p, --plain                 TSV output (no colors)
      --results-only          Strip envelope fields
      --page=STRING           Page token
      --all                   Fetch all pages
      --oldest                Show first message date
      --timezone=STRING       IANA tz (default local)
```

Other useful:

- `gog gmail thread <thread-id> --json` for full message body
- `--account=<email>` to switch accounts (default keyring picks the first)

## `gog calendar events` (CANONICAL for the digest)

```
Usage: gog calendar (cal) events (list,ls) [<calendarId>] [flags]
Flags:
  -a, --account=STRING        Account email for API commands
  --from=STRING               Start time (RFC3339, date, or relative: today, tomorrow, monday)
  --to=STRING                 End time (RFC3339, date, or relative)
  --today                     Today only (timezone-aware)
  --tomorrow                  Tomorrow only (timezone-aware)
  --week                      This week (uses --week-start, default Mon)
  --days=0                    Next N days (timezone-aware)
  --max=10                    Max results
  --all                       Fetch events from all calendars
  --json                      Output JSON
```

### Multi-account loop (canonical for the digest)

```bash
for ACCT in $USER@gmail.com jleechan2015@gmail.com $USER@your-project.com; do
  gog calendar events --account "$ACCT" \
    --from '2026-07-27T17:30:00-07:00' \
    --to '2026-07-28T17:30:00-07:00' \
    --max 50 --all --json
done
```

If `--account` is omitted, `gog` falls back to the keyring's first stored
account. With no keyring entry it errors with `No auth for calendar <email>`.

### CRITICAL JSON shape pitfall

`gog calendar events --all` returns `{"events":[...]}` — NOT `{"items":[...]}`.

`gog calendar events primary` (or with a single calendarId) ALSO returns
`{"events":[...]}`.

Always parse defensively:

```python
data = json.loads(out[out.find('{'):])
items = data.get("items", data.get("events", []))
```

If you only check `data["items"]` you'll see zero events and falsely conclude
the calendar is empty — this bit the 2026-07-27 run for 5 calls before the
real shape surfaced in a narrower-window query.

### Recurring event instances

When Google returns an INSTANCE of a recurring event (id like
`60pnucuc2mllh03cdb9a0c4ess_20260728T163000Z`), the JSON typically includes
`summary` and `recurringEventId`. Fetching the master event by the recurring
base id returns 404 (`Not Found`). Just rely on the per-instance summary;
don't try to resolve masters.

### Account auth failures

```
$ gog calendar events --account jleechan2015@gmail.com ...
No auth for calendar jleechan2015@gmail.com.
OAuth (browser flow):
  gog auth add jleechan2015@gmail.com --services calendar
Workspace service account (domain-wide delegation):
  gog auth service-ac...
```

When one account is unauthenticated, fall through and report the missing auth
in the digest's "Action needed" section (current cron run is missing
`jleechan2015@gmail.com` — this surfaces every time).

## `gws calendar events list` (avoid for this digest)

```
Usage: gws events list [OPTIONS]
Options:
  --params <JSON>             All parameters via JSON (URL + query)
  --format <FORMAT>           json (default) | table | yaml | csv
  --page-all / --page-limit / --page-delay   pagination
  --output <PATH>             binary response dump
  --dry-run                   validate locally
```

### Mandatory shape

```bash
gws calendar events list --params "{\"calendarId\":\"primary\",\"timeMin\":\"...\",\"timeMax\":\"...\",\"maxResults\":15,\"singleEvents\":true,\"orderBy\":\"startTime\"}"
```

⚠️ `calendarId` is required even if you only want the user's primary calendar.
There is no `--today` / `--now` shortcut — build `timeMin` / `timeMax` from
`date` in the shell.

### Output has a leading noise line

First line of stdout is:

```
Using keyring backend: keyring
```

Direct `json.loads(sys.stdin.read())` will fail with `Extra data: line 1`.
Fix:

```python
raw = sys.stdin.read()
i = raw.find('{')
if i > 0: raw = raw[i:]
d = json.loads(raw)
```

### Default account is the SA, not the user

`gws calendar events list` with no further auth and a cached token returns
events for whichever Workspace service account the cached token is bound to.
On this machine that's `firebase-adminsdk-fbsvc@worldarchitecture-ai.iam.gserviceaccount.com`
— essentially empty for personal scheduling. Don't trust it for the digest.

## `gog` vs `gws` auth

Both read from macOS keyring on macOS. No flags needed unless switching
accounts explicitly. Failure mode if keyring is locked: silent exit-code-0
with `error: ...` in JSON — always check the JSON's `error` field before
trusting the result.

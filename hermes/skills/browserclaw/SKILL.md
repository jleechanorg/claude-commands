---
name: browserclaw
description: Use the browserclaw CLI to capture browser traffic, infer API endpoints, generate Python clients, OR decrypt + inject Chrome cookies for session reuse. Use when asked to reverse-engineer a website, generate an API client from a HAR, or reuse a logged-in Chrome session in a Playwright browser.
agent_scope: Any AI agent (Codex, Claude Code, Hermes, AO)
---

# browserclaw

## What this skill covers

The `browserclaw` CLI (a single Python binary installed via `pip install -e .`) has two halves:

1. **Traffic capture + client generation** — record a Chromium session to a HAR, infer the API endpoints, emit a `requests`-based Python client + MCP tool definitions.
2. **Cookie decrypt + inject** (introduced in PR [#6](https://github.com/jleechanorg/browserclaw/pull/6)) — read the user's *logged-in* cookies out of the local Chrome/Brave/Edge SQLite DB, decrypt the AES-128 ciphertext using the macOS Keychain password, and inject them into a fresh Playwright Chrome so an agent can act as that user without re-authenticating.

This file documents the **cookies** subcommands. The capture / infer / generate flow is documented in `~/.claude/skills/browserclaw/SKILL.md` (legacy) and the upstream `browserclaw/SKILL.md`.

## When to use `cookies decrypt` + `cookies inject`

Use this pair when:

- The site is behind a login that requires MFA / SSO / WebAuthn (programmatic re-auth is impractical).
- The user has Chrome open and already logged into the target site.
- You need a Playwright session that **appears as the user** — same cookies, same session, same auth tokens.
- A token rotation / `invalid_auth` incident requires you to read what cookies Chrome currently has so you can decide whether to re-decrypt or escalate.

Do **not** use this for:

- Sites you do not have permission to access. The skill trusts the user's local keychain; if you are not the user, this is unauthorized access.
- Bypassing 2FA, CAPTCHAs, or anti-bot protections. The skill reuses an existing logged-in session — it does not break new ones.
- Linux/Windows browsers. The PBKDF2 + Keychain parameters are macOS-only (salt `saltysalt`, iterations `1003`, IV = 16 spaces). Linux Chromium uses `peanuts` / 1 iteration and is not supported by this CLI yet.

## Prerequisites

```bash
# From a checked-out browserclaw worktree or installed wheel
pip install -e '.[dev]'
python -m playwright install chromium
# cryptography>=42.0.0 is the only new dep introduced by PR #6
```

- macOS only (uses `security find-generic-password` against the Login keychain).
- Chrome (default) or Brave / Edge with explicit `--keychain-service` / `--keychain-account` flags.
- The user must have already logged into the target site in Chrome at least once (the SQLite Cookies DB must contain the encrypted values).
- Chrome must have been closed OR the file must be readable — the CLI copies the DB to a temp file before opening, so live read is safe even while Chrome is running, but a value that exists *only* in Chrome's in-memory cache may not yet be flushed to disk.

## Subcommand: `browserclaw cookies decrypt`

Read the local Chrome Cookies SQLite DB, decrypt every cookie value with the Keychain-derived AES key, and write a Playwright-compatible JSON.

### Synopsis

```bash
browserclaw cookies decrypt \
  --db ~/Library/Application\ Support/Google/Chrome/Default/Cookies \
  --output ./cookies.json \
  [--domain-filter '%slack.com%'] \
  [--keychain-service 'Chrome Safe Storage'] \
  [--keychain-account 'Chrome'] \
  [--summary]
```

### Arguments

| Flag | Type | Default | Required | Purpose |
|---|---|---|---|---|
| `--db` | path | — | yes | Absolute path to the Chromium-format Cookies SQLite. The CLI copies it to a temp file before opening, so passing the live Chrome-locked path is safe. |
| `--output`, `-o` | path | — | yes | Destination for the decrypted JSON (Playwright `storage_state` shape: `{"cookies": [...], "origins": []}`). |
| `--domain-filter` | str | `%` | no | SQL `LIKE` pattern against `host_key`. Use `%slack.com%` to grab only Slack cookies, `%.google.com%` to grab all subdomains. |
| `--keychain-service` | str | `Chrome Safe Storage` | no | Override for Brave (`Brave Safe Storage`) or Edge (`Microsoft Edge Safe Storage`). |
| `--keychain-account` | str | `Chrome` | no | Override for Brave (`Brave`) or Edge (`Microsoft Edge`). |
| `--summary` | flag | off | no | Print a one-line `domain name len=N` per cookie instead of full values. Use when debugging to avoid logging tokens. |

### Outputs

- Writes `--output` as a Playwright storage_state JSON: `{"cookies": [{"name","value","domain","path","expires","secure","httpOnly","sameSite"}, ...], "origins": []}`.
- Prints either the JSON summary (default) or the per-cookie summary lines (`--summary`).
- Exit code `0` on success, non-zero on `CookieDecryptError` (missing DB, empty file, no `meta.version` row, Keychain lookup failure).

### Example — extract Slack cookies for an agent run

```bash
browserclaw cookies decrypt \
  --db ~/Library/Application\ Support/Google/Chrome/Default/Cookies \
  --output /tmp/slack-cookies.json \
  --domain-filter '%slack.com%' \
  --summary
# Wrote 26 cookies to /tmp/slack-cookies.json
#   .slack.com                          d                     len=  225
#   .slack.com                          d-s                   len=   35
#   .slack.com                          b                     len=   18
#   .slack.com                          lc                    len=   31
#   .slack.com                          oi                    len=   17
```

### Example — Brave browser

```bash
browserclaw cookies decrypt \
  --db ~/Library/Application\ Support/BraveSoftware/Brave-Browser/Default/Cookies \
  --output /tmp/brave-cookies.json \
  --keychain-service 'Brave Safe Storage' \
  --keychain-account 'Brave'
```

### Example — Aside browser (2026-06-27, primary browser)

Aside uses the same Chromium v24 cookie schema but its own Keychain entry (`Aside Safe Storage`). The DB path is `~/Library/Application Support/Aside/Default/Cookies`.

```bash
browserclaw cookies decrypt \
  --db ~/Library/Application\ Support/Aside/Default/Cookies \
  --output /tmp/aside-cookies.json \
  --keychain-service 'Aside Safe Storage' \
  --keychain-account 'Aside'
```

**Keychain prerequisite:** the `Aside Safe Storage` entry is only created after Aside writes its first cookie to disk. If you see `Keychain lookup failed for service='Aside Safe Storage' account='Aside'`, log into a site in Aside once (any login), then re-run. Verify the entry exists:

```bash
security find-generic-password -s 'Aside Safe Storage' -a 'Aside' -w
```

**Cross-browser portability warning:** the underlying PBKDF2 password is per-browser (each browser has its own Keychain entry). Even after `cookies decrypt` succeeds, cookies decrypted from Aside cannot be replayed into a Chrome session and vice versa without re-encryption under the target's password — `browserclaw` does NOT do this re-encryption. Use the `cookies decrypt` + `cookies inject` cycle only on the same browser that produced the cookies.

### Edge cases / failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `CookieDecryptError: Cookie DB not found` | Wrong path or the browser is not installed | Confirm path with `ls "$HOME/Library/Application Support/Google/Chrome/Default/Cookies"` |
| `CookieDecryptError: Cookie DB is empty` | Chrome is currently writing to it; live copy is zero bytes | Quit Chrome fully, then re-run |
| `CookieDecryptError: is not a Chromium Cookies DB (no meta.version row)` | Wrong file — it's not a Chromium Cookies SQLite | Check `--db` is a `Cookies` file, not `Cookies-journal` or `Login Data` |
| `Keychain lookup failed for service='Chrome Safe Storage' account='Chrome'` | User clicked "Deny" on the keychain prompt, or the entry was removed | Open Keychain Access.app, search for `Chrome Safe Storage`, ensure it exists; re-run and click "Always Allow" |
| Output JSON has 0 cookies | `--domain-filter` is too narrow, or the user is not logged into that site in this profile | Drop `--domain-filter` to `%`, or switch `--db` to the correct profile (`Profile 1`, `Profile 2`, …) |

## Subcommand: `browserclaw cookies inject`

Open a Playwright Chrome (or `chromium`), inject the cookies from a previously-decrypted JSON, navigate to a target URL, and optionally screenshot / dump page text.

### Synopsis

```bash
browserclaw cookies inject \
  --cookies ./cookies.json \
  --goto https://app.slack.com/client \
  [--browser-channel chrome] \
  [--headless] \
  [--wait-after-load 5] \
  [--screenshot /tmp/slack-home.png] \
  [--print-text 500]
```

### Arguments

| Flag | Type | Default | Required | Purpose |
|---|---|---|---|---|
| `--cookies` | path | — | yes | Path to a cookies JSON. Either the output of `cookies decrypt` or any Playwright `storage_state` file. |
| `--goto` | URL | — | yes | Where to navigate after injection. Must be a URL whose domain matches the cookies (cookies are domain-scoped). |
| `--browser-channel` | str | `chrome` | no | Playwright channel. Use `chrome` for the real installed Chrome, `chromium` for the headless test build, `msedge` for Edge. |
| `--headless` | flag | off | no | Run without a visible window. Combine with `--screenshot` for evidence capture. |
| `--wait-after-load` | float | `5.0` | no | Seconds to wait after `page.goto` returns, before printing diagnostics. Increase for SPAs that hydrate slowly. |
| `--screenshot` | path | off | no | If set, save a full-page screenshot after navigation. Great for evidence + Slack thread attachments. |
| `--print-text` | int | `0` | no | If `> 0`, print the first N characters of `document.body.innerText` after navigation. Useful for verifying the page loaded as the expected user. |

### Outputs

- Opens (or spawns) a real browser window — visible by default unless `--headless`.
- Prints the final URL, page title, and any `--print-text` content to stdout.
- Writes screenshot to `--screenshot` path if provided.
- Exit code `0` on successful navigation; non-zero if Playwright cannot launch, cookies JSON is empty, or `page.goto` errors.

### Example — drive Slack web as the user

```bash
browserclaw cookies inject \
  --cookies /tmp/slack-cookies.json \
  --goto https://app.slack.com/client \
  --browser-channel chrome \
  --wait-after-load 5 \
  --print-text 800 \
  --screenshot /tmp/slack-home.png
```

### Example — headless evidence capture

```bash
browserclaw cookies inject \
  --cookies /tmp/slack-cookies.json \
  --goto https://app.slack.com/client \
  --browser-channel chromium \
  --headless \
  --wait-after-load 3 \
  --screenshot ./evidence/slack-after-login.png
```

### Edge cases / failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `No cookies found in <path>` | JSON is empty or has no `cookies` key | Re-run `cookies decrypt` and confirm the file has `{"cookies": [...]}` |
| Navigation lands on login page despite valid cookies | Domain mismatch — `--goto` is on a domain that does not match the cookie's `host_key` | Use a URL whose host matches at least one cookie domain |
| Navigation lands on login/2FA page despite valid cookies AND correct domain | **Browser fingerprinting** — site rejects Playwright-launched Chrome even with valid session cookies (LinkedIn, Twitter/X, Threads, Facebook, Dev.to observed 2026-07-05). The cookies are accepted by the HTTP layer but the site's JS anti-bot detects the Playwright Chrome fingerprint and redirects. `browserclaw cookies inject` is NOT a universal login bypass — it only works on sites that don't fingerprint-auth the session. | (1) Check if the site works in a normal Chrome tab with the same cookies (yes → fingerprint issue). (2) Try `--browser-channel chromium` instead of `chrome` (different fingerprint, sometimes passes). (3) For sites that always reject Playwright, use `aside repl` instead — Aside's persistent daemon has a real Chrome fingerprint and may pass. (4) If all fail, the user must log in manually in the target browser first, then re-decrypt. |
| `BrowserType.launch: Executable doesn't exist` | Playwright browsers not installed | `python -m playwright install chrome` (or `chromium`) |
| Page is blank | SPA not yet hydrated when `--wait-after-load` expired | Increase `--wait-after-load` to `8`–`15` for SPAs |
| Session expires within seconds | Cookie `expires` is in the past or the site re-validates the session on every navigation | Re-decrypt (`cookies decrypt`); some sites rotate session tokens on page load |

## Security implications (READ BEFORE USING)

Cookie decryption is **sensitive**. The keychain password unlocks every cookie Chrome has stored for the user — Slack `d` tokens, GitHub `user_session`, Google `SID`, banking sessions, etc. Operators MUST:

1. **Treat decrypted cookies like raw passwords.** Do not log full cookie values to Slack, GitHub PR comments, gist attachments, or any external surface. Prefer `--summary` when sharing evidence.
2. **Never commit the output JSON.** Add `cookies.json` and `*-cookies.json` to `.gitignore` immediately. Delete after use with `shred -u cookies.json` if the disk is encrypted, otherwise `rm` is sufficient on APFS.
3. **Run in a private context.** If you invoke this from an AO worker, treat the worker session as if it has root-level access to the user's identity. Do not dispatch this skill into shared / multi-tenant AO lanes.
4. **Respect the trust model.** This skill reads only the *current user's own* Chrome profile, using *that user's* macOS Keychain. It does not (and cannot) read another user's cookies without their Keychain password. Do not extend it to do so.
5. **No bypass claims.** This skill does not bypass 2FA, CAPTCHA, or anti-bot systems. It reuses an existing logged-in session. Do not advertise it as a "login bypass."
6. **Audit logging.** Every invocation should appear in the agent's session log. If you are dispatching this via AO, include `--summary` output in the worker report and never the raw cookie values.

## Trust model diagram

```text
┌──────────────┐    security find-generic-password   ┌──────────────────┐
│  user        │ ─────────────────────────────────▶ │  macOS Keychain   │
│  (you)       │ ◀─────── "Chrome Safe Storage" ─── │  Login keychain   │
└──────┬───────┘                                      └──────────────────┘
       │ grants access once per session
       ▼
┌──────────────┐    PBKDF2-HMAC-SHA1 (1003 iters)   ┌──────────────────┐
│ browserclaw  │ ─────────────────────────────────▶ │  AES-128-CBC key  │
│ cookies.py   │                                      └────────┬─────────┘
└──────┬───────┘                                               │
       │ reads Cookies SQLite (copy to tmp)                   │
       ▼                                                       ▼
┌──────────────┐   v10 || AES(plaintext)                  ┌──────────────┐
│   cookies    │ ──────decrypt──────────────────────────▶ │  JSON output │
│   .json      │                                          │  (Playwright) │
└──────────────┘                                          └──────────────┘
```

## Test script

A bash regression test lives at `tests/test_browserclaw_skill.sh` (this repo). It verifies:

1. This SKILL.md exists and is non-empty.
2. `browserclaw cookies decrypt` is documented with a real example.
3. `browserclaw cookies inject` is documented with a real example.
4. The security warning section is present.
5. The installed `browserclaw` CLI exposes the `cookies` subcommand (real binary surface, not just docs).
6. An `--help` invocation of `cookies decrypt` returns exit code 0.

Run it from this repo:

```bash
bash tests/test_browserclaw_skill.sh
```

## Eval criteria — "working" looks like

- `browserclaw cookies decrypt --db <path> --output /tmp/c.json --domain-filter '%slack.com%'` exits 0 and writes a JSON with `>=1` cookie for an actively-used Slack profile.
- `browserclaw cookies inject --cookies /tmp/c.json --goto https://app.slack.com/client --browser-channel chromium --headless --wait-after-load 5 --screenshot /tmp/proof.png` exits 0, writes a non-zero PNG, and prints a non-empty `--print-text` if requested.
- End-to-end (decrypt → inject → screenshot) is captured as evidence for PR /es layer-2 verification on PR [#6](https://github.com/jleechanorg/browserclaw/pull/6).

## Cross-references

- Source repo: [github.com/jleechanorg/browserclaw](https://github.com/jleechanorg/browserclaw)
- PR introducing the feature: [#6 — feat(cookies): Chrome cookie decrypt + Playwright inject for reuse of logged-in sessions](https://github.com/jleechanorg/browserclaw/pull/6)
- Module source: `src/browserclaw/cookies.py` (dataclasses, AES decrypt, Keychain lookup, JSON I/O)
- CLI source: `src/browserclaw/cli.py` (argparse for `cookies decrypt` / `cookies inject`)
- Tests (10 cases, all green on macOS): `tests/test_cookies_decrypt.py`
- Reference Chromium source: `os_crypt_mac.mm` (PBKDF2 params, AES key derivation)
- Inspiration: [pycookiecheat](https://github.com/n8henrie/pycookiecheat) (MIT) — adapted for Python 3.11+ and DB v24+ SHA256(host) prefix.
- Related Hermes skills: `~/.claude/skills/browser-testing` (Playwright MCP for localhost UI testing, headless) — use this skill for **session-less** UI testing, not for "act as user X" flows.

## Version / metadata

- Last updated: 2026-06-18
- browserclaw version: 0.1.0 (cookies added in commit `9320bc0` on branch `feat/cookie-decrypt-inject`)
- Tracking PR: [#6](https://github.com/jleechanorg/browserclaw/pull/6)
- Hermes skill location: `skills/browserclaw/SKILL.md` (this file); also mirrored at `~/.claude/skills/browserclaw/SKILL.md`
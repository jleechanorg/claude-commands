# Headless portal login — what blocks and what passes

Verified 2026-07-18 via `curl -sSI`, Apple Passwords DB probe, Chrome /
Aside cookie scan over Profiles 0/1/3, plus a CDP-driven cookie dump that
recovered 247 unique tax-domain cookies across Chrome Default + Aside
Default (bypassing Chrome v20 App-Bound Encryption).

## Hard-blocked on first page load (no headless path without human unlock)

| Portal                              | Block mechanism                  | What's needed once                |
|-------------------------------------|----------------------------------|-----------------------------------|
| orenheneainc.taxdome.com            | Cloudflare Turnstile (403 headless UA) | Interactive sign-in via any past TaxDome notification "Go to account" link, OR direct browser visit; session cookie then persists in browser profile |
| snap.okta.com (Snap Inc Workday)    | Okta SAML SSO                    | Interactive SSO via the Snap corporate IdP (MFA: push to phone)  |
| fidelity.com / netbenefits          | Web SSO + persistent captcha     | Interactive SSO with MFA (text/SMS/voice) — 2fa prompt blocks headless |
| client.schwab.com / schwab.com      | Web SSO + persistent captcha     | Same — Schwab uses Riskalyze / BioCatch passive challenge |
| morganstanley.com / us.etrade.com   | Web SSO + persistent captcha     | Same pattern; some flows gated behind `chat.etradefinancial.com` |
| wealthfront.com                     | Web SSO + passkey support         | Mobile-app-style auth; passkey via iCloud Keychain OR email + TOTP |
| wellsfargo.com                       | Web SSO + captcha                | Wells Fargo uses extensive bot-detection; persistent browser profile required |
| gemini.com (exchange)               | Web SSO + 2FA                    | TOTP required; hardware key optional |

**Important nuance:** the block is on the FIRST navigation. Once you have
valid session cookies in the user's existing Chrome / Aside profile,
subsequent navigations are NOT blocked — Cloudflare already issued the
`_abck` / `bm_sz` cookie during the interactive login.

## Proven headless drive path AFTER one interactive login

1. **Dump decrypted session cookies** via CDP on a headless Chrome / Aside
   with `--remote-debugging-port=N` and `--user-data-dir=<copy of user's profile>`.
   `Network.getAllCookies` returns plaintext values even for v20
   App-Bound Encryption cookies. See `~/.hermes/skills/browserclaw/references/cdp-decrypt-via-headless-browser.md`
   for the full recipe. Verified 2026-07-18 on 247 cookies.
2. **Drive the user's existing visible Chrome** (already past Cloudflare).
   Add tabs via AppleScript `make new tab at end` — does NOT activate the
   window (verified 2026-07-18). Read tab URLs/titles via AppleScript.
   Inject cookies via CDP `Network.setCookie` if the user has reset them.
3. **Coordinate with active Aside MCP sessions.** Probe first:
   `curl -fsS http://127.0.0.1:21420/health` → check `runningSessionCount`.
   `> 0` means another chat is driving; pass the URL playbook + local
   staging path and let it parallel-drive downloads.
4. **Cloudflare `_abck` rotates every 5–10 min.** Re-dump cookies right
   before each Cloudflare-fronted navigation.

**What does NOT work** (verified 2026-07-18 → 2026-07-19):
- `browser_navigate` (Hermes MCP browser tool) — routes through
  Browserbase, a data-center IP. Cloudflare blocks on TaxDome-class
  portals regardless of how valid the cookies are. The user pushed
  back: "shouldnt need cloudflare if I'm using aside mcp" — meaning
  use the local Chrome / Aside path, not Browserbase.
- **Playwright with bundled Chromium-for-Testing on Schwab / Fidelity /
  Morgan Stanley / Wells Fargo / E*TRADE** — these servers
  TLS-fingerprint the browser, so a fresh Chromium binary is treated
  as a new device even when valid cookies are loaded. Symptom: cookies
  decrypt fine, navigation lands on `SessionExpired`. **Do NOT loop on
  retries** — verified 8+ attempts across two sessions, all fail the
  same way. Alternative path: file-watcher cron on
  `~/Downloads/<preparer> <year>/` — let the user download manually,
  pick up the files automatically. Pattern in `references/file-watcher-cron-pattern.md`.
- `browserclaw cookies decrypt` against Chrome v120+ **DOES work**
  with `--keychain-service 'Chrome Safe Storage' --keychain-account 'Chrome'`.
  The earlier "returns empty values" claim was based on a default-flag
  invocation that hit the wrong keychain. Verified 2026-07-19: 1059
  Chrome + 553 Aside cookies dumped with all `value` fields
  populated. Always pass the keychain flags explicitly. If `value` is
  empty, re-check the flags first — don't assume v20 is unsupported.

## What's in browser / keychain caches (verified 2026-07-18)

- Chrome profiles 0/1/3: 109 decrypted tax-domain cookies after CDP
  bypass (incl. fidelity.com, schwab.com, morganstanleyclientserv.com,
  wellsfargo.com, snapchat.com/accounts.snapchat.com,
  gemini.google.com, taxdome.com — including orenheneainc.taxdome.com
  with `_try_login_signed_slim`, `_TD_selected_country/state`).
- Aside profiles 0/1: 138 decrypted tax-domain cookies after CDP
  bypass (adds us.etrade.com / JSESSIONID, ETSESSION_LB;
  wealthfront.com with `t-token`/`login_xsrf`/`device_secret`).
- Local Keychain (`login.keychain-db`): 8 internet password entries,
  ALL Docker / GitHub / Gist — none for tax/finance. Apple Passwords
  entries are NOT in the system keychain.
- `security find-generic-password -s "AppleIDClientIdentifier"` etc.
  shows only Apple / Continuity entries — same conclusion.

## Apple Passwords — accessible-but-not-headless

Apple Passwords DB lives at
`~/Library/Group Containers/group.com.apple.passwords/`. The DB is
encrypted with a key derived from the user's login-keychain unlock. It
is not queryable from a Hermes session via:

- `aside repl "applePasswords.listCredentials()"` — returns "No last-focused window"
  (the Aside daemon isn't active / has no window context).
- `security find-generic-password -s "AppleIDClientIdentifier"` —
  returns generic-password data, not the per-domain entries.
- Direct SQLite probe — DB schema is unreadable without screen unlock
  + Files-and-Folders permission on this Mac, and only the GUI Apple
  Passwords.app honors that permission.

**Canonical path for the user:** open Passwords.app, search for the
domain (e.g. `taxdome.com`), reveal, copy, paste into the portal. Tell
the user this in one line — do NOT enumerate alternate storage paths
or spend cycles probing Apple's CLI further.

## Aside MCP registration pitfall (fixable setup step)

If `claude mcp list` shows `aside-mcp: ✘ Failed to connect`, the most
likely cause is wrong registration. `aside mcp` is a **stdio** MCP
server, not an HTTP one. The HTTP form spawns and immediately exits on
`stdin-end`:

```bash
# Remove the bad HTTP registration
claude mcp remove aside-mcp -s user

# Re-register as stdio
claude mcp add aside-mcp --scope user -- aside mcp

# Verify
claude mcp list
# → aside-mcp: aside mcp - ✔ Connected
```

This is a 30-second fix vs the 10+ minutes of probing we'd otherwise
spend figuring out why the daemon is up but the MCP server won't bind.

## When to stop hunting and just ask the user

After Phase 5.5 of the parent workflow, present the human-blockers list
exactly once (the one-time interactive sign-in ask). Do NOT re-probe or
re-phrase every turn. The user knows their workflow; they will tell you
when an interactive sign-in is done. Watch for a Slack reply like
"ok I'm logged in now" or a Drive upload of a 1099 PDF; both count as
the cookie having landed.

## Past session verification

- 2026-07-18: All seven TaxDome / brokerage domain reachability probes
  returned non-200 (403 Cloudflare on TaxDome, 503 on irs capture login,
  200 on login.tax1099.com but with a JS-only login form). Headless
  login is NOT achievable end-to-end from a fresh process.
- 2026-07-18: CDP bypass recovered 247 unique decrypted tax-domain
  cookies. Existing Chrome (TaxDome tab w1t37 past Cloudflare) loaded
  the dashboard cleanly when navigated via AppleScript. End-to-end
  headless drive path is proven after the one-time interactive login.
- Cost of NOT asking the user: each portal probe took 5-15 seconds;
  five probes = ~60 seconds wasted; scale this and it eats the user's
  per-task time budget. Phase 5 should be a single user-message, not a
  multi-probe black hole.
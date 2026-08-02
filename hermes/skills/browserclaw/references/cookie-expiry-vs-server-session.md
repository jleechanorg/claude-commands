# Cookie expiry ≠ server-side session validity — the silent-fail mode

**Class of problem:** `browserclaw cookies decrypt` returns N>0 cookies with valid `expires` dates extending through 2027, but `cookies inject` against the broker / vendor portal still 302-redirects to the login page. The cookies are technically valid (Chrome will happily send them on every request). The **server-side session** that the cookies authenticate is gone.

This is the #1 cause of "I have all the cookies but I can't get in" and it is invisible if you only check `--summary` output (which prints expiry but not session validity).

## Verified symptom (2026-07-22, 5-broker probe)

Sweep returned valid-looking cookies for all five brokers. Actual injection behavior:

| Service | Cookie record status (expiry) | `cookies inject` result |
|---|---|---|
| `client.schwab.com/app/accounts/summary/` | `np2 exp=1818981233 (2027-08-22)` valid | HTTP 200, redirected to `Areas/Access/Login?SessionTimeOut=y` |
| `digital.fidelity.com/ftgw/digital/portfolio/summary` | `mbox exp=2027-08-23` valid | HTTP 200, redirected to `/prgw/digital/signin/retail` |
| `www.wealthfront.com/dashboard` | `rl_user_id exp=2027-07-19` valid | HTTP 200, redirected to `/login?redirect=...` |
| `mso.morganstanleyclientserv.com/` | `MSWM_LOGIN exp=2027-07-19` valid | `TimeoutError` (likely Akamai / bot-detect on headless UA) |
| `exchange.gemini.com/` | No auth cookies (Gemini's trading portal uses different cookie domain) | HTTP 200, redirected to `/signin?redirect=...` |

The 302 destination is the giveaway:

- **`?SessionTimeOut=y`** → server-side session timeout; need fresh interactive login (cookie wipe → user logs in again → browserclaw re-decrypts).
- **`/signin?redirect=<encoded_target>`** → server treats the user as logged-out; cookie wasn't recognized at all. Same fix.
- **`TimeoutError` (Morgan Stanley)** → Akamai bot-detection on the headless Chromium UA. Different problem; doesn't matter if cookies are valid. Reference recipe at `references/cdp-decrypt-via-headless-browser.md`.

## The tell-tale: how to confirm session-staleness WITHOUT assuming it

Don't trust the `--summary` output's `expires` field alone — it tells you Chrome believes the cookie is good, not that the server agrees. After extracting cookies, **probe one authenticated endpoint** and check the final URL:

```python
import json, urllib.request, urllib.error

with open('/tmp/<service>-cookies.json') as f:
    cookies = {c['name']: c['value'] for c in json.load(f)['cookies']}

cookie_hdr = "; ".join(f"{k}={v}" for k, v in cookies.items())
test_urls = [
    "<the dashboard URL you'd normally drive>",
    "<the /api/account endpoint, if known>",
]
ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

for url in test_urls:
    req = urllib.request.Request(url, headers={"Cookie": cookie_hdr, "User-Agent": ua})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            final = r.geturl()
            print(f"OK    {url}  →  {final}")
            if final != url and any(x in final for x in ["/login", "/signin", "SessionTimeOut", "/auth", "Redirect"]):
                print(f"  ^ server-side session is DEAD — re-login required")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}  {url}  →  {e.url if hasattr(e, 'url') else 'n/a'}")
    except Exception as e:
        print(f"{type(e).__name__}  {url}  — likely Akamai/bot-detect (use CDP recipe)")
```

**Decision tree:**

1. Final URL contains `/login`, `/signin`, `?SessionTimeOut=`, or the same domain with `?redirect=...` → **cookies exist but server session is dead**. Stop pretending auth will work.
2. HTTP 403/401 on `/api/...` → **may be different problem** (CSRF header missing, or paid-tier feature gating). Check `direct-graphql-stolen-cookie-auth.md` P5 / P6 first.
3. TimeoutError or HTTPS error → **bot-detect on headless UA**. Switch to CDP-via-real-Chrome recipe (`cdp-decrypt-via-headless-browser.md`).
4. HTTP 200 with final URL matching the request URL → **actually authenticated**. Proceed.

## Recovery paths when session is dead

In order of preference:

1. **Poll-until-fresh-cookies-appear cron** — register a `hermes cron` to re-decrypt every N minutes and run the session-probe check; if it starts returning HTTP 200, the user has logged in interactively. Use the `Poll-until-cookies-appear pattern` in the main SKILL.md; **replace the "0 cookies" trigger with "302 to login" detection**.
2. **Ask the user to log in once in the target browser** — single interactive action; a brief ~60s task. Then re-decrypt and the next agent session has working auth.
3. **Vendor data through email alerts** — many services (brokerages, banks, Monarch) send email alerts that contain the same data the API would return. Use `gog gmail search` per `multi-profile-cookie-scan.md`. Degraded data, but real and live.
4. **Direct GraphQL/REST with stolen cookies** — only works if the API itself is sharded from the web session (Monarch is; Fidelity's web and trading APIs share a session token so both die together). Not a recovery path; useful only when step 1 already has fresh cookies in hand.

## Why this happened in this session

The user's `/browserclaw` invocation was followed by "all 4 brokers blocked" claims with reasoning that "the cookies are stale / no cookies exist / server-side tokens expired." The reasoning conflated **three different things**: not-in-keyring (no cookies at all), cookie record expired by Chrome (wiped by browser), and **cookie record valid in Chrome but server-side session gone (the silent mode)**.

The right test for the third case is an **actual login-page redirect probe**, not a cookie DB expiry scan. Three of four brokers in the table above had cookies extending to 2027 and were still login-redirected.

## Embed in agent workflow

Whenever `cookies inject` lands on a login page despite `--summary` showing valid cookie expiry:

- **Do NOT** post "no cookies exist" or "need re-login" as the conclusion.
- **DO** run the probe above to confirm server-side session death.
- **DO** register a poll cron (per `Poll-until-cookies-appear pattern`) that re-decrypts + re-probes every N minutes; the user can log in at their leisure.
- **DO** document the exact 302 destination in the cron prompt so the recovery path can be verified end-to-end without the user's help.

## Cross-references

- Main SKILL.md "Poll-until-cookies-appear pattern" — extend the trigger condition from "0 cookies" to also fire on "302 to login / SessionTimeOut=y".
- Main SKILL.md "When to use cookies decrypt + inject" — clarify that valid cookie record ≠ valid server session.
- `references/direct-graphql-stolen-cookie-auth.md` — only useful AFTER session is restored; if server session is dead, no GraphQL auth either.
- `references/cdp-decrypt-via-headless-browser.md` — different problem (Chrome v20 ABE decrypt); use when cookies decrypt to empty values, not when they decrypt fine but login 302's.
- `references/gmail-as-fallback-when-sso-clickthrough-blocked.md` — degraded-data fallback when even fresh auth can't be obtained.

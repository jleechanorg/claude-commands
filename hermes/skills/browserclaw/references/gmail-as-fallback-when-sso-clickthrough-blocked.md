# Gmail-as-fallback — when vendor SSO needs interactive click-through

**Problem class:** vendor site (Monarch, Plaid-gated bank, Notion, similar) shows a "Continue with Google" / "Sign in with SSO" button on the login page but, after `browserclaw cookies inject` lands there, does NOT auto-redirect as the logged-in user. Instead it shows the SSO button + empty email/password fields. Headless Chromium can't drive the Google consent flow without a real account-picker gesture.

**Verified 2026-07-22 (Monarch Money net-worth diagnosis):** `cookies decrypt` against Chrome Default yielded 83 valid `*.google.com` cookies (`__Host-3PLSID`, `__Secure-OSID`, `NID`, `SID`, `COMPASS` for mail/chat/calendar). `cookies inject` against `https://app.monarch.com/login?route=%2F` returned the login page with empty fields. `cookies inject` against `https://mail.google.com/mail/u/0/…` returned the user's actual inbox with no login prompt. Both runs used the same `cookies.json`.

**Recovery recipe — Gmail alert scraping** (works for every vendor that emails the user account activity):

```bash
# 1. Reuse the same cookies.json that failed against the vendor
GSCOOKIES=/tmp/j-monarch-google-cookies.json

# 2. Pull vendor alert emails via Gmail search operands
browserclaw cookies inject \
  --cookies "$GSCOOKIES" \
  --goto "https://mail.google.com/mail/u/0/#search/from%3A%22${VENDOR_DOMAIN}%22+after%3A${YYYY}%2F${MM}%2F${DD}" \
  --browser-channel chromium --headless \
  --wait-after-load 14 \
  --print-text 25000

# 3. For specific event types, drill down with subject/from operators
browserclaw cookies inject \
  --cookies "$GSCOOKIES" \
  --goto "https://mail.google.com/mail/u/0/#search/from%3A%22${VENDOR_DOMAIN}%22+subject%3A%22budget%22+newer_than%3A90d" \
  --browser-channel chromium --headless \
  --wait-after-load 14 \
  --print-text 20000

# 4. URL-encode the query properly: spaces → %20, parens → %28%29, colons → %3A
# Use + (not %20) inside the hash fragment — Gmail's in-page search engine
# treats + as the AND operator and that is faster than %20.
```

**Why this works at all:** Gmail is the same Google SSO issuer as any "Continue with Google" button, BUT Gmail's own session token validates directly via the authDomain cookie path (no third-party-button redirect required). Other vendor sites use a Firebase-style OAuth flow that needs a click-through popup. The cookies are valid in both cases — the difference is whether the destination site auto-redirects on first load.

**Diagnostic tree when vendor SSO fails:**
1. **Same cookies → Gmail works?** Yes → use Gmail-as-fallback (this file).
2. **Same cookies → Gmail works, vendor does NOT?** Yes → vendor needs interactive click-through OR has bot-detection on the SSO path. Fallback path is Gmail + phone-app vendor check.
3. **Same cookies → Gmail ALSO fails?** Cookies have expired / were rotated. Re-decrypt with fresh DB copy (close Chrome first if needed).

**Structured data you typically get from Gmail alert emails:**
- Budget overrun alerts: `You've exceeded your <Category> budget this month by $X` — gives you the overrun amount WITHOUT needing live API access.
- Transaction notifications: `New expense from <merchant> for $X on <account>` — gives you merchant + amount + funding account.
- Sync/access state: `Access Expired`, `We found N new recurring merchants`, `Your balance is $X due <date>` — gives you account-health signals.
- Recurring charges: `New recurring merchant found … $X monthly` — gives you subscription fatigue.

**Example analysis the user got without ever needing live Monarch:**
| Email source | What it revealed |
|---|---|
| `from:monarch subject:budget after:2026/06/30` | Capital One access expired Jul 3 → likely source of "stale Chase …0002" symptom in Monarch chart |
| `from:monarch "Medical budget"` | Sustained $24–29K monthly overruns (Apr 2026 $28,387 → May $26,083 → Jun $23,652 → Jul) |
| `from:monarch "Education budget"` after 2026/06/30 | $29,160 overrun on Jul 15 — biggest single swing-factor right now |
| `from:monarch "Wells Fargo"` | Mortgage $13,457 paid Jul 15 → confirms mortgage is still on full rate |
| `from:monarch "new recurring"` | Primo Brands Monthly, Captions.ai Monthly, Annual Membership Fee Yearly — subscription audit |

**Companion file:** `references/multi-profile-cookie-scan.md` § "Gmail-as-data-fallback" — covers the case where there are NO cookies; this file covers the case where the cookies work for Gmail but not for the target vendor.

**Anti-pattern:** do NOT propose a `clarify` 4-option menu ("paste the email contents / re-share the doc / try a different login / give up"). Run the recipe; it takes ~5 seconds of `browserclaw` time per query. Posting a menu without first trying the recipe was the failure mode Jeffrey corrected for share links on 2026-07-20 (see `references/gemini-share-link-stopping-pattern.md`) — same pattern, different domain.

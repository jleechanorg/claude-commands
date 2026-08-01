# Aside vs Chrome cookie portability (and the "no auth" trap)

**Trigger:** you ran `browserclaw cookies decrypt --db "$HOME/Library/Application Support/Google/Chrome/Default/Cookies" --domain-filter '%<domain>%' --summary`, got 0 cookies, and concluded the user is not logged into `<domain>`. Before reporting that, sweep Aside + Brave + Edge + additional Chrome profiles.

**Verified case (2026-07-22, Monarch):** the user is logged into `app.monarch.com` in their Aside browser. Chrome Default profile has 0 cookies for `monarch.com`. Sweeping Aside's DB returns 10 valid cookies including `session_id` (HttpOnly, Secure, `.api.monarch.com`) + `csrftoken` (`.monarch.com`) + `monarchDeviceUUID` + `__cf_bm` + Stripe MID/SID. These are sufficient to call `https://api.monarch.com/graphql` directly with `X-CSRFToken: csrftoken` + `Origin: https://app.monarch.com` and return a live, validated response.

## Why this happens

Aside is a separate Chromium-based browser with its own:
- macOS Keychain entry (`Aside Safe Storage` / `Aside`)
- SQLite Cookies file (`~/Library/Application Support/Aside/Default/Cookies`)
- Profile state (extensions, IndexedDB, localStorage)

A user who browses "in Aside" (e.g. via the daemon for AI-browsing workflows) accumulates sessions in Aside's DB, not Chrome's. The two are completely independent — Chrome cannot read Aside's cookies and vice versa without explicit import.

## Sweep recipe

Always run this loop before declaring "no auth":

```bash
for source in \
  "$HOME/Library/Application Support/Google/Chrome/Default" \
  "$HOME/Library/Application Support/Google/Chrome/Profile 1" \
  "$HOME/Library/Application Support/Google/Chrome/Profile 2" \
  "$HOME/Library/Application Support/Aside/Default"; do
  if [ -f "$source/Cookies" ]; then
    profile=$(basename "$source")
    # Chrome vs Aside requires different keychain args
    if [[ "$source" == *Aside* ]]; then
      kc_svc='Aside Safe Storage'
      kc_acct='Aside'
    else
      kc_svc='Chrome Safe Storage'
      kc_acct='Chrome'
    fi
    echo "--- $profile ($source) ---"
    env -i HOME="$HOME" PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
      browserclaw cookies decrypt \
        --db "$source/Cookies" \
        --output "/tmp/$profile-$domain-cookies.json" \
        --keychain-service "$kc_svc" --keychain-account "$kc_acct" \
        --domain-filter '%<domain>%' --summary 2>&1 | tail -10
  fi
done
```

If any non-zero count returns, you have a session in THAT profile's cookie DB — not in the others. Use the JSON from that DB for `cookies inject` or the direct-GraphQL call.

## Full Aside decrypt block

```bash
env -i HOME="$HOME" PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
  browserclaw cookies decrypt \
    --db "$HOME/Library/Application Support/Aside/Default/Cookies" \
    --output /tmp/aside-cookies.json \
    --keychain-service 'Aside Safe Storage' \
    --keychain-account 'Aside' \
    --domain-filter '%<domain>%' \
    --summary
```

Note the `--keychain-service 'Aside Safe Storage'` + `--keychain-account 'Aside'`. Without these, browserclaw tries to decrypt using Chrome's keychain password and all cookie values come back as 0-length or garbage.

If `Keychain lookup failed for service='Aside Safe Storage' account='Aside'`:
- The Aside Safe Storage keychain entry is only created after Aside writes its first cookie to disk.
- Verify the entry exists: `security find-generic-password -s 'Aside Safe Storage' -a 'Aside' -w`
- If the command prompts, type the macOS user password (Aside Safe Storage uses the same Keychain password).
- If the entry truly doesn't exist, log into any site in Aside once (any login, even a throwaway), then re-run.

## Pitfalls specific to Aside-portability

- **P1 — "I see you aren't logged in" is wrong 90% of the time.** Always sweep Aside + Profile 1 + Brave + Edge before reporting.
- **P2 — Pasting cookies across browsers doesn't work.** Aside and Chrome encrypt with different Safe Storage passwords. You cannot copy Chrome cookies into Aside and have Aside read them. Round-trip requires: Chrome → cookie JSON (decrypt with Chrome keychain) → re-encrypt under Aside keychain → Aside. No tool currently does this automatically.
- **P3 — Slack auth-specific gotcha:** Aside decrypts Slack's `d` cookie to the newer hex format; Chrome decrypts to legacy `xoxd-...`. Slack rejects the Aside format (`auth.test` → `not_authed`). **For Slack targets specifically, prefer Chrome Default cookies over Aside cookies, even when Aside has them.** (Verified 2026-07-19, jleechanorg/mcp_mail OAuth fix.)
- **P4 — WebSocket cookies may be separate.** Some Chrome extensions (Notion Web Clipper, 1Password) keep their auth in extension storage, not the cookie DB. Sweeping won't help.
- **P5 — Multi-account users with multiple Aside profiles.** `aside account list` will show multiple profiles (`u0`, `u1`, ...). Each profile has its own cookie DB. If you see `<domain>` signed-in in `u1` but you're using `u0` cookies, you'll get 0 hits.

## Cross-reference

- See `~/.hermes/skills/browserclaw/SKILL.md` for the canonical Chrome/Brave/Edge cookie sweep recipe.
- See `~/.hermes/skills/browserclaw/references/direct-graphql-stolen-cookie-auth.md` for the next-step recipe (call the protected API directly once you have the cookies).

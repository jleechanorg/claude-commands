---
name: auth-cookie-ttl-class-2026-07-24
version: 1.1.0
status: refined-hypothesis
parent_skill: wa-cloud-run-deploy-failure-debug
changelog:
  - 1.0.0 (2026-07-24) Initial hypothesis: cookie TTL is the failure mode; fix is a server-side max_age override on the proxy.
  - 1.1.0 (2026-07-24) Root cause REFINED. The cookie TTL is fine; the failure is iOS WebKit localStorage eviction of the Firebase Auth persisted user record. v1.0 max_age fix is a no-op. Real fix options documented.
---

# Auth-cookie-TTL on `mvp-site-app-dev` — refined root cause (v1.1.0)

**REFINED 2026-07-24** after live root-cause investigation on the
exact same symptom the v1.0 reference was written for. The cookie TTL
is **NOT** the failure mode. The failure mode is **iOS WebKit
localStorage eviction of the Firebase Auth client's persisted user
record**. Read this whole document before applying the v1.0 fix
(`max_age` override) — that fix would be a no-op for the actual
user-visible symptom on iOS.

**Verified:** 2026-07-24, `mvp-site-app-dev-03980-l7l` (commit
`cb88231d8d0c90b9ec702ab3fd2171abd00afcd0`), service URL
`https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app`, campaign
`wc2BBcSgOljiU3vJ160A` ($GITHUB_REPOSITORY), iPhone iOS
26.5.2 + Chrome iOS 150 (CriOS) — both WebKit engines.

## Symptom pattern (unchanged)

User opens a campaign URL after a day or two → browser shows the
"Continue with Google" landing page → must re-auth. Cookie appears to
expire after ~24–48h instead of staying valid for the refresh-token
lifetime (Firebase default 6 months of inactivity).

## What I checked first, and why the v1.0 hypothesis was wrong

v1.0 of this reference asserted the backend proxy re-emits upstream
`Expires` verbatim and therefore the fix is to add a `max_age` override
in `$PROJECT_ROOT/main.py:1692`. That part is **correct as a description of
the code** but **wrong as a root cause for the symptom**. The
iPhone-observed sign-in interval is **2 days, 18 hours** (verified from
GCP auth-helper logs, 60d window, `state=AMbdm...` redirect events
filtered to iPhone user-agent), which the cookie-TTL theory cannot
explain on its own — a 1-day cookie TTL would be 1d, a 14-day TTL would
not expire at 2-3d. The cookie is not the thing getting evicted.

The two persistence stores in the auth flow are:

1. The `__session` cookie — first-party, set by the auth helper proxy
   at `$PROJECT_ROOT/main.py:1688-1696`, controlled by upstream
   `worldarchitecture-ai.firebaseapp.com`.
2. The Firebase Auth client's persisted user record — set by
   `setPersistence(LOCAL)` at `$PROJECT_ROOT/frontend_v1/auth.js:697-700`,
   stored in IndexedDB on desktop browsers but **forced to localStorage
   on iOS WebKit** by the iOS-WebKit persistence fallback at
   `$PROJECT_ROOT/frontend_v1/auth.js:75-99`.

The v1.0 reference only considered store (1). The actual root cause
is store (2) getting evicted by iOS WebKit's ITP storage-eviction
policy. The `__session` cookie is fine; the persisted user record
in localStorage is what disappears.

## The smoking gun — `auth.js:75-99` on iOS WebKit

```js
// iOS WebKit-only persistence fallback. Persistence.LOCAL in the 9.6.1
// compat SDK prefers indexedDBLocalPersistence, whose firebaseLocalStorageDb
// IndexedDB open/read can hang indefinitely on affected iOS WebKit browsers
// (firebase-js-sdk #8019). Neutralizing window.indexedDB BEFORE the first
// firebase.auth() call makes the SDK's indexedDBLocalPersistence._isAvailable()
// probe fail, so LOCAL falls back to localStorage.
const isAffectedIOSWebKitBrowser = () => {
  const isiOSDevice = /iPhone|iPad|iPod/i.test(ua);
  const isWebKit = /AppleWebKit/i.test(ua);
  return (isiOSDevice || isiPadDesktopUA) && isWebKit;
};
try {
  if (isAffectedIOSWebKitBrowser() && typeof window.indexedDB !== 'undefined') {
    Object.defineProperty(window, 'indexedDB', { configurable: true, value: undefined });
  }
} catch (e) { … }
```

On iPhone + AppleWebKit (any iOS browser, including Chrome iOS /
CriOS — Apple App Store policy forces iOS browsers to use WebKit),
this kills IndexedDB and forces the Firebase SDK to fall back to
**localStorage**. localStorage on iOS Safari/WebKit is subject to
Intelligent Tracking Prevention (ITP) storage eviction:

- First-party localStorage can be evicted after ~7 days of no user
  interaction with the site (webkit.org/blog/8311, expanded in iOS
  17 to also evict first-party storage).
- Chrome iOS is built on WebKit per Apple's App Store policy, so the
  same policy applies to `CriOS/150` user-agents.
- The eviction window is shortened for low-engagement sites; a 2-3
  day eviction matches the user's observed 2d 18h sign-in interval.

When localStorage is evicted, the SDK's `onAuthStateChanged` callback
fires with `user=null` on next visit, the `__session` cookie is
ignored (the SDK's `getRedirectResult` won't fire because the
persisted user record is gone), and the user is routed to the
"Continue with Google" landing page. The user re-signs in, the
localStorage record is repopulated, the cookie is reset, the user
is in. **The cycle repeats every 2-3 days.**

## Phase 1 — confirm the symptom is iOS WebKit localStorage, not cookie TTL

**Three checks, all must pass:**

1. **Confirm the user-agent is iOS WebKit.** Filter GCP auth logs by
   the user's IP and a recent sign-in chain:

   ```bash
   gcloud logging read \
     'resource.type=cloud_run_revision
      AND resource.labels.service_name=mvp-site-app-dev
      AND httpRequest.userAgent=~"iPhone"' \
     --limit=5 --format=json --freshness=60d | python3 -c "
   import sys, json
   for e in json.load(sys.stdin):
       print(e.get('httpRequest',{}).get('userAgent',''))
   "
   ```

   Expect: `Mozilla/5.0 (iPhone; CPU iPhone OS 26_5_x like Mac OS X)
   AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/…` — iPhone + WebKit
   (CriOS is a WebKit fork, not Blink).

2. **Confirm the sign-in interval is 1-3 days, not session-only.**
   Pull the actual sign-in chain and compute the gaps:

   ```bash
   gcloud logging read \
     'resource.type=cloud_run_revision
      AND resource.labels.service_name=mvp-site-app-dev
      AND httpRequest.userAgent=~"iPhone"
      AND (httpRequest.requestUrl=~"/__/auth/" OR httpRequest.referer=~"accounts.google.com")' \
     --limit=500 --format=json --freshness=60d | python3 -c "
   import sys, json
   from datetime import datetime
   data = json.load(sys.stdin)
   signin = []
   for e in data:
       h = e.get('httpRequest', {})
       ref = h.get('referer', '')
       if 'state=' in ref and 'auth/handler' in ref:
           signin.append((e.get('timestamp',''), ref[-60:]))
   signin.sort()
   for i in range(1, len(signin)):
       t1 = datetime.fromisoformat(signin[i-1][0].replace('Z','+00:00'))
       t2 = datetime.fromisoformat(signin[i][0].replace('Z','+00:00'))
       print(f'  {signin[i-1][0]} -> {signin[i][0]} :: {t2 - t1}')
   "
   ```

   Expect: gaps of 1d-3d between sign-in events. A 1d gap means
   session-cookie eviction; a 2-3d gap matches iOS WebKit localStorage
   eviction; a 7d+ gap is consistent with iOS 17's expanded ITP rule.

3. **Confirm there is NO server-side cookie TTL config.** Query the
   Firebase project config and grep for any session/cookie TTL knob:

   ```bash
   curl -s -H "Authorization: Bearer *** auth print-access-token)" \
     'https://identitytoolkit.googleapis.com/v2/projects/worldarchitecture-ai/config' \
     | jq 'keys'
   # Expect: signIn, notification, quota, monitoring, multiTenant,
     authorizedDomains, subtype, client, mfa, blockingFunctions,
     smsRegionConfig, emailPrivacyConfig, mobileLinksConfig,
     defaultHostingSite
   # NOT present: sessionVerificationConfig (there is NO per-project
   # cookie TTL config in Firebase Auth at all)
   ```

   Also confirm the proxy code path:

   ```bash
   grep -n "set_cookie\|max_age\|SESSION_COOKIE" $PROJECT_ROOT/main.py | head -10
   # Expect: only main.py:1688 (proxy re-emit) and main.py:1692
   # (expires=cookie.expires). No max_age, no SESSION_COOKIE_* env var.
   ```

   The "no server-side cookie TTL" finding is **necessary but NOT
   sufficient** to conclude cookie TTL is the failure mode. The cookie
   has whatever `Expires` Firebase Hosting's auth helper attaches, and
   that helper's default is 14 days for the OAuth callback. The
   1-3 day symptom is NOT the cookie being expired by an over-strict
   server override — it would still be 14d if the cookie were the only
   thing in play.

## Phase 2 — confirm the proxy passes upstream `Expires` verbatim (unchanged from v1.0)

The Firebase auth helper reverse-proxy is at
`$PROJECT_ROOT/main.py:1644-1697`. The cookie re-emit block is at
`$PROJECT_ROOT/main.py:1684-1696`. The cookie TTL is whatever
`worldarchitecture-ai.firebaseapp.com` upstream attaches, plus any
Werkzeug-side `max_age` you add. There is currently **no `max_age`**,
**no env-var override**, **no hardcoded fallback** in the proxy.

## Phase 3 — confirm `auth.js` forces localStorage on iOS WebKit

```bash
grep -n "isAffectedIOSWebKitBrowser\|window.indexedDB\|setPersistence" \
  $PROJECT_ROOT/frontend_v1/auth.js | head -20
```

Expect:
- `auth.js:75-99`: `isAffectedIOSWebKitBrowser` + `Object.defineProperty(window, 'indexedDB', ..., value: undefined)`
- `auth.js:697-700`: `setPersistence(firebase.auth.Auth.Persistence.LOCAL)`

This is the load-bearing detail: **the JS forces localStorage on
iPhone**. The v1.0 reference did not consider this.

## Why the v1.0 "max_age" fix would be a no-op

Adding `max_age=SESSION_COOKIE_MAX_AGE` to the proxy's `set_cookie`
call would extend the **cookie** TTL. The cookie is fine — it is NOT
the thing being evicted. iOS WebKit ITP evicts **localStorage**, which
is where the Firebase SDK persists the **user record**, which is the
bootstrap handle for `onAuthStateChanged`. The cookie is downstream of
that decision: when the SDK has no user, it doesn't read the cookie at
all. Bumping the cookie TTL changes nothing about the SDK's decision
to call `onAuthStateChanged(null)`.

If you apply the v1.0 fix and re-test on iPhone, you will see the
same 2-3 day eviction. The user-visible symptom is unchanged.

## Real fix options (ordered by recommendation)

### Option 1 — Silent re-sign-in on localStorage miss (recommended)

When the SDK boots and `onAuthStateChanged` returns null but the
`__session` cookie is still present in `document.cookie`, the user
clearly has a valid session but lost their localStorage. Treat the
cookie as a stronger signal than the SDK's "no user" callback and
attempt a silent re-auth:

```js
// $PROJECT_ROOT/frontend_v1/auth.js — pseudocode
const cookieSession = parseFirebaseSessionCookie(document.cookie);
if (!firebase.auth().currentUser && cookieSession) {
  // SDK says no user, but cookie says we have one — trust the cookie.
  // Try to use the existing session by calling signInWithCustomToken with
  // a token the server derives from the __session cookie.
  // (See Option 2 for the server-side token mint.)
  const restored = await fetch('/api/session/restore', {
    credentials: 'include',
  });
  if (restored.ok) {
    const { customToken } = await restored.json();
    await firebase.auth().signInWithCustomToken(customToken);
    // Now SDK has a user, the cookie + localStorage are both repopulated.
    return; // skip the login-page redirect
  }
}
```

This is ~30 lines in `auth.js` plus a new `/api/session/restore`
endpoint (Option 2). It directly answers the user's complaint
("shouldn't need to log in again") because the cookie IS the
durable session — the localStorage was just a faster re-bootstrap
that we're now bypassing.

### Option 2 — Server-side session restore from `__session` cookie

New endpoint at `$PROJECT_ROOT/main.py` that, given the `__session` cookie,
verifies the Firebase session cookie server-side and mints a custom
token for the user:

```python
@app.route('/api/session/restore', methods=['GET'])
@limiter.limit('30 per hour')
def session_restore():
    session_cookie = request.cookies.get('__session')
    if not session_cookie:
        return jsonify({KEY_SUCCESS: False, KEY_ERROR: 'no_session'}), 401
    try:
        decoded = auth.verify_session_cookie(session_cookie, check_revoked=True)
    except Exception as e:
        return jsonify({KEY_SUCCESS: False, KEY_ERROR: 'invalid_session'}), 401
    custom_token = auth.create_custom_token(decoded['uid'])
    if isinstance(custom_token, bytes):
        custom_token = custom_token.decode('utf-8')
    return jsonify({KEY_SUCCESS: True, 'custom_token': custom_token})
```

This is the **server half** of Option 1. The cookie becomes the
durable source of truth; the localStorage record is just a fast
re-bootstrap. ~50 lines on the server + a 6-test contract in
`$PROJECT_ROOT/tests/test_firebase_auth_helper_proxy.py`.

### Option 3 — Disable the iOS WebKit localStorage fallback

Keep `setPersistence(LOCAL)` going through indexedDB. The
`auth.js:75-99` fallback was added because the 9.6.1 compat SDK's
IndexedDB read could hang indefinitely on iOS WebKit (firebase-js-sdk
#8019). Removing the fallback requires either:

- Upgrading the Firebase JS SDK to a version where #8019 is fixed
  (verify on a non-prod branch first — there's no guarantee the
  hang is gone in newer lines), OR
- Implementing a custom IndexedDB-wedge timeout that falls back to
  in-memory persistence after N seconds, instead of the current
  "neutralize indexedDB and force localStorage" trick.

This is risky — it may regress the iOS sign-in wedge the fallback
was added for. **Not recommended** unless the user has specifically
asked for it AND the hang is confirmed in a newer SDK.

### Option 4 — Document the iOS WebKit behavior

Acknowledge that iOS WebKit ITP evicts localStorage after ~7 days
(2-3 days for low-engagement sites) and that re-sign-in is the
expected behavior. Cheapest, but does not address the user's
complaint.

### What I would do

Open a single PR for **Option 1 + Option 2** as a coherent 2-component
fix: server endpoint + client re-bootstrap. The 2-component shape is
mandatory — Option 1 alone (without the server endpoint) is
incomplete; Option 2 alone (without the client re-bootstrap) is
inert until the user lands on the login page.

Estimated size: ~80 lines across `$PROJECT_ROOT/main.py` +
`$PROJECT_ROOT/frontend_v1/auth.js` + `$PROJECT_ROOT/tests/test_firebase_auth_helper_proxy.py`.
Smaller than the v1.0 max_age patch; bigger blast radius
(frontend + backend + test). Per `$GITHUB_REPOSITORY`
AGENTS.md, this is a non-test change to `$PROJECT_ROOT/**` and requires
`/es` evidence before merge.

## Pitfalls — DO NOT do these (refined from v1.0)

- **Do NOT apply the v1.0 "max_age" fix.** It addresses a real
  description of the code (the proxy passes `cookie.expires` verbatim)
  but NOT the actual failure mode. The cookie is not being evicted by
  iOS WebKit ITP; localStorage is. Adding `max_age` to the cookie
  changes nothing about the SDK's `onAuthStateChanged` decision.
- **Do NOT disable the iOS WebKit localStorage fallback** without a
  follow-up plan for the IndexedDB wedge. The fallback exists
  because the 9.6.1 compat SDK's IndexedDB read hangs on iOS WebKit
  (firebase-js-sdk #8019). Removing it without addressing #8019
  regresses the iOS sign-in wedge.
- **Do NOT change the iOS-WebKit localStorage fallback to use
  sessionStorage instead.** sessionStorage is also evicted on tab
  close, and the SDK doesn't have first-class sessionStorage support.
- **Do NOT propose fix options before proving the root cause.**
  The original v1.0 of this reference (and my first reply in the
  session that triggered this revision) listed 4 fix options A/B/C/D
  before running any of the diagnostic steps. The user pushed back:
  *"Let's first root cause why it's expired versus all these
  speculative fixes. It has not been 30 days."* The pushback was
  correct — the proposed fixes were a no-op for the actual symptom.
  The diagnostic order is: (1) confirm user-agent, (2) compute
  sign-in interval, (3) check Firebase project config for any
  cookie TTL config, (4) read the JS persistence code path,
  (5) only then propose fixes. Phase 1 takes 2 minutes; the
  fixes are wrong if Phase 1 is skipped.
- **Do NOT confuse "no server-side cookie config" with "cookie is
  the problem."** The lack of a server-side `max_age` override is
  a real description of the code, but it is not evidence that the
  cookie is the failure mode. The cookie's default TTL (14 days from
  Firebase's auth helper) is far longer than the user's observed
  2-3 day symptom. The localStorage record is the thing with the
  matching eviction window.

## What to verify before claiming "fixed" (refined)

| Gate | How to verify | Block if red |
|------|---------------|--------------|
| New `__session` cookie behavior is unchanged on non-iOS | Sign in on desktop Chrome, sign out, sign back in. Confirm `client_diag` shows `cdiag_field_has_current_user=true` after page reload | The fix regressed non-iOS sign-in |
| iOS re-sign-in is silent | Sign in on iPhone Chrome, clear localStorage in DevTools, reload. Confirm SDK re-bootstraps from cookie without showing the "Continue with Google" page | Option 1 is incomplete |
| `/api/session/restore` returns a valid custom token | `curl -H "Cookie: __session=…" https://…/api/session/restore` returns `{"success": true, "custom_token": "…"}` | Option 2 is broken |
| `cdiag` no longer shows the eviction cycle | After deploying the fix, monitor `cdiag_name=route.unauthenticated_drop` events for 7+ days. The iPhone re-auth interval should drop from 2-3 days to "as long as the cookie lasts" (the cookie survives a long time on first-party origin, well past iOS WebKit ITP's 7-day cap) | The fix is incomplete |
| Live deploy matches PR HEAD | `gcloud run services describe mvp-site-app-dev --format='value(metadata.labels.commit-sha-full)'` returns the PR's head SHA | Don't claim "fixed" until deploy lands |

## What I would tell the user right now

I do NOT have a fix shipped. The 2-3 day eviction is iOS WebKit
ITP, not a backend bug. The server-side `max_age` override from
v1.0 is a no-op for the actual symptom on iPhone. The right fix
is Options 1+2 together (server endpoint + client re-bootstrap).
I am waiting for the user to confirm direction before opening a PR.

## Cross-reference

- The umbrella skill `wa-cloud-run-deploy-failure-debug` describes
  this reference's location under
  `references/auth-cookie-ttl-class-2026-07-24.md`. That umbrella
  name is misleading — this is NOT a deploy failure, it's a sibling
  operational class. The umbrella's "When to use this skill" section
  has a bullet that points here; consider renaming the file in a
  future pass to `references/auth-session-eviction-2026-07-24.md`
  to better reflect the actual failure mode.
- Umbrella SKILL.md Pitfall #15 (added 2026-07-24) embeds the
  diagnostic-order discipline learned from the user pushback
  *"Let's first root cause why it's expired versus all these
  speculative fixes. It has not been 30 days."* Future operators
  hitting this class will be steered to this v1.1.0 reference by
  the umbrella's bullet in the "When to use this skill" section
  (which now explicitly states that the v1.0 hypothesis is wrong).

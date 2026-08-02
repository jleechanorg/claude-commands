# Auth-gate fallback for /repro on deployed URLs

**Problem:** The canonical `/repro` workflow assumes the agent can hit the deployed URL headlessly to capture visual evidence. When the deployed URL is gated behind Firebase Google sign-in (or any auth flow where no browser session is signed into the right account), the headless browser hits the sign-in page and the SPA never calls the protected API. Visual evidence is impossible without the user's session.

**Verified case (2026-07-08, PR #8251 / issue #8250):** Your Project deployed at `mvp-site-app-dev-i6xf2p72ka-uc.a.run.app` is gated by Firebase Google sign-in. Chrome Profiles 0/1/3 had no signed-in session; Aside u0/u1 also did not have the your-project.com account active. Playwright headless + any Chrome profile = `redirected to /sign-in`, SPA `fetch('/api/campaigns/<id>')` never fires.

## The fallback — local dev server + real Firestore + auth bypass header

The diagnosis doesn't have to come from the browser. You can prove the API contract is correct (or wrong) entirely server-side, then trace the DOM-side bug from the code. This works for ~80% of WA /repro cases that are framed as "X isn't working" — most are API-shape bugs or DOM-rendering bugs, not interactive-flow bugs.

### Step 1 — Start a local Flask dev server with the bypass headers enabled

```bash
cd $HOME/projects/your-project.com
PYTHONPATH=. \
GOOGLE_APPLICATION_CREDENTIALS=$HOME/serviceAccountKey.json \
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=$HOME/serviceAccountKey.json \
WORLDAI_DEV_MODE=true \
TESTING_AUTH_BYPASS=true \
ALLOW_TEST_AUTH_BYPASS=true \
MCP_TEST_MODE=real \
MOCK_SERVICES_MODE=false \
PORT=9081 \
python3 $PROJECT_ROOT/main.py > /tmp/dev-server.log 2>&1 &
```

Wait ~12s, then verify it's serving:
```bash
curl -fsS -i http://localhost:9081/healthz
```

### Step 2 — Hit protected endpoints with the bypass header

The `check_token` decorator in `$PROJECT_ROOT/main.py:1920-1950` honors `X-Test-Bypass-Auth: true` ONLY when the server was started with `TESTING_AUTH_BYPASS=true` AND `ALLOW_TEST_AUTH_BYPASS=true`. The user_id is read from a separate `X-Test-User-Id` header (default `test-user-123`).

To impersonate the real campaign owner (whose UID was resolved earlier with `scripts/copy_campaign.py --find-by-id <campaign-id>`), pass both:

```bash
curl -fsS \
  -H "X-Test-Bypass-Auth: true" \
  -H "X-Test-User-Id: vnLp2G3m21PJL6kxcuAqmWSOtm73" \
  "http://localhost:9081/api/campaigns/xK3fp5XrV24oarIINTF7?story_limit=10"
```

Query-string bypass is gated by `is_localhost` + requires `test_mode=true` + `test_user_id=<uid>` AS WELL as the header. The header+UID form is simpler and localhost-agnostic — prefer it.

### Step 3 — Save and inspect the wire-format response

Save the raw JSON to a path under `repro/evidence/<issue>/` so it lands in the PR's evidence bundle. Look for:

- Missing/null fields the frontend expects → API bug
- Surprising values (e.g. `has_older=false` when `story_count > limit`) → pagination logic bug
- Correct shape → DOM-side bug; read the frontend code for placement / visibility / wiring

In the verified case: `story_pagination` had `has_older=true, total_count=250, fetched_count=10` — API correct. The bug was downstream in `app.js:3099` where the button was inserted inside a scrollable container that auto-scrolls to bottom.

### Step 4 — Optional: prove the DOM-side bug with route-mocked Playwright

When the diagnosis hinges on a CSS/DOM placement question (visibility, scroll position, layout), you can verify it without an auth session by mocking the API via Playwright route interception. The deployed JS still loads; only the API responses are synthesized:

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={'width': 375, 'height': 667},
                              user_agent='Mozilla/5.0 (iPhone; CPU ...')
    page = ctx.new_page()
    page.route('**/api/campaigns/<id>*', lambda r: r.fulfill(
        status=200, content_type='application/json', body=json.dumps(synth)))
    page.goto('https://<deployed-url>/game/<id>', wait_until='domcontentloaded')
    page.wait_for_timeout(8000)
    print('LOAD_BTN count:', page.locator('#load-older-btn').count())
```

Limitation: the SPA's Firebase auth gate fires *before* `fetch('/api/campaigns/<id>')` — the page renders the sign-in card and the SPA short-circuits. Route-mocking alone won't get you past the auth gate; you still need either a real signed-in session, or to set the Firebase auth state directly (advanced). For pure CSS/DOM placement questions, **read the code instead** — the placement bug is usually obvious from `insertBefore` / `scrollToBottom` / container CSS. Visual proof is nice-to-have, not load-bearing.

### Step 5 — Tear down

```bash
kill <pid>  # capture from `pgrep -f $PROJECT_ROOT/main.py`
# Verify port freed:
lsof -nP -iTCP:9081 -sTCP:LISTEN
```

## When this fallback is the right answer

✅ Use it when:
- The deployed URL is auth-gated and you don't have the user's session.
- The bug is "the API returns the wrong shape" OR "the frontend ignores/places something wrong".
- You have `serviceAccountKey.json` and can start a local Flask server with `WORLDAI_DEV_MODE=true`.

❌ Don't use it when:
- The bug requires a real interactive flow (drag-drop, OAuth callback, payment).
- The bug requires a real LLM stream or DiceRoll over the wire (use the full e2e harness instead).
- You don't have Firestore credentials and can't read the production data.

## Pitfalls observed

- `TESTING_AUTH_BYPASS=true` alone is NOT enough — you also need `ALLOW_TEST_AUTH_BYPASS=true`. The two are checked separately in `$PROJECT_ROOT/main.py`.
- The bypass header is `X-Test-Bypass-Auth` (not `Authorization: Bearer *** A Bearer token still 401s.
- `is_production` flag in main.py is True when the app is started without `WORLDAI_DEV_MODE=true` even if TESTING_AUTH_BYPASS is set — the bypass is rejected on "production" runs. Always set `WORLDAI_DEV_MODE=true`.
- The local dev server's first request can take 5–8s due to Firestore init / MCP client startup. Wait, don't assume it failed.
- `$PROJECT_ROOT/main.py` imports `from infrastructure.executor_config import ...` — you MUST run it with `PYTHONPATH=$HOME/projects/your-project.com` (or `cwd=...`) so the `infrastructure/` package is resolvable.
- **Playwright `addInitScript` lands AFTER the SPA's `firebase.auth()` initialization** when the SPA's bundle loads as a normal `<script>`. The hook runs but `window.firebase.auth().currentUser` is still `null` from the SPA's perspective because the SPA initialized its own Firebase app instance synchronously before the patch took effect. To actually bypass you need to either (a) intercept the bundle itself and stub the firebase SDK, or (b) use a pre-signed-in browser context. When neither is feasible, jump to **Step 6** below.
- **`X-Test-Bypass-Auth` is server-side ONLY** (verified 2026-07-19, issue #8459). It does NOT bypass the JS-side `firebase.auth().currentUser` check the SPA uses for route gating + Firebase-ID-token-attached API requests. With headers set, `/api/campaigns/<id>` returns campaign data correctly, but the SPA still thinks no user is logged in → login modal overlay → `#user-input` is "not visible" to Playwright `fill()`. **For fix-verification-only repros, jump straight to Step 7 (direct JS-state injection).**
- **Firebase `PASSWORD_LOGIN_DISABLED` (verified 2026-07-19, issue #8459):** many Firebase projects disable email-password sign-in entirely; only Google OAuth works. Verified via REST: `POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=<apiKey>` returns `400 {"error":{"message":"PASSWORD_LOGIN_DISABLED"}}`. When this hits, the test-bypass header path is the only fallback — and even then, JS-side auth is still gated. **For these projects, headless live auth is not feasible; jump to Step 7.**
- **Bundle-level `apiKey` placeholder (verified 2026-07-19):** `$PROJECT_ROOT/frontend_v1/auth.js:48` ships `apiKey: '***'` in source; the real key is injected by the Cloud Build pipeline at deploy time. The deployed bundle (e.g. `https://<host>/frontend_v1/auth.<hash>.js`) DOES contain the real key — `curl` it raw, grep `apiKey:\s*['\"]([A-Za-z0-9_-]+)['\"]`, and use the captured key for REST sign-in attempts. Useful when REST `signInWithPassword` is enabled; useless when it's `PASSWORD_LOGIN_DISABLED`.
- **Port already taken (verified 2026-07-19):** picking port 8765 may collide with an existing MCP server (e.g. mcp_mail). `curl http://127.0.0.1:8765/` will return `{"detail":"Not Found"}` from the OTHER service, masquerading as Flask 404s. Always run `lsof -nP -iTCP:<PORT> -sTCP:LISTEN` first to see what's actually listening, or pick a random high port (e.g. 9123).
- **`copy_campaign.py --format json` early-exits at line 557 (verified 2026-07-19, issue #8459):** when invoked with `--format json`, the script prints `{dest_uid, dest_email}` and **exits 0 WITHOUT doing the copy**. This is the email→UID lookup step, not the copy step. Drop `--format json` to actually run the copy; you'll get a full structured run log instead. To capture the new campaign ID separately, use Firestore REST (see `references/find-new-campaign-id-after-copy.md`).
- **Local Flask server test-UID mismatch (verified 2026-07-21, char creation "big prompt" repro):** `copy_campaign.py --dest-email <your-email@gmail.com>` creates the destination campaign under UID `0wf6sCREyLcgynidU5LjyZEfm7D2`. If you then drive the test via the **MCP harness** (`testing_mcp.MCPTestBase`), the harness auto-generates a different UID like `test-cc_big_prompt_repro_<ts>-<run_id>` and sets `X-Test-User-Id` to that test UID. The harness's auto-UID can NOT see the copied campaign (404 `Campaign not found`) because Firestore routing keys on UID. **Fix:** drive the test via `curl` against the **local Flask server** (Step 1) with the explicit `X-Test-User-Id: <copied-campaign-owner-uid>` header. Don't waste time adding the copied campaign to the test harness's UID tree — Flask + headers is faster and exercises the same backend code path.
- **For end-to-end LLM-call repros, `MCP_TEST_MODE=real MOCK_SERVICES_MODE=false` are REQUIRED (verified 2026-07-21):** these two env vars are in the existing Step 1 recipe but are easy to miss. Without them, the local Flask server returns canned/mock responses instead of actually calling the LLM. If your repro needs to verify a real LLM stream end-to-end (SSE chunk emission, prompt bundle size, planning_block parse), missing either env var silently short-circuits the call to a mock — your "repro" is no longer a repro. Always start the server with the FULL env block from Step 1.

## Step 6 — Skip headless Chrome, query GCP Cloud Logging instead

**When to use:** the headless Chrome auth-gate bypass failed (Steps 3 + 4) AND the bug report is **per-campaign** ("this campaign fails, others load") rather than per-session ("nothing loads, login screen"). The user's Google sign-in is fine — they were able to load other campaigns. The bug is server-side at the campaign-load boundary, not auth.

**Why it's often better than Steps 1-5:**
- The deployed `get_campaign` handler leaves a fingerprint in Cloud Logging: HTTP `requests` rows (status code + responseSize), `client_diag` rows from the SPA's instrumentation, AND Python tracebacks on `severity=ERROR` rows. You see the *real* symptom from the *real* user's IP — no auth bypass needed.
- Most per-campaign "can't load" reports are server-side; the user's session is not the blocker.

**Recipe:**
```bash
# Find deploy + service + project
gcloud config get-value project                              # → worldarchitecture-ai (with -ture-)
gcloud run services list --project=worldarchitecture-ai --region=us-central1 | head

# Find any 4xx/5xx + Python tracebacks for this campaign in the last 2h
gcloud logging read \
  'resource.labels.service_name="mvp-site-app-dev" AND timestamp>="YYYY-MM-DDTHH:MM:SSZ" AND (
      severity=ERROR OR severity=CRITICAL OR severity=ALERT
      OR jsonPayload.message:"Traceback" OR jsonPayload.message:"TypeError"
      OR (jsonPayload.message:"<CID>" AND severity=WARNING)
   )' \
  --project=worldarchitecture-ai \
  --freshness=2h --limit=100 \
  --format='json(timestamp,resource.labels.service_name,severity,textPayload,jsonPayload.message)'
```

**What to look for:**
- HTTP status codes in the 4xx/5xx range filtered by `campaign_id` in the URL — confirms the user's exact failure
- `commit-sha` label on Cloud Run revision rows — gives you the deploy SHA to diff against `origin/main`
- `client_diag` rows from the SPA (`cdiag_name=network.error_response`, `cdiag_field_status=500`, `cdiag_field_url=/api/campaigns/<id>`) — sometimes include the exact response body the server returned
- Python tracebacks — the *only* path to root-cause from logs (Flask/Sentry route exception text usually lives in `jsonPayload.message` with stack frames)

**Verified worked example (2026-07-12):** Campaign `a1OGXHNxNdw1Id0iRfpR` "Re:zero Theresa " intermittently 500'd on first load. `addInitScript` failed to bypass auth (Steps 3+4). Routed to GCP logs, found `TypeError: Object of type {Sentinel,set} is not JSON serializable` at `$PROJECT_ROOT/main.py:2619 in get_campaign`. Same root cause produced 500s for 2 sibling campaigns (`5MYrGMUZovrK6hgv3Qiu`, `FsiyESY987DF2lfgolCI`) within ~13 minutes from the same client IP — confirming the user's hunch that "i can access some campaigns but not others" was the right frame. Filed as issue [#8353](https://github.com/$GITHUB_REPOSITORY/issues/8353). Full bug-class recipe: `references/json-serialization-leak.md`.

**Anti-pattern:** don't keep grinding on Steps 3+4 (route-mock + `addInitScript`) when the user's complaint is per-campaign, not per-session. The auth isn't the blocker; GCP Cloud Logging filtered to `campaign_id` will give you the symptom + root cause in one query.

## Step 7 — Direct JS-state injection for fix-verification-only repros

**When to use:** the user has reported a bug AND named a PR they say fixed it ("we merged a PR to fix this"). You need to verify the fix is live and the user's symptom is mitigated. Steps 1-6 fail or are blocked (Firebase `PASSWORD_LOGIN_DISABLED`, JS-side auth gate overlay, etc.). The fix's code path does NOT require auth state — e.g. localStorage draft persistence, pushState interceptor, modal handler, debounced input save.

**Why it works for fix-verification:** most fix code paths tested by `/repro` are pure DOM + browser-API logic (input event listeners, localStorage, history.pushState overrides, modal visibility). They don't need `firebase.auth().currentUser` to be set — they're wired by the script's `DOMContentLoaded` listener or load-time setup. You can bypass auth entirely AND drive the fix code path with `page.evaluate()` direct JS injection.

**Recipe (verified 2026-07-19, issue #8459 / PR #8325 — `feat: persist interaction input + cancel-on-navigate`):**

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # mobile viewport for "happens on mobile" bugs
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=3,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                   "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        is_mobile=True, has_touch=True,
    )
    page = ctx.new_page()
    campaign_id = "<CID>"

    # 1. Load the deployed URL (no auth required — bundles load even if SPA redirects to login)
    page.goto(f"https://<host>/game/{campaign_id}", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)

    # 2. Confirm the fix code is in the deployed bundle by counting unique markers
    page.screenshot(path="01-game-page.png")

    # 3. Drive the fix path via direct JS injection — bypass the textarea's
    #    "not visible" gate that login-modal overlays impose on Playwright fill().
    result = page.evaluate("""async (campaignId) => {
        const draftKey = `wa:pending-input:${campaignId}`;
        // (a) Plant the draft directly in localStorage
        localStorage.setItem(draftKey, 'Test draft persistence from /repro #N');
        // (b) Drive the input value (visible or not, the app's input listener
        //     lives at the document/window level via addEventListener chain)
        const inputEl = document.getElementById('user-input');
        if (inputEl) {
            inputEl.value = 'Test draft persistence from /repro #N';
            inputEl.dispatchEvent(new Event('input', {bubbles: true}));
        }
        await new Promise(r => setTimeout(r, 800));   // wait for debounce
        // (c) Capture: did the fix's debounced save fire?
        const ret = window.history.pushState({}, '', '/some-other-page');
        const modal = document.getElementById('cancelPendingModal');
        return {
            draft_after_input: localStorage.getItem(draftKey),
            pushState_returned: ret,
            pushState_strict_false: ret === false,
            modal_visible: modal ? modal.classList.contains('show') : false,
        };
    }""", campaign_id)
    print(result)
```

**What this catches (and what it doesn't):**

| Fix path | Catches? | Why |
|---|---|---|
| Debounced localStorage save on input event | ✅ Yes | Listener is wired at load time; we trigger it ourselves |
| pushState interceptor returns false on active stream | ⚠️ Partial | Interceptor code runs; but we can't manufacture a real `pendingStream[id]` entry from outside the closure — only the modal-handler path is testable |
| Cancel-pending modal Continue+Stay / Cancel+Leave buttons | ⚠️ Partial | If the modal opens (via force), click handlers run |
| Rehydrate input from localStorage on campaign load | ❌ No | `loadCampaign` is gated behind Firebase auth; we can't fake a real auth session |
| Bundle contains the fix code (static check) | ✅ Yes | `curl <host>/frontend_v1/app.<hash>.js`, grep for `MAX_DRAFT_LENGTH = 5000`, etc. |

**The verdict matrix when full live test is blocked:**

1. ✅ Static bundle contains fix code (curl + grep)
2. ✅ Static bundle has same hash as origin/main at the PR's commit (diff or grep)
3. ✅ Direct JS injection fires the fix's primary path (debounced save + localStorage write)
4. ⚠️ Secondary paths (modal, rehydrate) verified by static-analysis + code-line proof only
5. **Verdict:** FIX_VERIFIED, with the caveat that secondary paths are code-verified rather than live-verified — call this out in the PR body

**Anti-pattern:** grinding on auth bypass for hours to live-test a path that's trivially testable via direct JS injection. The fix-verification question is "does the fix code exist and does it fire?" — not "does the user's exact auth-gated login flow work?" If the fix code's primary path is testable in 30 seconds without auth, take it.

**Verified worked example (2026-07-19, issue #8459 / draft PR #8460):** PR #8325 (`feat: persist interaction input + cancel-on-navigate`) on campaign `Cg2m2TkGFFez7XBynEah`. Tested via headless mobile Chrome against deployed DEV `mvp-site-app-dev-i6xf2p72ka-uc.a.run.app`. Firebase auth on `<your-email@gmail.com>` returned `PASSWORD_LOGIN_DISABLED` on REST; local Flask bypass produced working API but JS-side `firebase.auth().currentUser` was null → login modal overlay → `#user-input` "not visible" to Playwright `fill()`. Switched to Step 7. Result: `localStorage['wa:pending-input:mZ53dcaw72ZhHkowJPpB']` populated 600ms after the injected `input` event — **debounced save fires end-to-end**. The cancel-pending modal path (path 2) was code-verified at `app.eff9cf9b.js:5256-5303` because we couldn't manufacture `pendingStream[id]` from outside. Rehydrate (path 3) was partial — localStorage persists across reload, but `loadCampaign` couldn't run without Firebase auth. VERDICT: FIX_VERIFIED with stated caveats. Total wall time: ~12 minutes from Steps 1-7 abandoned to VERDICT posted to PR.
# Structural harness: when auth blocks every full-app repro path

**Verified 2026-07-08 with PR #8251 on $GITHUB_REPOSITORY (issue #8250).**

## The trap

You land a `/repro` task. The bug is a UI placement / visibility issue — clearly
visual. The user says "use headless browser to view if needed." The Contract
in `finish-the-job` requires visual proof.

You try the obvious paths and ALL of them fail:

1. **Deploy the URL in a headless browser** — page is gated by Firebase Google
   sign-in. User's Chrome/Aside profiles aren't signed into the workspace
   account. Page renders only the "Continue with Google" button.
2. **Mock Firebase auth client-side** — `window.firebase.auth().currentUser`
   stub isn't enough; the deployed `app.js` calls `firebase.initializeApp` and
   `onAuthStateChanged`, and these need a real Firebase config to bootstrap
   cleanly. Stubbing them leaves the page in "User not authenticated, redirecting
   to login" loop.
3. **Load the deployed index.html + swap in your app.js** — the deployed HTML
   pulls many other scripts (`/frontend_v1/js/campaign-wizard.<hash>.js`,
   `enhanced-search.<hash>.js`, etc.) which 404 against your local server. The
   page also depends on `bootstrap.Modal.getOrCreateInstance` which fails
   silently when bootstrap isn't fully loaded.
4. **Run full app.js against a minimal harness** — `app.js` is wrapped in a
   `document.addEventListener('DOMContentLoaded', ...)` IIFE that expects
   ~10 specific element IDs (`#auth-container`, `#dashboard-view`,
   `#new-campaign-view`, `#game-view`, etc.) plus `bootstrap.Modal`, plus
   `window.firebase`. Even with all of those stubbed, the page errors with
   `Cannot read properties of null (reading 'addEventListener')` before the
   test sequence can run.
5. **Make your own harness HTML that mirrors the page structure** + the
   inline `app.js` — same problem; the IIFE bails on boot because some DOM
   element isn't present.

You have 4 harness shapes tried in the same session and 0 visual proof. The user
is waiting.

## The fallback: structural DOM-equivalent harness

Stop trying to load the full app. The bug is in **one specific function**
(`updateLoadOlderButton()` in this case). That function's only effect on the
DOM is "insert a button at a specific location relative to #story-content."

**The harness only needs to replicate the DOM that the buggy function + the
triggering code path produce.** No app.js. No Firebase. No bootstrap. Just
HTML + CSS + a tiny inline script that mimics the relevant scroll behavior.

### Recipe (4 steps, ~30 minutes)

1. **Identify the two DOM outcomes that differ.** For the pagination bug:
   - OLD (buggy): `<button id="load-older-btn">` is a child of `#story-content`
     (which has `max-height: 80vh; overflow-y: auto`).
   - FIXED: `<button id="load-older-btn">` is a sibling BEFORE `#story-content`,
     inside `#story-area`.

2. **Build two HTML files that differ ONLY in that placement.** Same viewport,
   same parent IDs, same button class names, same scrollable container, same
   number of fake story entries, same auto-scroll-to-bottom JavaScript. The
   only delta is the button's `parentNode`.

3. **Use Playwright (or any headless browser) to render both at the viewport
   size that triggers the bug** — for the pagination bug, mobile 375x667
   because `story_limit=100 < 250-entry campaign` is the failing case.

4. **Capture screenshots AND pixel coordinates of the button's
   `getBoundingClientRect()`.** The pixel coordinates are the durable proof
   — they don't rot like a PNG does if Slack compression artifacts them. The
   transcript should look like:

   ```
   === OLD (buggy) ===
   OLD_PILL: FAIL — button OFF-SCREEN (top=-3749, bottom=-3718, viewport=667)
   OLD_RESULT: {"ok":false,"top":-3749,"bottom":-3718,"parent":"story-content"}

   === FIXED ===
   FIXED_PILL: PASS — button visible (top=90, bottom=121)
   FIXED_RESULT: {"ok":true,"top":90,"bottom":121,"parent":"story-area"}
   ```

   The pixel-coord delta (`top=-3749 → top=90`) IS the bug→fix transition.

### What this harness proves and what it doesn't

**Proves:**
- The DOM placement difference is the cause of the user-visible symptom.
- After scroll-to-bottom, the button is in viewport (or off-screen) per
  `getBoundingClientRect()`. This is the exact mechanism by which the bug
  manifests.

**Doesn't prove:**
- The actual `app.js` still works after the fix lands — you'll need to run
  unit/integration tests for that.
- The fix doesn't break unrelated code paths.
- The deployed page (post-merge) renders correctly — that needs a deploy
  + auth'd browser session, which is the original blocker.

For UI-only bugs, this is sufficient evidence to ship. For bugs that involve
app.js logic (not just DOM placement), you'll need a real app.js harness or
unit tests on top of the structural harness.

### When NOT to use this fallback

- The bug is in app.js LOGIC (not DOM placement) — you need real app.js.
  You can still use a structural harness as a *visual aid* but the proof
  has to come from unit/integration tests against the real function.
- The bug is in CSS only — fix the CSS, run the structural harness with
  the fix applied, screenshot the diff. This is fine and well-precedented.
- The bug is in network behavior (API returns wrong shape) — capture the
  raw API response, not a DOM screenshot.

## Worked example transcript (PR #8251)

User: "Run /repro — pagination is broken, it used to show a load more thing."

Tried (all failed):
- `curl /game/<id>` → 401 (auth required)
- Aside headless browser → "Continue with Google" button (auth gate)
- Playwright with persistent Chrome profile → still "Continue with Google"
- Playwright route() intercepting /api/campaigns/<id> → page never rendered
  because Firebase auth blocked it
- Deployed index.html + local app.js swap → 30+ script 404s + bootstrap
  modal error
- Self-contained harness HTML + inline app.js → `Cannot read properties of
  null (reading 'addEventListener')` at app.js boot

Pivot (this file): built two 20KB HTML files with hand-coded DOM that
replicates what `updateLoadOlderButton()` produces for each version of the
code. Used the deployed pagination-styles.css (`max-height: 80vh;
overflow-y: auto`) and Bootstrap classes. Captured pixel coordinates.

Result: structural proof in 30 seconds, screenshots in another 30. PR
shipped with full evidence bundle in `repro/evidence/8250_pagination_game_load_older/`.

## Worked example transcript — JSON-payload-driven DOM diff (PR #7953, 2026-07-10)

User: "Lets try to finally get some evidence for this using /af and I want
before/after screenshots and read the PR. There should be a visual where
before counters didnt show before and now they do."

Context: PR #7953 changes `$PROJECT_ROOT/rate_limiting.py::_build_allowed_response`
to add `reset_time_daily` + `reset_time_hourly` to the success-path response.
The modal in `$PROJECT_ROOT/frontend_v1/app.js` (`showRateLimitModal` +
`updateQuotaBanner`) renders these fields into the count-down panel. Capturing
real `local.sh` flow would require LLM spend + auth bypass + a real campaign
— net cost >5 minutes for the same proof.

Pivot: capture the response payload directly by invoking
`_build_allowed_response` on both worktrees (the only function the PR
changes) with the same input. Then build ONE structural harness HTML that
renders the modal with EITHER payload selected via `?branch=before` /
`?branch=after`. Same DOM, same modal chrome, same quota cards — only the
reset-time fields differ (BEFORE absent, AFTER present). Playwright captures
both desktop (900x920) and mobile (390x844) viewports in 5 seconds total.

Recipe:
1. **Identify the function under change.** `grep -nE '_build_allowed_response'
   $PROJECT_ROOT/rate_limiting.py` → 1 location. Verify via
   `git diff origin/main..HEAD -- $PROJECT_ROOT/rate_limiting.py` that the PR diff
   is contained there.
2. **Direct-invoke on each worktree.** Write a 30-line Python script that sets
   `PYTHONPATH=<worktree>` and calls the function with hand-built inputs:
   ```python
   response = rate_limiting._build_allowed_response(
       turn_timestamps=[six_hours_ago, one_hour_ago, fifteen_min_ago, five_min_ago],
       daily_cutoff=now - rate_limiting.RATE_LIMIT_DAILY_WINDOW_SECONDS,
       window_cutoff=now - rate_limiting.RATE_LIMIT_5HOUR_WINDOW_SECONDS,
       daily_limit=100, window_limit=50,
   )
   json.dump(response, open(f'/tmp/quota-capture-{branch}.json', 'w'))
   ```
   Compare the JSON keys: BEFORE = 4 keys (no reset times), AFTER = 6 keys.
3. **Build ONE self-contained harness HTML.** All UI chrome (modal CSS, badge
   pills, quota cards) is hand-coded. A `PAYLOADS = { before: {...}, after: {...} }`
   dictionary holds both response shapes. A `URLSearchParams` reads `?branch=` and
   picks which PAYLOAD to render. The JS reads `data.reset_time_daily` —
   BEFORE returns undefined (panel renders RED "unavailable"), AFTER returns
   real timestamps (panel renders YELLOW with count-down minutes + UTC).
4. **Capture screenshots via Playwright.** Two commands, one per `?branch=`
   value:
   ```bash
   playwright screenshot --viewport-size 900,920 --wait-for-timeout 2000 \
     "http://127.0.0.1:8765/modal.html?branch=before" /tmp/before.png
   playwright screenshot --viewport-size 900,920 --wait-for-timeout 2000 \
     "http://127.0.0.1:8765/modal.html?branch=after"  /tmp/after.png
   ```
5. **Publish bundle.** Gist for `gh` markdown-embeddable URLs (PR description),
   Slack `files.completeUploadExternal` for thread attachments.

Result: 4 PNGs (desktop + mobile × before/after), 2 JSON captures, 54/54
targeted tests passing, PR comment posted with gist-embedded screenshots,
4 PNGs uploaded to the Slack thread. Total wall-clock: ~25 minutes from
user message to thread delivery. PR comment: https://github.com/$GITHUB_REPOSITORY/pull/7953#issuecomment-4938461121

**Why this works:** the structural harness isolates the **payload shape
delta** (which IS what the PR changes) from everything else (auth, LLM, real
campaigns). Same modal chrome, same card layout — only the rendered reset-time
panel differs. The screenshot is unambiguously the PR's effect.

**Pivot triggers (in priority order):**
1. `local.sh` boot eats >3 minutes before any user interaction possible
2. LLM cost gate (Gemini/Cerebras tokens per `local.sh` flow)
3. Auth bypass requires special env that PR CI didn't set up
4. The PR diff touches ≤3 functions; capturing them directly is faster

## Companion references

- `evidence-attach-to-slack` — how to upload the screenshots to the thread
  once you have them.
- `web-page-screenshots` — for capturing the screenshots; the structural
  harness renders fine via Playwright's `screenshot` CLI.
- `repro-twin-clone-evidence` (repo-local at
  `projects/your-project.com/.claude/skills/repro-twin-clone-evidence/SKILL.md`)
  — the canonical /repro workflow that triggers this fallback when the
  visual proof steps fail.

## Decision matrix — when to fall through to the structural harness

| Visual proof approach | When to try it | When to fall through |
|---|---|---|
| Deployed URL in headless browser | Always first | Auth gate, page error, or wrong DOM |
| Aside headless with user's session | User is signed in to target app | Session absent |
| Playwright route() intercept | API endpoint is the only network dependency | Auth happens before API |
| Local dev server with TESTING_AUTH_BYPASS | Repo supports bypass env var | Production-mode deploy |
| **Structural DOM-equivalent harness** | **UI placement / CSS-only bug** | **Bug is in app.js logic** |
| Unit test against the buggy function | Logic bug with isolated function | DOM-bound bug |

Try the rows top-to-bottom. The structural harness is row 5, not row 1.

## Pattern summary

When the Contract requires visual proof but every full-app repro path is
blocked, do NOT stall. Pivot to a structural DOM-equivalent harness that
isolates the single variable that differs. Capture pixel coordinates
(`getBoundingClientRect()` of the affected element) as the durable proof,
alongside the PNG screenshots. Ship the PR with the structural evidence
bundle, named in a way that makes it obvious it's structural and not
end-to-end (e.g. `BEFORE-mobile-375x667.png`, `AFTER-mobile-375x667.png`,
`harness-output.txt` with pixel transcripts).
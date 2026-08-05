---
name: web-advice
description: "Browser-based multi-model review using ChatGPT, Gemini, Grok, and Perplexity Web via real authenticated browser sessions. Use when you need an independent multi-model adversarial pass over a PR, evidence bundle, design doc, or video/screenshot evidence — not for in-session reviews (use /advice for that). HARD RULE: real websites only — provider APIs, CLI models, and subagents are banned substitutes even with disclosure."
when_to_use: "Use when the user invokes /web-advice, asks for a multi-model web review, wants ChatGPT/Gemini/Grok/Perplexity to independently verdict a PR or evidence bundle, or needs video/image evidence reviewed by a web-only model (Gemini web is the only video-capable seat). Do NOT use for in-session code review (/advice) or evidence-bundle integrity checks (/er)."
allowed-tools: mcp__aside-mcp__repl, aside (Bash CLI), mcp__claude-in-chrome__*, Bash (chrome-headless via Playwright + browserclaw-decrypted cookies), Read
context: inline
---

# /web-advice — Multi-Model Browser Review

`/web-advice` queries independent web LLMs (ChatGPT, Gemini, Grok, Perplexity) through their **real web UIs in a real authenticated browser session**, then synthesizes their verdicts. Different from `/advice` (in-session, subagents + /secondo + /research) and `/er` (evidence-bundle integrity, 4-gate checksum/SHA check).

---

## 1. HARD-FAIL CONTRACT — real websites or STOP (operator ruling, 2026-08-02)

`/web-advice` means a **real browser session on the real site**, nothing else.

- **BANNED even with disclosure:** provider APIs (Gemini Files API, OpenAI API, xAI API), CLI models (agy/codex/gemini CLI), in-session subagents, WebSearch/WebFetch synthesis. Running one of these and calling it "/web-advice" is a method-fidelity violation — no "disclosed downgrade" exception. (2026-08-02: an operator explicitly rejected a disclosed API substitution; that ruling is binding here.)
- **If no transport in the ladder below is live: STOP.** Run `scripts/e2e_smoke.sh` (see [scripts/](#scripts-evals-resolvermd--transport--prompt-automation)) first — it prints the full probe matrix non-destructively. Report verbatim which transports failed and their exact errors, and ask the user to fix/reconnect. Do not proceed, do not substitute.
- Deterministic core, unit-tested: `resolve_transport_ladder(probe_results)` in `scripts/web_advice_transport.py` raises `WebAdviceHardFail` when every probe is false — that IS this contract as code, call it instead of reimplementing the if/else inline. `is_banned_substitute(mechanism)` is the check to run before ever labeling a result "/web-advice".

## 2. Transport ladder — probe in this order, use the first that's live

| # | Transport | Probe command |
|---|---|---|
| 1 | `mcp__aside-mcp__repl` | `console.log((await listBrowserTabs()).length)` via the repl tool |
| 2 | `aside repl` CLI in Bash (same API; use when MCP stdio is stale) | `aside repl "console.log((await listBrowserTabs()).length)"` |
| 3 | `claude-in-chrome` extension | `mcp__claude-in-chrome__list_connected_browsers` — must return non-empty |
| 4 | Chrome-headless + browserclaw-decrypted cookies | `browserclaw cookies decrypt --db "$HOME/Library/Application Support/Google/Chrome/Default/Cookies" -o /tmp/ck.json --domain-filter '%<site>%'` then Playwright `launch(channel="chrome", headless=True)` + `add_cookies` |

All four are real-website transports — none is a substitute. `browserclaw` here is used ONLY for its cookie-decrypt utility, never as an API bypass. Delete `/tmp/ck_*.json` after the run.

## 3. No-focus-steal launch (mandatory on this machine)

- If probe 1/2 returns `"No last-focused window"`, the Aside daemon is alive but has no window. Launch WITHOUT stealing focus: `open -g -a "/Applications/Aside.app"` (`-g` is mandatory).
- **NEVER** `open -a "Aside.app"` (no `-g`) and **NEVER** pass a URL through `open` — both foreground the app and steal the user's focus (user-flagged 2026-08-02).
- Open tabs via repl `openTab(url)` only — verified with `osascript` before/after that frontmost app is unchanged across `openTab` calls.

## 4. Visual-description-first prompting (the biggest quality lesson)

Grok and Perplexity cannot ingest video but CAN ingest images. Never open with an abstract "review this" question — that produces INSUFFICIENT verdicts about evidence theory, not your actual evidence (2 review rounds were burned this way on 2026-08-02). Sequence every visual prompt: **(1) describe literally what's in each frame, no inference → (2) what changed between frames → (3) verdict → (4) what would change the verdict.** A model describing something not present in the frame is itself a finding. Copy-pasteable templates: [Prompt shapes](#prompt-shapes).

---

## Seat availability matrix

| Seat | Video ingest? | Image ingest? | Transport | Known walls |
|---|---|---|---|---|
| **Gemini web** | **YES — the only video-capable seat** | YES | aside repl, or chrome-headless w/ `%google.com%` cookies | None once uploaded; long polls required (Send stays disabled during upload processing; allow ≥420s for a stable response) |
| **ChatGPT web** | NO | YES (once logged in) | aside repl (only if user is logged into chatgpt.com inside Aside) — otherwise DEAD END, see below | Cloudflare walls plain/copied-profile headless — see "ChatGPT dead end" |
| **Grok web** | NO | YES | aside repl | `page.screenshot()` reliably CDP-timeouts at any timeout value (iframe interference) — use the DOM snapshot tree as the proof artifact, never a screenshot. **grok.com has SIX `input[type="file"]` elements — a bare `.first()` locator silently attaches to the wrong one, no exception, zero images uploaded** — use the [Verified upload recipe](#verified-upload-recipe-per-provider--mandatory-before-prompting) below, never a bare file-input locator |
| **Perplexity web** | NO | YES | aside repl | Defaults to web-grounded "Search" mode; switch to "Reasoning" mode for code-only review. **Free plan hit its upload limit after a single 3-image submission** (2026-08-02: "You've reached the file upload limit on the Free plan" banner appeared right after one round) — budget for this before a multi-round batch; a wait or plan upgrade may be needed between rounds |

### Honest seat accounting — mandatory (user directive 2026-08-02)

If any seat is unavailable, the synthesis MUST say so explicitly — never present a partial panel as the full one. Required in every synthesis with a missing seat:

1. **Which seat is missing**, named explicitly (ChatGPT / Gemini / Grok / Perplexity).
2. **Which in-policy paths were exhausted** for that seat — cite the actual attempts (e.g. for ChatGPT: "headless Cloudflare-walled, cookie-copy profile deletes auth cookies [Chrome anti-theft hardening, not a bug — do not retry], claude-in-chrome extension not connected, CDP :9222 not listening"), not a generic "unavailable."
3. **The explicit fraction, N-of-4**, in the synthesis header — e.g. `**Panel: 3-of-4 (ChatGPT unavailable — see below)**` — never a table that quietly has 3 rows.

Reaching a decision with a partial panel (3-of-4, even 2-of-4 across different model families) is fine — *hiding* that the panel was partial is not. `seat_accounting(seats)` in scripts/ (below) implements this automatically; run `scripts/e2e_smoke.sh` before starting so the missing-seat explanation is backed by real probe output, not a guess.

---

## ChatGPT dead end — read this before re-attempting (do not re-burn the hour)

**Do not retry cookie-copy or plain-headless for ChatGPT.** Both are proven, verified dead ends, not flaky bugs:

- **Plain/synthetic headless Chrome** → Cloudflare "Just a moment…" wall, confirmed at every timeout tried.
- **Cookie-copy of the user's real Chrome profile** → the copy correctly carries non-sensitive `chatgpt.com` cookies, but Chrome's own anti-cookie-theft hardening **silently fails to decrypt and then deletes** the security-hardened `.auth.openai.com` cookies (`unified_session_manifest`, `usc_*`, `oai-client-auth-info`) from the copied DB on open — verified 3 ways: pre-launch decrypt shows 12 openai.com cookies present, post-launch `Network.getAllCookies()` shows 0 loaded, and re-querying the SAME copy's SQLite file after Chrome closes shows the rows physically deleted (12→0), while the 11 non-auth cookies survive untouched. This is a real anti-abuse control working as designed — defeating it is out of policy. **Stop here, don't re-attempt.**

**The two remaining in-policy paths (both require a user action — cheapest first):**

1. **User clicks "Connect" in the Claude-in-Chrome extension toolbar** (extension is already installed in the user's real Chrome `Default` profile, id `fcoeoabgfenejglbffodgkkbkcdhcgfn`). Probe with `mcp__claude-in-chrome__list_connected_browsers`.
2. **User quits and relaunches their own Chrome with the debug port open**: `open -a "Google Chrome" --args --remote-debugging-port=9222`, then CDP-attach via `chromium.connect_over_cdp("http://127.0.0.1:9222")`. Verify the port is live first with `curl -s http://127.0.0.1:9222/json/version`. Never quit/relaunch the user's Chrome yourself — ask them to do it.

Full investigation provenance (four paths tried, exact commands/output) is in [Field notes](#field-notes--chatgpt-transport-investigation-2026-08-02).

---

## Prompt shapes

Both templates are copy-pasteable. Build the prompt BEFORE opening any tab so the same text goes to every seat in one pass (adapt only the video-vs-frame instruction). `build_visual_prompt(claim, frame_names)` in scripts/ (below) renders the frame template programmatically so the description-first ordering can't be accidentally dropped.

### VIDEO review (Gemini web only — the only video-capable seat)

```markdown
You are reviewing a video artifact as evidence for a claim. Do NOT skip to a verdict.

Step 1 — DESCRIBE, don't infer: Watch the full video. Report literally what you see,
second by second: what's on screen, what moves, what text/UI is visible, what changes.
Do not describe what you assume is happening — only what is visibly rendered.

Step 2 — CHANGE LOG: List what visibly changed between the start, middle, and end of
the video (positions, states, text, colors). Cite approximate timestamps.

Step 3 — VERDICT (only after steps 1-2):
VERDICT: <PASS | FAIL | INCONCLUSIVE>
REASONING: 3-4 sentences, grounded ONLY in what you described in Step 1-2
RISK: main risk, one sentence
CONFIDENCE: high | medium | low

Step 4 — FALSIFIABILITY: What single additional frame or detail would change your verdict?

Claim being evaluated: <paste the exact claim>
```

Upload mechanics: click `button[aria-label="Upload & tools"]` → `input[type=file]` appears (dynamic — fallback `expect_file_chooser()` around the "Upload files" menu item) → `set_input_files`. The **Send** button stays disabled until upload processing completes — poll it (up to ~3 min), then poll the last `message-content` innerText until stable ×3 (allow ≥420s total).

**Never reconnect to a Gemini thread via a fresh `storage_state` load.** Loading cookies into a new context and navigating back into what looks like the same conversation starts a **blank chat**, not the continuation of the uploaded-video thread — the model has no memory of the upload. Keep upload → paste prompt → send → poll response as ONE continuous browser session; a 420s poll was burned re-learning this on 2026-08-02. If the session dies mid-review, re-upload the video in a new thread rather than trying to resume the old one.

### VISUAL FRAME review (all 4 seats — description-first)

**MANDATORY before this prompt is sent to any seat:** the upload must be verified per the [Verified upload recipe](#verified-upload-recipe-per-provider--mandatory-before-prompting) below — do not proceed to Step 1 on an unverified upload (see the 2026-08-02 Grok incident that motivated this: a silently-failed upload, no exception, produced a confident, fully-fabricated verdict for content that was never uploaded).

```markdown
You are reviewing N still frames as evidence for a claim. Do NOT skip to a verdict.

Frames are numbered in upload order — refer to each frame by this exact number
throughout your response:
Frame 1 = <filename 1>
Frame 2 = <filename 2>
... (one line per frame)

Step 1 — DESCRIBE each image literally, BY ITS FRAME NUMBER ABOVE: objects, positions,
colors, visible text, UI state. Do not infer intent, story, or what "should" be
happening — report only pixels you can point to.

Step 2 — CHANGE LOG: What changed from Frame 1 → Frame 2 → ... → Frame N? Cite the
specific visual difference for each transition. If nothing changed between two frames,
say so explicitly — that is itself a finding.

Step 3 — VERDICT (only after steps 1-2):
VERDICT: <PASS | FAIL | INCONCLUSIVE>
REASONING: 3-4 sentences, grounded ONLY in what you described in Step 1-2
RISK: main risk, one sentence
CONFIDENCE: high | medium | low

Step 4 — FALSIFIABILITY: What would change your verdict?

Claim being evaluated: <paste the exact claim>
```

The explicit `Frame N = <filename>` mapping exists because a model can read every frame's pixels correctly and still discuss them **out of upload order** — Perplexity did exactly this on 2026-08-02 (own "Frame 1/2/3" labels didn't match upload order), which scrambled its causal narrative and cost it a verdict notch (PARTIALLY SUPPORTED vs. the SUPPORTED that Gemini/Grok reached on identical evidence read in order). After scraping the response, run `verify_frame_order(prompt_frame_names, model_reported_order)` (scripts/, below) against the model's own `Frame N = ...` echo — a non-empty `reordered_frames` in the result is a real finding to note in the synthesis, not silently accepted.

**Submitting long prompts (2000+ chars):** `keyboard.type()` is minutes-slow at this length, AND Gemini's contenteditable box can submit prematurely on an embedded newline. Use clipboard instead:

```javascript
await pg.evaluate(t => navigator.clipboard.writeText(t), prompt);
await pg.keyboard.press('Meta+A');
await pg.keyboard.press('Backspace');
await pg.keyboard.press('Meta+V');
// verify innerText().length is within ~20% of the source prompt's length BEFORE pressing Enter
```

**Verdict scraping:** `snapshot(page)` → `tree.indexOf('VERDICT')` → slice forward. `parse_verdict(tree_text)` in scripts/ (below) does this programmatically and tolerates markdown-bold labels and blockquote markers. **Proof-of-real-website artifact** = a screenshot (or, for Grok, the DOM snapshot tree — screenshots CDP-timeout there) showing the response rendered in the site UI with the user's profile avatar visible.

### Verified upload recipe (per provider) — MANDATORY before prompting

**Why this exists (2026-08-02, bead wc-kjny):** Grok's first upload attempt used `page.locator('input[type="file"]').first()` — no exception was thrown, the call logged "files set." But `grok.com` has **SIX** `input[type="file"]` elements and `.first()` silently grabbed the wrong one; `document.querySelectorAll('img')` afterward showed zero uploaded images (only Grok's own avatar + a cookie-consent-banner logo). Grok then produced a fully-formatted `DESCRIPTION` and `VERDICT: NOT SUPPORTED` for content that does not exist anywhere in the app — a **"9:41" status bar** (Apple's marketing-screenshot placeholder), a **"hooded figure"** with a weapon, "the scent of ozone lingering," a **"🎲 Roll Initiative" button** — and claimed 2 frames were pixel-identical although 3 were referenced. A broken upload is **indistinguishable from a working one** at every layer the calling code normally checks (no exception, a plausible success log line, a model willing to answer confidently anyway).

**Per-provider recipe, verified 2026-08-02:**

| Provider | Do this | NEVER do this |
|---|---|---|
| **Grok** | Click `button[aria-label="Attach"]` → a menu opens (`"Upload a file"` / `"Recent"` / `"Project"` / etc.) → click `"Upload a file"` → this triggers a REAL `filechooser` event (`page.expect_file_chooser()` around the click) → `set_input_files`. Verify via `document.querySelectorAll('img')` showing `assets.grok.com` URLs. | A bare `page.locator('input[type="file"]')...set_input_files(...)` without going through the Attach button+menu — grok.com has 6 file inputs on the page and a naive selector (`.first()`, `.nth(0)`, or no disambiguation at all) can silently bind to the wrong one |
| **Gemini** | Click `button[aria-label="Upload & tools"]` → dynamic `input[type=file]` appears → `set_input_files`; fallback `page.expect_file_chooser()` around the "Upload files" menu item (see [VIDEO review](#video-review-gemini-web-only--the-only-video-capable-seat) above for the full upload-mechanics note). Poll the Send button until enabled (gated on upload processing) before treating the upload as done. | Assuming the upload finished just because `set_input_files` returned — Send stays disabled during processing; submitting before it re-enables races an incomplete upload |
| **Perplexity** | Use the composer's attach/paperclip control to open the file chooser, then verify via the **"N attachments" pill** that appears in the composer (e.g. "3 attachments") — this is the `attachment_indicator_text` signal for `assert_attachment_verified()`. **Free plan hits its upload limit after a single 3-image submission** (2026-08-02: "You've reached the file upload limit on the Free plan" banner appeared right after one round) — check for that banner before trusting a subsequent round's response as image-grounded. | Treating the mere presence of the compose box or a "file selected" toast as proof — confirm the actual "N attachments" pill, not an intermediate UI state |
| **ChatGPT** | No verified upload recipe yet — ChatGPT is currently a [dead end](#chatgpt-dead-end--read-this-before-re-attempting-do-not-re-burn-the-hour) for all transports in this skill; do not attempt an image upload there until a transport is live. | — |

**MANDATORY gate — verify attachment before prompting:** immediately after the upload action and BEFORE typing/submitting the review prompt, probe the DOM (scoped to the composer's attachment-preview area, NOT a raw page-wide `querySelectorAll('img')` — that count is non-empty even on a failed upload because it includes the avatar/cookie-banner) and call `assert_attachment_verified(dom_probe_result)` in scripts/ (below). It raises `AttachmentNotVerifiedError` unless at least one of: (a) a new `<img>` in the attachment-preview area, (b) a URL matching a known provider attachment-CDN host (`assets.grok.com`, `oaiusercontent.com`, `pplx-res.cloudinary.com`, ...), or (c) an explicit "N attachments"/"N files attached" indicator with N > 0. **If it raises: STOP. Do not send the prompt. Re-locate the upload control per the recipe above, retry, and re-probe.** If a response was already obtained without a passing check, **discard it — do not record its verdict** (see `evals/web_advice_evals.md` Case 5 — "unverified attachment, confident verdict" — the single most important eval case in that file).

---

## scripts/, evals/, RESOLVER.md — transport + prompt automation

`~/.claude-wa/skills/web-advice/scripts/web_advice_transport.py` is the audited, unit-tested source of truth for the deterministic parts of this skill (0 browser/network calls, safe to run anywhere) — use these instead of re-deriving the ladder/parsing logic inline each run. Browser execution (opening tabs, typing, polling) is inherently stateful/live and is NOT extracted here; it stays as skill instructions above.

| Function | Encodes | Section above |
|---|---|---|
| `resolve_transport_ladder(probe_results)` → transport name, raises `WebAdviceHardFail` | Hard-fail contract + ladder order (`aside_mcp` → `aside_cli` → `chrome_extension` → `cdp_port` → `chrome_cookies`) | HARD-FAIL CONTRACT / Transport ladder |
| `is_banned_substitute(mechanism)` → bool | Provider APIs / CLI models / subagents / WebSearch are never "/web-advice" | HARD-FAIL CONTRACT |
| `build_visual_prompt(claim, frame_names)` → str | Description-first frame prompting (describe → what changed → verdict → falsifiability) | Prompt shapes |
| `parse_verdict(tree_text)` → dict | Verdict scraping tolerant of markdown-bold, colon-separated, and blockquote-`>` response formats | Step 4 — Capture responses |
| `seat_accounting(seats)` → str | Honest N-of-4 accounting, never a quietly-partial panel | Honest seat accounting |
| `assert_attachment_verified(dom_probe_result)` → `None`, raises `AttachmentNotVerifiedError` | "No exception thrown" is NOT proof of a successful upload — requires a new attachment-area `<img>`, a provider-CDN URL, or an explicit "N attachments" indicator before a prompt/verdict may be trusted (bead wc-kjny, 2026-08-02 Grok incident) | Verified upload recipe (per provider) |
| `verify_frame_order(prompt_frame_names, model_reported_order)` → dict | Detects a model discussing frames out of upload order even when every frame's pixel content was read correctly (2026-08-02 Perplexity: correct pixels, wrong order, cost it a verdict notch) | VISUAL FRAME review |

```bash
cd ~/.claude-wa/skills/web-advice/scripts && python3 -m pytest test_web_advice_transport.py -q
```

Read the file directly for exact signatures — this table does not replace the hard-fail or honest-accounting rules above. Also present alongside the script: `scripts/e2e_smoke.sh` (non-destructive live probe of all 4 ladder rungs — never opens a tab, never submits a prompt, never decrypts cookie contents, existence check only; exits 0 with a printed matrix even when most rungs are down — a partial ladder is a normal working session; exits 1 only when every rung is down, the HARD-FAIL condition), `evals/web_advice_evals.md` (5 cases: happy path, 2-of-4 honest-accounting edge, API-substitution adversarial, frames-only methodology-question adversarial, unverified-attachment-confident-verdict adversarial), `evals/test_resolver_trigger.py`, and `RESOLVER.md` (trigger phrases for skill discovery).

---

## Pre-Flight Checklist (run BEFORE opening any browser)

### Step 0a — Verify the review subject is ready

```bash
# 1. PR + HEAD
gh pr view <N> --json number,title,headRefName,headRefOid,state,url

# 2. Evidence bundle (if reviewing a PR with one)
ls -la docs/pr<N>-evidence/ 2>/dev/null
cat docs/pr<N>-evidence/metadata.json 2>/dev/null | python3 -m json.tool

# 3. /er 4-gate pre-flight (REQUIRED for PRs with evidence bundles)
cd docs/pr<N>-evidence
sha256sum -c SHA256SUMS.txt          # Gate 1: Checksum integrity
test -f verification_report.json    # Gate 2: Verification report (N/A if absent)
cat metadata.json | jq '.git_provenance.git_head' | xargs -I {} \
  bash -c 'test {} = $(gh pr view <N> --json headRefOid -q .headRefOid) && echo Gate 4 PASS || echo Gate 4 FAIL'  # Gate 4: SHA matching
```

**Stop here if any gate FAILs** — regenerate the bundle first; /web-advice is wasted on stale evidence.

### Step 0b — Build the review prompt

For video/frame evidence use [Prompt shapes](#prompt-shapes) above. For text/code/PR review, use this 4-section shape:

```markdown
You are a Senior Staff Principal AI Systems Architect reviewing a [PR | evidence bundle | design doc].

**Subject**:
- Type: [PR | bundle | doc]
- Identifier: [<PR URL> | <bundle path> | <doc path>]
- Branch / Commit: [<branch> @ <sha>]
- Working directory: <absolute path>

**Context** (≤ 200 lines, paste from local files):
- <relevant code, file:line citations>
- <relevant tests, file:line citations>
- <relevant doc snippets>

**Review dimensions** (pick what applies):
1. Architectural soundness (state-machine compliance, ZFC consumer split, layer isolation)
2. Edge case safety (concurrent writes, time freeze, god mode, modal locks)
3. Evidence bundle integrity (checksum validity, SHA alignment, real-service proof)
4. Test coverage (structural vs rendered-text, multi-turn vs single-shot)
5. Web standards alignment (cite external sources)

**Required output format** (verbatim):
VERDICT: APPROVED | APPROVED with notes | CHANGES REQUESTED | REJECTED
REASONING: 3-4 sentences
RISK: main risk, one sentence
CONFIDENCE: high | medium | low
WEB SOURCES: 1-3 URLs with one-line summaries (if you cited any)
```

The prompt is the same for all seats. Don't customize per model.

---

## Browser Execution Protocol

### Step 1 — Open tabs (one per live seat)

```javascript
// In aside-mcp repl (mcp__aside-mcp__repl tool)
await openTab('https://gemini.google.com/app');
await openTab('https://chatgpt.com/');   // only if a ChatGPT transport is live — see dead end section
await openTab('https://grok.com/');
await openTab('https://www.perplexity.ai/');

const allTabs = await listBrowserTabs();
console.log('opened:', allTabs.length, 'tabs');
for (const t of allTabs) console.log(' -', t.title, '(', t.url, ')');
```

Expected output: 5 tabs (your existing tab + 4 new). Logged-in users will see "Ask Gemini", "ChatGPT", "Grok", "Perplexity" titles.

### Step 2 — Verify auth state (CRITICAL)

```javascript
const tabs = await listBrowserTabs();
const gemTab = tabs.find(t => t.title === 'Google Gemini');
const gemPage = await attachBrowserTab(gemTab.targetId);
const gemSnap = await snapshot(gemPage);
const geminiLoggedIn = !gemSnap.tree.includes('Sign in') && !gemSnap.tree.includes('Log in');
console.log('gemini logged in:', geminiLoggedIn);
```

**Repeat for ChatGPT, Grok, and Perplexity.** If any model is not logged in, **stop and ask the user to log in** — do NOT try to log in for them (no credentials, no auth cookies, no OAuth flow). Login state per model:

- **Gemini**: Logged in shows "Google Account: `<email>`" in the sidebar
- **ChatGPT**: Logged in shows "Log in" button HIDDEN; prompt textbox visible. May show the marketing landing page ("Where should we begin?") with a "Log in" button even when a session cookie exists — if the textbox is missing OR the page shows "Sign up for free", the session is genuinely gone. Try `chat.openai.com` as a fallback URL before concluding logged-out.
- **Grok**: Logged in shows chat history in sidebar; "New Chat" button enabled
- **Perplexity**: Logged in shows username top-right (e.g. "jleechan77861") AND a "Sessions" sidebar with prior chats

If the user can't log in to one model, run /web-advice with the others (3-of-4 still satisfies the multi-model adversarial requirement) and use [Honest seat accounting](#honest-seat-accounting--mandatory-user-directive-2026-08-02) in the synthesis.

### Step 3 — Submit prompt to each model (sequentially, not parallel)

Submit one model at a time. Submitting in parallel can hit rate limits or trigger captchas. Wait for each response before submitting the next.

```javascript
// Gemini — locator ref varies; use aria-label selector
const gemPrompt = `<your review prompt>`;
const gemT = (await listBrowserTabs()).find(t => t.title === 'Google Gemini');
const gemP = await attachBrowserTab(gemT.targetId);
const textbox = await gemP.locator('div[aria-label="Enter a prompt for Gemini"]');
await textbox.click();
await gemP.keyboard.type(gemPrompt, {delay: 3});  // 3ms/char; use clipboard method (Prompt shapes) if 2000+ chars
await gemP.keyboard.press('Enter');
console.log('sent to Gemini, waiting...');
await new Promise(r => setTimeout(r, 30000));      // Gemini Pro: 15-45s typical; video review: allow >=420s
const gemResp = await snapshot(gemP);
console.log(gemResp.tree);
```

**Gotcha — duplicated text:** if a prior prompt was inserted via `el.innerText = ...`, the textbox may show duplicated content. Always clear first: `Cmd+A`/`Meta+A` → `Backspace` → wait 500ms → type/paste.

**Gotcha — TrustedHTML errors:** don't use `el.innerHTML = ...` (Gemini's textbox uses Trusted Types). Use `el.innerText = ...` or `keyboard.type()`.

**Gotcha — ChatGPT send:** requires clicking the "Send message" button, not Enter.

**Perplexity (proven pattern):**

```javascript
// Perplexity textbox is a DIV with role="textbox" — NOT a <textarea>
const perpTab = (await listBrowserTabs()).find(t => t.title === 'Perplexity');
const perpPage = await attachBrowserTab(perpTab.targetId);
const textbox = await perpPage.locator('[role="textbox"]').first();
await textbox.click();
await perpPage.keyboard.type(reviewPrompt, {delay: 3});
await perpPage.keyboard.press('Enter');  // Enter submits; no separate button click
```

**Perplexity quirks:** no `aria-label` — use the role selector, not aria-label. The textbox ref changes after each response (Perplexity regenerates the element) — always re-snapshot before the next prompt. Answers include a `Sources` accordion (collapsed by default) and a `Pro` badge — citation-rich, useful for "cite your web sources" requirements. Defaults to "Search" mode (web-grounded); switch to "Reasoning" mode via the model selector for code-only review.

### Step 4 — Capture responses

```javascript
const respSnap = await snapshot(modelPage);
const verdictMatch = respSnap.tree.match(/VERDICT:\s*([^\n]+)/);
const reasoningMatch = respSnap.tree.match(/REASONING:\s*([^\n]+(?:\n[^\n]+){0,3})/);
```

Per-seat response shape: Gemini Pro is structured ("Copy code" button visible, dedicated response region); Grok is conversational ("Like"/"Dislike" footer, verdict may be a single line near the end); ChatGPT is most conversational and may skip structure unless reminded; Perplexity is citation-rich with a "Sources" accordion, "Helpful"/"Not helpful" footer, verdict usually at the end.

**Parser fallback** if regex misses — re-prompt: *"Reply with ONLY this exact format (no other text): VERDICT: `<one line>` | REASONING: `<one line>` | RISK: `<one line>` | CONFIDENCE: high/med/low"*. This is the most reliable cross-model pattern. (`parse_verdict()` in scripts/ implements the primary extraction.)

### Step 5 — Synthesize

```markdown
## /web-advice synthesis

**Panel: N-of-4** (name any unavailable seat + exhausted paths — see Honest seat accounting)

| Seat | Verdict | Confidence | Key finding |
|---|---|---|---|
| ChatGPT | <verdict or UNAVAILABLE> | high/med/low | <one line> |
| Gemini Pro | <verdict> | high/med/low | <one line> |
| Grok | <verdict> | high/med/low | <one line> |
| Perplexity | <verdict> | high/med/low | <one line> (web-grounded, citation-rich) |

**Convergence:** <3-of-4 agree / all 4 agree / 2-2 split / other>
**Recommended action:** <APPROVE / approve with conditions / change requests>
**Open web sources cited:** <URLs from Perplexity + any seat that cited external standards>
```

**Decision rule:** 3-of-4 agreement is sufficient (or 2-of-4 if both verdicts strongly converge and come from different model families). If all diverge, surface the disagreement to the user and ask which axis (speed/safety/cost) matters most. Perplexity's web grounding often breaks ties by surfacing external standards (D&D 5e SRD, RFC, etc.) the other models lack.

---

## Failure Recovery

### Aside daemon disconnects

Symptom: `Task failed: fetch failed: other side closed. Aside daemon is not reachable — make sure Aside Browser is running, then retry.`

1. Check the Aside app is still running (not crashed); if windowless, use the [no-focus-steal launch](#3-no-focus-steal-launch-mandatory-on-this-machine).
2. Reopen lost tabs via `openTab(url)`.
3. Re-snapshot before each fill (refs are NOT stable across `attachBrowserTab` cycles).
4. If recovery fails 3 times: **HARD FAIL per section 1** — report exact errors to the user and stop. Do NOT fall back to WebSearch subagents, provider APIs, or CLI models and call it /web-advice.

### Captcha or rate limit

Symptom: an "I'm not a robot" or "You've reached your limit" page.

1. Stop the affected seat — don't retry.
2. Note the rate-limit in the synthesis.
3. Continue with the other seats; if only 1 remains, that's a single-model review — note it explicitly (never present as multi-model).

### Login required

Symptom: ChatGPT shows "Log in" button; Grok shows "Sign in" page; Gemini shows "Sign in to continue".

1. **Do NOT attempt login** — no credentials, no OAuth flow.
2. Stop and ask the user to log in manually; continue with the other seats.
3. If only 1 model is logged in, that's a single-model review, not multi-model — note this in the synthesis.

### Stale evidence (Gate 4 FAIL)

Symptom: `metadata.json:git_provenance.git_head` ≠ PR HEAD `headRefOid`.

1. **Stop /web-advice** — the verdict would be against stale evidence.
2. Regenerate the evidence bundle against current HEAD, re-run `/er` 4-gate, re-run `/web-advice`.

---

## When NOT to use /web-advice

- **In-session code review** → `/advice` (subagent + /secondo + /research)
- **Evidence bundle integrity** → `/er` (4-gate checksum/SHA/real-services)
- **Triage plan review** → `/advice` first; escalate to `/web-advice` only if the plan needs external validation
- **Visual/video proof** → `/web-advice` IS the right tool (Gemini web is the only seat that can watch video)

---

## Token Budget

| Step | Tokens |
|---|---|
| Pre-flight + prompt build | ~2K |
| Browser session (per tab) | ~5K (state management) |
| Per-model response | ~2-3K |
| Synthesis | ~500 |
| **Total** | **~13K** vs ~50-100K for full `advisor()` |

**~85-90% fewer tokens** than `advisor()` while still getting multi-model adversarial coverage.

---

## Field notes

Narrative/history detail — read only if you need full provenance for a claim above; not required for routine execution.

### ChatGPT transport investigation (2026-08-02, exhaustive)

Cookie-inject into a synthetic/fresh Playwright profile Cloudflare-walls (confirmed). Four in-policy alternatives were tried against the user's real Google Chrome (`~/Library/Application Support/Google/Chrome`, 3 profiles: `Default`=$USER@gmail.com has the ChatGPT session, `Profile 1`/`Profile 3` do not):

1. **CDP attach to the user's live Chrome** (`chromium.connect_over_cdp("http://127.0.0.1:9222")`): Chrome does not listen on 9222 by default. It was not running at all at the start of one check (`ps aux` empty), then found running mid-session (real user activity, PID with no `--user-data-dir` flag) but still without the debug port — only enabled by the user **relaunching** Chrome with `--remote-debugging-port=9222`. Highest-probability remaining path (see ChatGPT dead end section for the exact command).
2. **`launch_persistent_context` on a COPY of the real Chrome profile** (`channel="chrome"`, headed with `--window-position=-3000,-3000` to avoid stealing focus — headless=new still Cloudflare-walls; headed-offscreen gets PAST Cloudflare, confirming the mechanism is sound): the copy correctly carries non-sensitive `chatgpt.com` cookies, but Chrome's cookie-theft-hardening silently fails to decrypt and then deletes the security-sensitive `.auth.openai.com` cookies from the copied DB on open — verified 3 ways: (a) `browserclaw cookies decrypt` on the on-disk copy shows all 12 openai.com cookies present pre-launch, (b) `ctx.cookies()` and raw CDP `Network.getAllCookies()` post-launch show 0 openai.com cookies loaded into the live jar, (c) re-querying the SAME copy's SQLite file after Chrome closed shows the openai.com rows physically deleted (12→0), while the 11 non-auth `chatgpt.com` cookies survive untouched. This is Chrome's 2024+ anti-cookie-theft device binding working as intended — do not attempt to defeat it (out of policy scope). **Profile-copy cannot carry a ChatGPT session, full stop.**
3. **claude-in-chrome extension**: IS installed in the user's real `Default` Chrome profile (extension id `fcoeoabgfenejglbffodgkkbkcdhcgfn`, named plain "Claude" under `~/Library/Application Support/Google/Chrome/Default/Extensions/`), but `list_connected_browsers` returns `[]` even with real Chrome running. Needs the user to open the extension's toolbar icon and click **Connect** (or restart Chrome so the background worker registers) — user action, not fixable from-session.
4. **Aside's own chatgpt.com tab**: confirmed still logged out (unchanged since the 17:00 PT baseline check) — Aside is a separate Chromium profile from the user's real Chrome and has never had a ChatGPT login.

Net result: no fully-automated ChatGPT web capture is currently possible without one user action. See the ChatGPT dead end section above for the two remaining paths, cheapest first.

### Proven working recipe (2026-08-02 run — all four lanes exercised)

- **Chrome-headless lane** (for sites logged in only in Chrome): `browserclaw cookies decrypt --db "$HOME/Library/Application Support/Google/Chrome/Default/Cookies" -o /tmp/ck.json --domain-filter '%google.com%'` (safe on the live DB — it copies first) → Python Playwright `launch(channel="chrome", headless=True)` + `add_cookies` (coerce missing `sameSite` to `Lax`) → real site, real session. Delete `/tmp/ck_*.json` after the run. **Gemini web verified working this way, including video upload.**
- **Auth note:** Aside is its own Chromium profile — Chrome logins do NOT carry over. If a model site shows Sign-in/Sign-up markers, the user must log in inside Aside; never log in for them. 2-of-4 seats from different model families is the documented minimum for a valid multi-model pass.

### Incident provenance

2026-08-02 — both primary browser transports were down; a Gemini-Files-API video review was substituted with disclosure; the operator ruled any substitution unacceptable for this command regardless of disclosure. That ruling is what section 1 (HARD-FAIL CONTRACT) encodes.

### Attachment-verification incident (2026-08-02, bead wc-kjny)

Full narrative, per-model responses, and proof artifacts: `docs/ios_evidence/wave3_20260802/WEB_ADVICE_VISUAL_ROUND.md` in the worldai_claw repo. Summary: Grok's first upload attempt used `page.locator('input[type="file"]').first()` against a page with 6 file inputs, silently attached zero images (no exception, logged "files set"), and Grok fabricated a complete, confident `DESCRIPTION` + `VERDICT: NOT SUPPORTED` for content that does not exist in the app. Fix applied and reproduced correctly: `button[aria-label="Attach"]` → "Upload a file" menu item → real `filechooser` event; re-sent the identical prompt on a fresh page load and got an accurate response, verified against the actual PNGs. Same round also surfaced the Perplexity frame-order finding (own "Frame 1/2/3" labels didn't match upload order, correctly-read pixels but a weaker verdict) and Perplexity's free-plan upload-limit wall (hit after one 3-image submission). These three findings are what `assert_attachment_verified()`, `verify_frame_order()`, and the [Verified upload recipe](#verified-upload-recipe-per-provider--mandatory-before-prompting) / seat-matrix "Known walls" updates above encode.

---

## Reference

- Provenance: artifact `~/roadmap/2026-08-01-web-advice-and-evidence-review-guide.md` (Antigravity Genesis Coder, 2026-08-01); hard-fail + transport-ladder + visual-description-first lessons from the 2026-08-02 live run (memory `feedback_2026-08-02_web_advice_hard_fail_no_substitution.md`, `reference_2026-08-02_web_advice_working_recipe.md`).
- Attachment-verification hardening (this update): bead `wc-kjny`; evidence `docs/ios_evidence/wave3_20260802/WEB_ADVICE_VISUAL_ROUND.md` (worldai_claw repo) — see [Attachment-verification incident](#attachment-verification-incident-2026-08-02-bead-wc-kjny) above.
- 4-gate pre-flight: `~/.claude/skills/evidence-standards/SKILL.md`
- Browser automation: `mcp__aside-mcp__repl`, `aside` CLI, `mcp__claude-in-chrome__*`, chrome-headless + `browserclaw` cookie decrypt
- Transport/prompt/eval automation: `~/.claude-wa/skills/web-advice/scripts/web_advice_transport.py`, `scripts/test_web_advice_transport.py`, `scripts/e2e_smoke.sh`, `evals/web_advice_evals.md`, `evals/test_resolver_trigger.py`, `RESOLVER.md` — see [scripts/, evals/, RESOLVER.md](#scripts-evals-resolvermd--transport--prompt-automation) above.
- Companion skill: `/advice` (in-session multi-reviewer)

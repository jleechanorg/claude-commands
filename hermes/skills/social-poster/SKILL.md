---
name: social-poster
version: 0.1.0
description: |
  Draft social-media posts for LinkedIn, Hacker News, Twitter/X, Reddit, Threads,
  Facebook, Instagram, Mastodon, Bluesky, and Dev.to. Each draft is staged in an
  Aside browser tab (signed-in persistent session), screenshotted, and surfaced
  for human review. Posts ONLY go live after the user types "POST APPROVED"
  (per-platform allowed: "POST APPROVED linkedin,hackernews"). Pure draft mode by
  default — no LLM augmentation, no auto-post, no exceptions.
when_to_use: |
  Use when the user asks to draft a post for any social platform, share a project
  on LinkedIn/HN/Twitter, post to Reddit, prepare a Show HN, draft an Instagram
  caption, or any "draft a post" / "post to <platform>" / "share on social" /
  "/social <intent>" request. Also fires on "/social <intent>" slash command.
allowed-tools:
  - Read
  - Write
  - Bash
  - Edit
  - Grep
triggers:
  - "draft a social post"
  - "draft a post"
  - "post to social"
  - "post to linkedin"
  - "post to hacker news"
  - "post to reddit"
  - "post to twitter"
  - "post to threads"
  - "post to facebook"
  - "post to instagram"
  - "draft linkedin post"
  - "draft hacker news post"
  - "draft reddit post"
  - "draft tweet"
  - "draft twitter thread"
  - "draft instagram caption"
  - "draft threads post"
  - "show hn"
  - "social poster"
  - "/social"
context: inline
---

# Social Poster — Draft-Only, POST APPROVED Gated

## Contract

1. **Draft, never post** — default mode produces text files + browser-staged tabs + screenshots. No network mutation without explicit `POST APPROVED`.
2. **Persistent browser session** — uses `aside` CLI (signed into $USER@gmail.com) to keep one session across multiple platform tabs; never spawns a fresh Playwright Chromium per platform.
3. **Per-platform conformance** — character limits, title rules, hashtag placement, threading, self-promo ratios checked at draft time (no "fix it after posting").
4. **Reddit 10/90 + per-sub rules** — every Reddit draft is checked against the live-verified rules in `references/subreddit-rules.md` (r/LocalLLaMA, r/Rag, r/OpenAI verified via Aside probe 2026-07-05).
5. **POST APPROVED token** — `scripts/post_approved.py` checks for literal `POST APPROVED` (or per-platform like `POST APPROVED linkedin,hackernews`) before clicking any submit button. Without the token, exits code 2 with "BLOCKED — no POST APPROVED token".
6. **No LLM augmentation by default** — pure templating. To enable LLM refinement, pass `--use-llm` (which routes through your existing `~/.hermes/config.yaml` auxiliary provider; never hardcodes API keys).

## Supported Platforms

| Platform | Template | Has web compose? | Notes |
|----------|----------|------------------|-------|
| LinkedIn | `templates/linkedin.md` | ✅ | long-form + 300-char short variant |
| Hacker News | `templates/hackernews.md` | ✅ | "Show HN:" prefix when self-promo; title ≤80 chars |
| Twitter/X | `templates/twitter.md` | ✅ | single tweet + thread; hashtags at end of last tweet only |
| Reddit | `templates/reddit.md` | ✅ | one file per subreddit; text-post preferred over link-post |
| Threads | `templates/threads.md` | ✅ | ≤500 chars, casual |
| Facebook | `templates/facebook.md` | ✅ | medium-length, link-friendly |
| Instagram | `templates/instagram.md` | ⚠️ no web compose | caption + 30-hashtag block; surfaces mobile instructions |
| Mastodon | `templates/mastodon.md` | ✅ | 500-char default; configurable instance |
| Dev.to | `templates/devto.md` | ✅ | markdown article format |

## Phases

### Phase 1 — Draft (deterministic, no browser)

Run `scripts/draft_social_post.py` with intent + key-points + link + platforms. Produces per-platform files in `--out <dir>`. Character-limit hard-rejects; spam-rule soft-warns.

```bash
PY=$HOME/.hermes/skills/social-poster/scripts/draft_social_post.py
python3 "$PY" \
  --intent "announce jleechanclaw open-source release" \
  --key-points "AI agent orchestration, hermes deploy pipeline, skill framework" \
  --link "https://github.com/jleechanorg/jleechanclaw" \
  --platforms linkedin,hackernews,twitter,reddit,threads,facebook,instagram,mastodon,devto \
  --reddit-subs "LocalLLaMA,Rag,OpenAI" \
  --image "" \
  --out /tmp/drafts/social-2026-07-06/
```

Output: one `.md` file per platform (or per subreddit for Reddit). Filename-safe slugs.

### Phase 2 — Stage in Aside (browser, no auto-post)

Run `scripts/stage_in_aside.py` (uses `aside repl`):

```bash
PY=$HOME/.hermes/skills/social-poster/scripts/stage_in_aside.py
python3 "$PY" --drafts /tmp/drafts/social-2026-07-06/
```

For each platform:
1. Opens a new Aside tab on the platform's compose URL.
2. Pastes the draft into the compose field (no submit).
3. Screenshots → `/tmp/drafts/social-2026-07-06/screenshots/<platform>.png`.
4. Leaves the tab open for human inspection (or closes if `--close-tabs` flag).

**Aside recipes** for each platform's compose URL live in `references/aside-recipes.md`.

### Phase 3 — Surface to user

Print all draft file paths + screenshot paths. Attach screenshots via Slack `MEDIA:/path` (per `evidence-attach-to-slack` skill). Ask: *"POST APPROVED?"*

### Phase 4 — Post (gated)

ONLY after the user types `POST APPROVED` (literal, case-insensitive, optionally with comma-separated platform allowlist), run:

```bash
PY=$HOME/.hermes/skills/social-poster/scripts/post_approved.py
python3 "$PY" \
  --drafts /tmp/drafts/social-2026-07-06/ \
  --approval-token "POST APPROVED" \
  [--platforms linkedin,hackernews]  # if omitted, posts all staged
```

Behavior per platform:
- LinkedIn / HN / Twitter / Reddit / Threads / Facebook / Mastodon / Dev.to → click submit, capture post-URL.
- Instagram → surface draft caption as text + print mobile instructions (no web compose). Manual copy-paste from phone.

Posting log written to `--drafts/posted.json` with timestamps + captured URLs.

## Safety Gates

1. **`POST APPROVED` required** — see `scripts/post_approved.py` `check_approval()` function. Hard exit 2 if missing.
2. **`--dry-run`** — default behavior of `post_approved.py` if invoked without an approval token. Prints staged tabs and exits.
3. **Per-platform allowlist** — `POST APPROVED linkedin` only posts LinkedIn. Comma-separated = OR. Default = all staged platforms.
4. **No silent failures** — any platform that fails to post writes to `posted.json` with `{"status": "failed", "error": "..."}`. User is notified.
5. **Audit log** — every draft run writes `--out/manifest.json` with timestamp, intent, platforms, character counts, spam-rule warnings.

## Subreddit Selection (verified 2026-07-05)

| Content type | Primary | Secondary | Tertiary |
|---|---|---|---|
| Open-source / local AI tool | r/LocalLLaMA | r/OpenSourceAI | r/singularity (opinion-only) |
| RAG / retrieval / vector DB | r/Rag | r/LocalLLaMA | — |
| Coding agent / dev tool | r/OpenAI (text post) | r/LocalLLaMA | — |
| General AI news / opinion | r/OpenAI | r/LocalLLaMA | r/ClaudeAI (Claude-specific) |

**Banned / avoid:**
- r/AItools, r/AutoGen, r/LMStudio → banned subs.
- r/singularity, r/AGI, r/Futurism, r/MachineLearning → zero self-promo.
- r/philosophy, r/ProgrammerHumor → AI content banned outright.

## Anti-Patterns

- ❌ Auto-posting without `POST APPROVED` (bypasses the safety gate)
- ❌ Using `mcp__playwright-mcp__*` for localhost testing — use `aside` (signed-in session)
- ❌ Calling `aside show_browser` / headed mode without explicit opt-in (headless-only default)
- ❌ Hardcoding API keys in `draft_social_post.py` (LLM augmentation must route through `~/.hermes/config.yaml`)
- ❌ Stripping 10/90 framing from Reddit drafts ("I built this, here's the link") — guarantees removal
- ❌ Posting the same draft verbatim across Reddit subs (each sub has different norms; per-sub files required)
- ❌ Posting link-only to r/OpenAI — requires text post + context (verified rule)
- ❌ Clicking submit in Phase 2 (stage-only)

## Output Format

After Phase 3, the skill reply includes:

```
## social-poster draft ready

- Drafted: 9 platforms (linkedin, hackernews, twitter, reddit x3, threads, facebook, instagram, mastodon, devto)
- Staged: 9 Aside tabs open (URLs: …)
- Screenshots: /tmp/drafts/social-2026-07-06/screenshots/ (9 PNGs)
- Manifest: /tmp/drafts/social-2026-07-06/manifest.json

**To post:** reply with `POST APPROVED` (all) or `POST APPROVED <platforms>`.
**To revise:** tell me what to change and I'll re-draft + re-stage.
```

Screenshots attached via `MEDIA:/path/to/png` for inline Slack preview.

## Trigger → Action Map

| User says | Action |
|-----------|--------|
| `draft a post about X` | Phase 1 only |
| `draft + stage a post about X` | Phase 1 + Phase 2 |
| `POST APPROVED` | Phase 4 (all staged) |
| `POST APPROVED linkedin,twitter` | Phase 4 (only those two) |
| `revise the linkedin draft` | Re-run Phase 1 + Phase 2 for that platform only |
| `cancel drafts` | Close Aside tabs, keep files |

## Files

- `scripts/draft_social_post.py` — deterministic drafter
- `scripts/stage_in_aside.py` — opens Aside tabs + screenshots (uses `aside repl` + `annotatedScreenshot`)
- `scripts/cookie_inject_and_stage.py` — uses `browserclaw cookies decrypt` + Playwright Chrome with injected cookies to stage + paste drafts (for platforms where Aside is not signed in)
- `scripts/post_approved.py` — gated publisher
- `templates/*.md` — 9 platform templates
- `references/subreddit-rules.md` — live-verified per-sub rules
- `references/platform-character-limits.md` — hard limits + soft guidance
- `references/aside-recipes.md` — `aside repl` snippets per platform
- `references/platform-session-status.md` — per-platform cookie injection + anti-bot results (verified 2026-07-05). **Playwright Chrome only — see `aside-repl-session-state.md` for `aside repl`-based staging.**
- `references/blog-post-to-gdoc.md` — recipe for "draft a blog post in Google Docs" (canonical `gws docs` path + local-markdown fallback when gws OAuth is unauthenticated).
- `references/aside-repl-session-state.md` — verified auth state per platform for `aside repl` workflows (2026-07-06). Includes the `listBrowserTabs()` live-tab probe recipe, the `document` scope-doesn't-persist-across-REPL-calls pitfall, and per-platform paste workarounds for LinkedIn contentEditable / Facebook click-first / Twitter thread pagination.
- `references/aside-repl-playwright-pattern.md` — verified `openTab()` returns a Playwright `Page` object with `screenshot()` (Buffer→base64), `evaluate()`, `locator()`, `frameLocator()`. Includes 6 working paste/click/inspect idioms. Source of truth for the 2026-07-06 staging rewrite.
- `tests/test_*.py` — unit + integration tests

## Critical lessons (from real sessions, not theoretical)

1. **`aside account list` does NOT show per-platform auth state.** It only shows the active Google account ID. To gauge whether LinkedIn/Twitter/Facebook/etc. are actually signed in, run `aside repl "const tabs = await listBrowserTabs(); console.log(tabs.map(t => t.url).join(' | '))"`. A signed-in tab on the platform = the session is valid, even if a fresh `openTab(compose-url)` shows a login wall (compose-URL navigation may trigger session re-auth).

2. **`document` scope does NOT persist across `aside repl` calls.** Each call gets a fresh JS context. Multi-step workflows (open → click → paste → verify) must be bundled in ONE async IIFE in a single call. Screenshot via `annotatedScreenshot(pageObj)` returned from `openTab()`, not `annotatedScreenshot(null)`.

3. **Programmatic paste into LinkedIn/Twitter/Facebook compose modals is unreliable.** Twitter's textarea + React setter trick works in a single bundled call. LinkedIn's contentEditable div + `el.innerHTML = text` works but React state may not sync (manual paste is more reliable). Facebook requires click-first on "What's on your mind, [Name]?" before the modal opens. **Default workflow: stage + screenshot the empty compose area, let the user paste manually.** This avoids the React control gymnastics entirely and the user still gets visual proof the compose UI is loaded.

4. **`POST APPROVED` is mandatory for any submit/click-post action.** Drafts may be staged freely. Posting requires the literal `POST APPROVED` string (optionally with comma-separated platform allowlist). No exceptions, no "looks approved" heuristics. See `scripts/post_approved.py` `check_approval()` for the gate logic.

5. **`aside session` ≠ `account list` ≠ Chrome cookie DB.** The source of truth is `listBrowserTabs()`. If the user says "I'm signed in to LinkedIn", verify with that probe before declaring a platform unreachable.

6. **`openTab(url)` returns a Playwright `Page` object**, not a serializable tab descriptor. Use `p.screenshot()` directly (returns a Buffer that base64-encodes for stdout), or `p.locator(...)` / `p.evaluate(() => ...)` for DOM ops. `annotatedScreenshot(null)` throws `Cannot read properties of null (reading 'snapshot')`; `annotatedScreenshot(pageObj)` works but `p.screenshot()` is simpler. See `references/aside-repl-playwright-pattern.md` for the verified idioms.

7. **Reddit compose URL must end in `?selftext=true`.** `https://old.reddit.com/r/<sub>/submit` lands on the link-post form by default, which navigates through the "link vs text" tab UI and triggers a session re-auth redirect. The `?selftext=true` param lands directly on the text-post form with title (textarea[name="title"]) + body (textarea[name="text"]) fields visible. `stage_in_aside.py`'s compose URL for Reddit MUST include this param. Verified 2026-07-06 for r/LocalLLaMA, r/OpenAI, r/Rag — all three compose forms loaded immediately with no auth redirect when the `?selftext=true` suffix was used.

8. **Vision-verify compose-vs-login, don't DOM-detect.** A DOM-only check like `document.querySelector('input[name="title"]')` can give false negatives if the page is still loading. The deterministic check is `p.screenshot()` → save → `vision_analyze(image_url, "Is the compose form for posting to r/X visible, with title input and body textarea? Or is it a login wall?")`. The user said "Many of these screenshots are login screens I wanna find the draft post screen / Still not good enough" on 2026-07-06 — the lesson: ALWAYS confirm by vision, never trust URL or DOM-only state when the user wants visual proof.

9. **Aside daemon restart = sessions break.** If `aside repl` returns "fetch failed" and you `pkill -f AsideDaemon` to recover, all open tabs are lost. Subsequent `openTab()` calls hit login walls even though the underlying Chrome cookie DB still has valid sessions, because Aside's tab-object state is gone. `listBrowserTabs()` returns `TOTAL_TABS 1` (a single fresh tab) instead of the prior 17-tab state. **Fix:** instead of `pkill`, try `open -a "Aside"` first — sometimes the daemon recovers without losing tabs. If you must restart, plan for a sign-in re-pass on platforms that were "previously signed in."
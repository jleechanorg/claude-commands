# Worked Example: Fable AI 2D-Game Post (2026-07-11)

Reference run for **commentary/opinion** drafts (NOT project announcements). When the source is a LinkedIn URL describing a third-party capability + personal reaction (e.g. "Fable one-shot a 2D game from my text sim"), the templating pipeline hallucinates the wrong subject. Hand-author the drafts.

## Source

LinkedIn URL: `https://www.linkedin.com/posts/jeffrey-lee-chan_1-to-all-the-twitter-2d-game-hype-just-share-7481840760233848832-eWW-/`

Extracted via `curl -A Chrome ... <url>` + Python regex on `<meta property="og:description">`. The og:description had the full post body embedded.

## What the templater got wrong

First run with `intent="Fable AI oneshot a 2D game prototype from my text-based AI D&D world simulator..."` produced drafts that:

- Used "jleechanclaw" as the project name (the user's open-source harness) instead of "Fable" (the third-party model being discussed)
- Stuffed every key-point into bullet lists under "what we built" instead of weaving them into the personal commentary voice
- Generated the wrong CTA (open-source repo link) instead of the right CTA (prototype video at lnkd.in/gEAxhum9)

Root cause: the template treats every intent as "announce a project." When the intent is "share my reaction to someone else's capability," the template needs a different shape — no `## What it does`, no `## Stack`, no `## Repo:`. Just a personal-voice commentary that links to the source.

## What worked

Hand-authoring all 13 `.md` files in `/tmp/drafts/fable-2d-game-2026-07-11/` using the actual post body as the source. Each platform got a tailored take:

| Platform | Approach |
|---|---|
| LinkedIn | Personal voice, hook in first 210 chars, link to prototype video + your-project.com |
| Hacker News | Show HN format, focus on the eval methodology (same prompt, every model release, for 18 months) |
| Twitter/X | Single tweet + 5-tweet thread; hashtags only in final tweet |
| Threads | Casual, single paragraph |
| Facebook | Long-form personal, same as LinkedIn but no hashtag discipline |
| Instagram | Caption + 30 hashtags; no web compose, surface for mobile |
| Mastodon | Short, single paragraph |
| Dev.to | Markdown article with comparison table of all 5 models tested |
| r/LocalLLaMA | Technical depth + comparison table + "open question" framing for benchmark gap |
| r/OpenAI | OpenAI-family-specific angle: how GPT-4 family failed this eval |
| r/ClaudeAI | Claude-specific angle: 3.7 Sonnet was best Claude, still didn't pass |
| r/MachineLearning | Research-grade framing with full model table + reproducibility offer |
| r/singularity | Brief — observation, not announcement |

## Vision-verify results (2026-07-11)

| Platform | DOM-detect verdict | Vision verdict | Actual state |
|---|---|---|---|
| Hacker News | compose-ready | compose-ready | ✅ /submit form, signed in |
| Twitter/X | compose-ready | compose-ready | ✅ compose modal, @jleechan2015 |
| Reddit r/LocalLLaMA | compose-ready | compose-ready | ✅ /submit?selftext=true form, signed in |
| Reddit r/OpenAI | compose-ready | compose-ready | ✅ /submit?selftext=true form, signed in |
| Reddit r/ClaudeAI | compose-ready | compose-ready | ✅ /submit?selftext=true form, signed in |
| Reddit r/MachineLearning | compose-ready | compose-ready | ✅ /submit?selftext=true form, signed in |
| Reddit r/singularity | compose-ready | compose-ready | ✅ /submit?selftext=true form, signed in |
| LinkedIn | login-wall | login-wall | ❌ "Welcome back" + Google One-Tap unblock visible |
| Dev.to | login-wall | login-wall | ❌ 6 OAuth options, no session |
| Threads | login-wall | login-wall | ❌ Instagram login wall |
| Facebook | login-wall | login-wall | ❌ Login wall, Adblock Plus overlay |
| Mastodon | login-wall | login-wall | ❌ Publish editor visible but not signed in |

**Compose-ready ≠ Paste-stuck.** Even on the 7 platforms with confirmed compose-ready vision state, programmatic paste via React setter did NOT stick in the field. The form was loaded but the textarea was empty when vision-checked post-paste. User had to paste manually from the `.md` files.

## Recommended workflow for future commentary/opinion runs

1. Extract the source URL body (LinkedIn og:description, Twitter card meta, etc.) — use curl + Python regex, NOT `web_extract` (DuckDuckGo backend refused to extract LinkedIn URLs on 2026-07-11; `ddgs is search-only`).
2. Run `draft_social_post.py` once to scaffold the directory + manifest, but READ every generated `.md` file. If templating misfires (hallucinated project name, wrong CTA, stuffed bullets), hand-author the drafts directly into the same files.
3. Run `stage_in_aside.py` to open tabs + screenshot. Vision-verify AT LEAST ONE compose-ready screenshot per platform to confirm the form loaded.
4. Do NOT trust programmatic paste. Tell the user the drafts are in `/tmp/drafts/<run>/<platform>.md` and the compose tabs are open — they'll paste manually.
5. Surface 3 next-step options:
   - Sign in to login-walled platforms (LinkedIn Google One-Tap is the cheapest — 1 click)
   - POST APPROVED the compose-ready ones (after manual paste)
   - Revise any draft

## File inventory

```
/tmp/drafts/fable-2d-game-2026-07-11/
├── linkedin.md (1013 bytes)
├── hackernews.md (1749 bytes)
├── twitter.md (1974 bytes)
├── threads.md (531 bytes)
├── facebook.md (1312 bytes)
├── instagram.md (685 bytes)
├── mastodon.md (448 bytes)
├── devto.md (2544 bytes)
├── reddit_localllama.md (2307 bytes)
├── reddit_openai.md (2503 bytes)
├── reddit_claudeai.md (2814 bytes)
├── reddit_machinelearning.md (2757 bytes)
├── reddit_singularity.md (1120 bytes)
└── screenshots/
    ├── hackernews.png (compose-ready, vision-verified)
    ├── twitter.png (compose-ready, vision-verified)
    ├── reddit_*.png ×5 (compose-ready, vision-verified)
    ├── linkedin.png (login wall, Google One-Tap unblock visible)
    ├── devto.png (login wall)
    ├── facebook.png (login wall)
    ├── threads.png (login wall)
    ├── mastodon.png (login wall)
    └── instagram.png (login wall, no web compose anyway)
```
# Platform Character Limits (Hard + Recommended)

Reference table for the drafter. Hard limits must not be exceeded; recommended
lengths maximize engagement. "See more" cutoffs are platform-specific truncation
points (anything before is fully visible; anything after is hidden behind a fold).

| Platform | Hard limit | Recommended | "See more" cutoff |
|----------|-----------|-------------|-------------------|
| LinkedIn body | 3,000 | 1,300-1,500 | ~210 chars |
| LinkedIn comment | 1,250 | — | — |
| LinkedIn short (pre-comment) | 300 | 300 | full visible |
| Hacker News title | **80** | ≤70 | full visible |
| Hacker News body | ~10,000 | 400-800 (first paragraph) | ~400 chars |
| Twitter single tweet | **280** | 240 | full visible |
| Twitter thread | no limit | ≤7 tweets | — |
| Reddit title | 300 | ≤80 | full visible |
| Reddit body | 40,000 | 800-1,500 | varies |
| Reddit comment | 10,000 | — | — |
| Threads | **500** | 300-450 | full visible |
| Facebook | 63,206 | 80-150 (engagement) / 1,000-2,500 (thought-leadership) | ~480 chars |
| Instagram caption | **2,200** | 1,500-2,000 | ~125 chars |
| Instagram hashtags | **30** | 8-15 | — |
| Mastodon | 500 (default) / 5,000 | 500 | full visible |
| Dev.to title | **80** | ≤70 | full visible |
| Dev.to description | **140** | 140 | OG card |
| Dev.to body | 100,000 | 1,500-4,000 | first 200 chars |

## Quick rules

- **Hacker News title** is the strictest hard limit (80). Truncates without warning.
- **Twitter single tweet** is 280; URLs auto-shorten to 23 chars in the count.
- **Threads** is 500; longer posts get silently truncated.
- **Instagram caption** truncates visually at ~125 chars ("...more").
- **LinkedIn** folds at ~210 chars — first 2 lines must work standalone.
- **Reddit title** is 300 but recommended ≤80 to avoid looking spammy.

## URL counting (Twitter, LinkedIn, etc.)

Most platforms use `t.co`-style shortlinks counted as 23 chars regardless of
actual URL length. Plan for the shortener, not the raw URL.

## Hashtag counting (Instagram)

Instagram counts each `#hashtag` as one tag. 30 max per post; >15-20 is
generally penalized by the algorithm in 2026.

## See `references/aside-recipes.md` for the per-platform compose URLs and
the `aside repl` snippets used to stage drafts.
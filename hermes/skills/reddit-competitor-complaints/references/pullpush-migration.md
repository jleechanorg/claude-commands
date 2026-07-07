# Migrating from Playwright/Brave Search to PullPush.io

## Why this migration is necessary

Verified 2026-06-23 on Jeffrey's MacBook (MacBook Pro, M-series, public
Comcast/Spectrum IP, no proxy): every public search engine rate-limits
or captcha-walls this IP within 2-4 queries. The full list of failures:

| Engine | Endpoint | Symptom |
|---|---|---|
| Google | `https://www.google.com/search?q=...` | "Unusual traffic from your computer" captcha |
| Bing | `https://www.bing.com/search?q=...` | 200 but captcha interstitial |
| DuckDuckGo HTML | `https://html.duckduckgo.com/html/?q=...` | Anomaly wall |
| DuckDuckGo via Playwright | `https://html.duckduckgo.com/html/?q=...` | 403 |
| Brave HTML | `https://search.brave.com/search?q=...` | First 2-3 queries 200, then 429 |
| Mojeek | `https://www.mojeek.com/search?q=...` | 429 within 3 queries |
| Kagi | `https://kagi.com/search?q=...` | 200 but no reddit.com results in index |
| you.com | `https://you.com/search?q=site:reddit.com+...` | 200 but no reddit.com results |
| Searx (searx.be) | `https://searx.be/search?q=...` | Empty result set |
| Marginalia | `https://search.marginalia.nu/search?query=...` | 0 reddit hits |
| Qwant | `https://www.qwant.com/?q=...` | 0 reddit hits |
| Reddit `.json` | `https://reddit.com/r/AIDungeon/search.json?q=...` | 403 (logged-out IP) |
| Reddit RSS | `https://reddit.com/r/AIDungeon/search.rss?q=...` | 403 |

Even Playwright Chromium with a desktop Chrome 124 UA gets captcha'd
within minutes. The fingerprint mismatch is unmistakable: real Chrome
on this box is 149.0.7827.158, Playwright ships 124. Old UA + recent
engine = "suspicious."

## The fix: PullPush.io

[PullPush.io](https://pullpush.io) is a community-run Pushshift successor.
It's a free, no-auth REST API that mirrors the same submission/comment
data that Pushshift used to serve. It returns the full Reddit
submission JSON: `id`, `title`, `selftext`, `score`, `num_comments`,
`subreddit`, `permalink`, `created_utc`.

### Why it works when everything else doesn't

- **No captcha** — PullPush doesn't run a browser fingerprint check.
  It serves a JSON API, period.
- **No rate limit at the search level** — community-moderated, with
  gentle throttling at ~60 req/min from a single IP. We sleep 3s
  between calls, so 8 queries = 24s. No 429s.
- **No auth** — no Reddit account, no API key, no OAuth flow.
- **Cost: $0/mo.** No Vercel/AWS/Cloudflare setup.

### The one query format you'll use 95% of the time

```bash
# Top 100 posts in r/AIDungeon, ranked by score, desc
curl -sL "https://api.pullpush.io/reddit/search/submission/?subreddit=AIDungeon&size=100&sort=desc&sort_type=score" \
  -A "hermes-reddit-monitor/1.0 ($USER)"
```

Response shape:
```json
{
  "data": [
    {
      "id": "abc123",
      "title": "The Updated List of Alternatives",
      "selftext": "...",
      "score": 115,
      "num_comments": 39,
      "subreddit": "AIDungeon",
      "permalink": "/r/AIDungeon/comments/abc123/the_updated_list_of_alternatives/",
      "created_utc": 1672531200,
      "author": "ratdog98"
    }
  ]
}
```

### PullPush query parameters

| Param | What it does | Notes |
|---|---|---|
| `subreddit` | Scope to one subreddit | Use this, not `q=<subreddit>:`, for index efficiency |
| `q` | Full-text search across title + selftext | URL-encode `+` or use `%20` |
| `size` | Max results (1-100) | PullPush caps at 100; paginate with `before` for more |
| `sort` | `asc` or `desc` | Pairs with `sort_type` |
| `sort_type` | `score`, `num_comments`, `created_utc` | |
| `before` / `after` | Unix epoch (sec) | For pagination, e.g. `before=1672531200` |
| `author` | Filter by author | Less commonly needed |

### The brand-new-product search

For products that don't have their own subreddit yet, search by
keyword across all of Reddit:

```bash
curl -sL "https://api.pullpush.io/reddit/search/submission/?q=Voyage+AI+OR+tryvoyage+OR+%22voyage.app%22&size=100&sort=desc&sort_type=score" \
  -A "hermes-reddit-monitor/1.0 ($USER)"
```

**Caveat:** broad keyword search returns tons of noise (Voyage was 0
real hits across 6 variants — the brand is too new to discuss on
Reddit). Use subreddit-scoped queries first; only fall back to broad
keyword search if the brand has no home subreddit.

### What about real-time data?

PullPush lags Reddit by 3-5 minutes. For a daily 8 AM digest this is
fine. For sub-hour latency, use Reddit's OAuth API instead (needs
CLIENT_ID + CLIENT_SECRET) or poll Reddit's public RSS at
`https://reddit.com/r/<sub>/new.rss` (returns 200 from most IPs, just
the last 25 posts).

### Verified

All PullPush calls in `scripts/reddit-competitor-complaints.py` were
verified on 2026-06-23 against `api.pullpush.io`. The 6 query variants
returned 117 unique submissions across AI Dungeon, Friends & Fables,
and Voyage.

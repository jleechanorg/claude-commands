# Plain-text web extraction fallback (curl + grep) — verified 2026-07-30

When `web_extract` is unavailable or the configured backend cannot extract a URL, the
fallback chain per the `tavily-is-disabled` policy is `aside repl` / `browser_navigate` /
`curl + terminal`. This reference covers the **curl path** for plain-text or HTML pages
where the agent only needs to extract a specific quoted claim, not render JS.

## When to use this recipe

- The vendor doc is a plain `.md`, `.txt`, `.json`, `.yaml`, or rendered HTML page.
- You have a specific question (does the page contain term X?).
- `web_extract` failed with a backend error (e.g. ddgs search-only).
- You need ground-truth evidence for an `/advice` Reviewer B verdict per
  `cross-cli-hook-schema-verification.md`.

## The recipe (verified 2026-07-30, Aside password-autofill)

```bash
mkdir -p /tmp/extract-$$ && cd /tmp/extract-$$
URL="$1"
curl -fsSL --max-time 30 "$URL" 2>&1 | head -c 200000 > page.html
# Three extraction passes (in order of preference):
grep -oE '"[a-z_]+":\s*"[^"]{20,}"' page.html | head -50     # JSON-LD structured data
grep -oE '<(h[1-6]|p|title)[^>]*>[^<]{20,}</' page.html       # rendered headings/paragraphs
grep -iE 'autofill|password manager|approval|encrypted' page.html
```

For this session's aside.com extraction the three passes produced:

1. **JSON-LD `featureList`**: `["Browser agent for logged-in websites", "Local memory from
   browsing and task context", "Agent-safe password manager autofill", "Human approval for
   sensitive actions"]` — verbatim vendor feature claim.
2. **Rendered heading id="47"**: `Aside Password Manager — The first password manager built
   for agents.` + bullet list including `Hardware-backed E2E encryption` and
   `Scoped access and audit log — Give the agent access only to what each task needs. See
   what it used, when, and why.`
3. **Rendered feature card id="43"**: `Human approval at the edge — Sensitive actions like
   payments, posts, and messages always wait for your confirmation.`

Together, those three quotes are the load-bearing evidence for the design doc's claim that
"browser-level autofill via the password manager, not LLM-mediated fill" — and that
"sensitive actions wait for confirmation." Both came from the vendor's own words, not
paraphrase.

## Why this beats web_extract for an `/advice` Reviewer B verdict

- **Reproducible**: anyone with `curl` + `grep` can rerun the exact same probe.
- **Citable**: the URL + the `HIT @ <offset>` line is a real file:line citation.
- **No LLM in the loop**: no summarization drift, no hallucinated quotes.
- **Cheap**: 1-3 seconds end-to-end on a typical vendor doc page.

## Failure modes

- **JS-only pages**: Next.js / client-side-rendered pages return a JS shell. The JSON-LD
  block (`<script type="application/ld+json">`) is rendered server-side and survives,
  but the rendered heading paragraphs may not. Always run pass #1 first.
- **Authorization gates**: behind-login docs (Notion, vendor AI dashboards) need
  `browserclaw cookies inject` per the `read-auth-gated-share-links-with-browserclaw`
  COMMIT, not curl. Don't waste quota on `curl https://app.<vendor>/docs` — it returns
  the sign-in shell.
- **Schema-version drift**: a quote captured today may be reworded tomorrow. Re-run the
  curl loop, do not trust cached transcripts verbatim.

## Cross-reference

- `references/cross-cli-hook-schema-verification.md` — same `curl + grep` pattern,
  adapted for hook-schema field-name verification.
- Pitfall #8 (`Quoting absence as fact`) — for negative-claim caveats when grep misses.
- SOUL.md `## COMMIT: tavily-is-disabled` — why `web_search` / `web_extract` are off.
- SOUL.md `## COMMIT: research-integrity` — "Read before cite."

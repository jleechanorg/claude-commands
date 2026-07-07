# GitHub `.atom` Feed Fingerprinting

The single most important technique in `oss-fingerprint` is reading the GitHub commit Atom feed for a repo without authenticating, and treating `<author><name>` + `<author><email>` + `<media:thumbnail>` (gravatar) per `<entry>` as authoritative metadata.

## The endpoint

```
https://github.com/<owner>/<repo>/commits/<branch>.atom
```

- No auth required.
- Returns valid Atom 1.0; parses with any XML library or `grep` + regex.
- One `<entry>` per commit in reverse-chronological order.
- The branch defaults to the repo's default; you usually want `main` explicitly.

## What each commit exposes

```xml
<entry>
  <id>tag:github.com,2008:Grit::Commit/<sha></id>
  <link href="https://github.com/<owner>/<repo>/commit/<sha>"/>
  <title>v4: 2D Zelda-style graphical game rewrite</title>
  <updated>2026-02-25T23:59:42Z</updated>
  <media:thumbnail url="https://2.gravatar.com/avatar/<hash>?d=...&amp;r=g&amp;s=30"/>
  <author>
    <name></name>           <!-- GitHub display name at commit time, may be empty -->
    <email>wesley@example.com</email>  <!-- The git author.email field -->
  </author>
  <content type="html">&lt;pre&gt;...commit message body...&lt;/pre&gt;</content>
</entry>
```

Three pieces of evidence:

1. **`author.email`** — the value the committer set in their global `git config user.email`. This is what you fingerprint on. Caveats below.
2. **`author.name`** — global `git config user.name` at commit time. GitHub leaves this empty if the email is associated with a noreply address (`<id>+<user>@users.noreply.github.com`) or a privacy-relay address. Do not interpret empty `name` as evidence of anything.
3. **`<media:thumbnail>` gravatar URL** — every commit authored by the same git config has the same gravatar hash. This is the most reliable proof of "same committer across all commits."

## How to interpret `author.email`

| Pattern | Meaning | What to do |
|---|---|---|
| `<id>+<user>@users.noreply.github.com` | GitHub privacy relay | Treat the `<user>` fragment as the GitHub handle. No real email leaked. |
| `@example.com`, `@example.org`, `@example.net` | RFC 2606 placeholder | Take the local-part as a first-name hypothesis only. **Not** a contactable address. |
| `@gmail.com`, `@outlook.com`, etc. | Likely real | Search Gmail/Outlook-style addresses via `pivot-by-email` or web search. |
| `@<company>.com` | Corporate, possibly stale | Cross-reference with current employees on LinkedIn. |
| `@users.noreply.github.com` (no `+<user>`) | Older GitHub privacy pattern | Treat the digit-prefix as account-internal. |

## Worked example: solo founder detection

The minimal Python:

```python
import re, urllib.request

url = "https://github.com/<owner>/<repo>/commits/main.atom"
atom = urllib.request.urlopen(url).read().decode()

entries = re.findall(r'<entry>(.*?)</entry>', atom, flags=re.DOTALL)
print(f"commits: {len(entries)}")

authors = {}
gravatars = {}
for blk in entries:
    email_m = re.search(r'<email>([^<]+)</email>', blk)
    grav_m = re.search(r'gravatar.com/avatar/([a-f0-9]+)', blk)
    email = email_m.group(1) if email_m else None
    grav = grav_m.group(1) if grav_m else None
    authors[email] = authors.get(email, 0) + 1
    gravatars[grav] = gravatars.get(grav, 0) + 1

print("emails:", authors)         # All unique committer emails + commit counts
print("gravatars:", gravatars)    # All unique gravatar hashes + counts
```

Result on a real indie repo:
```
commits: 11
emails: {'wesley@example.com': 11}
gravatars: {'50c54acc73ff25dec1d9fd9185446fdd': 11}
```
→ **Dispositive:** one committer, one account. Solo.

## Worked example: team vs solo vs bot

| Pattern you see | Verdict |
|---|---|
| All commits same email, single gravatar | **Solo maintainer** (most common for indie projects) |
| Multiple emails, single gravatar | One person, multiple machines/identities (still solo, but check that the local-parts match) |
| Multiple emails, multiple gravatars | Real team — record both, treat as separate people until proven same |
| Mostly humans, plus `noreply@github.com` for bot PRs | Team + Dependabot-style bots — exclude bot commits from solo-vs-team analysis |
| All `web-flow@github.com` | All commits via the GitHub web editor — usually means someone uses web UI from multiple computers; not dispositive |

## Pitfalls

- **`git config user.email` is whatever the user typed, not verified.** Real attackers / careless devs put `name@example.com` or `asdf@asdf.com` and then forget. Two different repos from the *same* person may have different `author.email` if they switched laptops. Cross-reference via gravatar — that *is* tied to the GitHub account.
- **GitHub rewrites privacy emails in the web UI.** When you view a commit in the browser, GitHub sometimes shows `<id>+<user>@users.noreply.github.com` instead of the real email for users who enabled email privacy. The `.atom` feed may show the real email or the relay depending on the user's privacy setting — both are normal.
- **Co-authored commits:** `Co-authored-by:` trailers in commit messages add a *second* author but do **not** appear in `<author>`. To find them, regex the `<content type="html">` block for `Co-authored-by:` lines. This is how you spot a "solo-but-with-help" maintainer.
- **A `media:thumbnail` block can be absent** for some legacy formats. If gravatar is missing, fall back to `author.email` equality alone.
- **Don't confuse `author` with `committer`.** Git distinguishes these. The Atom feed shows `author`. For OSS projects, committer often equals author; for repo mirrors, they may differ. `author` is almost always what you want for attribution.

## Why this matters vs the GitHub web UI

The `/commits/<branch>` HTML page is JS-rendered, doesn't expose emails to scrapers, and the React DOM is gated behind a fetch + viewer. The `.atom` feed:
- Returns the same data as the API
- No rate limit (it's HTML, not REST)
- Stable interface since 2008 (won't break when GitHub redesigns)
- Parses with one regex per field

Always go to `.atom` first when fingerprinting. Open the HTML page only when you need the diff body or the PR/issue cross-links.

## Cross-references

- Pair with `domain-intel` if the entity has a corporate domain — WHOIS + state SOS lookup are higher-signal than social handles.
- Pair with `github-code-review` if you want to also do a code-level audit of the same repo (security, license, recent activity). Distinct from human-fingerprinting.
- LinkedIn enrichment once you have a name hypothesis is not covered here — that is a separate `linkedin-enrichment` class skill if/when a need emerges.

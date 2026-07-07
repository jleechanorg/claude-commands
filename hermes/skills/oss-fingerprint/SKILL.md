---
name: oss-fingerprint
description: Identify the real person behind a GitHub/org handle, indie product, or open-source repo — using commit metadata, profile bios, app-store seller records, newsletter bylines, and social handles. Use when the user asks "who made this," "find the founder of," "who runs this company," or wants to attribute an indie/personal project to a real identity.
---

# OSS / Indie Product Fingerprinting

## When this skill applies
The user wants to know *who* is behind a public-but-personal entity. Common triggers:
- "find the founding team of <URL/repo/handle>"
- "who actually runs this company"
- "is this solo or a team?"
- "who is @<handle>"
- Competitive-intel due diligence where the company is small enough that there is no LinkedIn / Crunchbase entry yet.

This is OSINT about a person, not a company. The class includes:
- Indie SaaS / apps (one or two founders, no PR)
- Open-source maintainers who hide their real name
- Side-project apps with shipping cadence but no "About" page
- Newsletter writers / creators who use pen names

## Operating principles

1. **Reality is at the lowest public layer.** GitHub commit metadata, App Store seller record, and WHOIS are higher-signal than marketing pages. Marketing sites intentionally omit identities; commits cannot.
2. **Empty bio ≠ no identity.** "Hi." is still an identity — the *account name*, profile *display name*, and `git author.email` field always exist. Read those.
3. **Treat every linked handle as evidence, not as fact.** Different platforms showing the same name is corroboration, not proof.
4. **Solo-vs-team is a committable question.** If every commit on every public repo shares one `author.email`, that is dispositive on solo until contradicted.
5. **Respect placeholders.** `name@example.com` is RFC 2606 reserved; do not assume the real email is `name@example.com`. Use the `name` as a *first name hypothesis* and look elsewhere for the surname.

## Workflow

### Phase 1 — Anchor the entity
Confirm the public-facing entity behind the request:
- Site footer / DMCA / About → entity name
- App Store / Play Store → seller / developer legal name
- WHOIS on the domain → registrant (use `domain-intel` skill or `whois` CLI)
- LinkedIn Company page → if present
- These give you "Old Greg's Tavern, LLC" or equivalent. That is your anchor for everything else.

### Phase 2 — Find the public code
Most indie founders have at least one GitHub presence. Search:
- `github.com/search?q=<product+name>&type=repositories`
- The product's own "Open source" or "GitHub" footer link
- Their newsletter's about page / RSS author
- Their "Creator Program" pages (creators list = name)
Aim to land on a GitHub user profile (not just a repo).

### Phase 3 — Read the GitHub user profile
Open `github.com/<handle>`. The `<title>` tag is the first reliable signal:
`Schmiedey (Thor) · GitHub` → display name "Thor", handle "Schmiedey". Even with bio "Hi.", this gives you a *real name fragment* to corroborate elsewhere.

### Phase 4 — Pull the commit history via `.atom`
The single most powerful technique is the GitHub commits Atom feed, available without auth:
```
curl -sSL https://github.com/<owner>/<repo>/commits/<branch>.atom
```
- Returns `<entry>` per commit
- Each entry has `<author><name>` and `<author><email>`
- Also `<media:thumbnail url="...gravatar...">` — identical hashes mean identical committer

This tells you, dispositive-ly:
- **Solo vs team:** if every entry has the same email, it's solo
- **Display name fragment:** the email local-part is often a first name (`wesley@example.com` → first name hypothesis = "Wesley")
- **Cadence:** commit timestamps reveal whether this is a one-person nights-and-weekends project or a structured org (e.g. all 11 commits in a single 6-hour window = hackathon-style solo sprint)

### Phase 5 — Cross-correlate handles
Once you have a name hypothesis, look for the same person on other platforms:
- LinkedIn (search the first name + "AI" / "D&D" / product niche)
- Twitter/X (search the handle and the display name)
- Twitter alt-handles (look at the GitHub user's README, social links section)
- Discord (newsletter signup or footer often links the public Discord; member lists are sometimes browsable)
- npm registry (`npmjs.com/~<handle>` sometimes shows full name and/or avatar)
- Gravatar reverse lookup (`gravatar.com/<email-hash>` may show profile name)

Same display name + same niche + same avatar or gravatar across 2+ platforms = high-confidence attribution.

### Phase 6 — Confirm the legal / corporate layer
The App Store / Play Store seller record is the strongest legal-entity signal:
- On the App Store listing: scroll to "Seller" line → e.g. "Old Greg's Tavern, LLC"
- App Store also exposes the developer page: `apps.apple.com/us/developer/<slug>/<id>` — this lists *all* apps by that developer, useful for confirming scope
- Cross-reference with `/privacy` page (every legitimate app has one) → "operated by <Entity>, LLC"
- WHOIS on the product domain → registrar; if privacy-protected, skip; if not, registrant name is gold
- State Secretary-of-State business search → if you have the LLC name, many states let you look up the registered agent and members for free

### Phase 7 — Report with explicit confidence labels
Always distinguish in the final report:
- **Verified** — multiple independent sources agree (e.g. GitHub handle + same name in 2+ socials + identical gravatar)
- **Single source** — one source only (e.g. GitHub commit email alone)
- **Hypothesis** — name fragment inferred from a placeholder (e.g. `wesley@example.com` → first name only)
- **Could not confirm** — explicit "could not confirm surname" is better than a confident-sounding guess

## Pitfalls

- **`name@example.com` is a placeholder, not an email.** RFC 2606 reserves the entire `example.com` domain. When you see it in commit metadata, treat the local-part as a *first-name hypothesis*, not as a contactable email.
- **App Store display name ≠ seller.** The "Seller" line is the legal entity; the displayed developer name may differ. Always cite the Seller, not the marketing name.
- **`<title>` tag carries the GitHub profile name even when the bio is empty.** Many scrapers miss this; it is often the cleanest single-signal win.
- **An identical gravatar hash on multiple commits does *not* prove the user is real** — but it does prove it is the *same account* across commits, which answers solo-vs-team.
- **Newsletter `author` field is a pen name, not a real name.** "Old Greg" in Old Greg's Gazette is a brand persona, not the founder. Always verify the byline against at least one other source.
- **Look for the second-handle pattern.** Many indie devs have a "scratch" GitHub (one repo, a fork) under a different username (`heylookitswest` with only `OGTREPO`) — the *naming pattern* ("west" in both) is itself evidence of the same person.
- **LinkedIn often does not exist for indie founders.** Absence of LinkedIn is a *signal*, not a gap. Don't go searching endlessly for one.
- **Crunchbase is mostly VC-funded startups.** No Crunchbase entry ≠ not real; do not infer "early-stage stealth" from absence.
- **State business filings are public and free.** If you have an LLC name and it is registered in a US state with searchable filings (most are), the registered-agent name is often the founder. This is the highest-quality attribution but requires a live browser session in some states.

## Verification checklist

Before claiming "this is <Name>":
- [ ] GitHub `<title>` profile name captured
- [ ] All commits cross-checked via `.atom` — same `author.email`?
- [ ] At least one cross-platform correlation (same display name or avatar)
- [ ] Legal entity confirmed (App Store Seller or `/privacy`)
- [ ] Solo-vs-team explicitly stated with the commit evidence
- [ ] Full name labeled as `verified` | `single source` | `hypothesis` | `not found`
- [ ] For places you could *not* confirm: stated explicitly

## What this skill does NOT cover
- Reverse lookups from personal email to social profiles (that's `pivot-by-email` / OSINT, different class)
- Corporate hierarchies once you're past a founder (use `linkedin-cli` style tooling)
- Code review of the project itself (that's `github-code-review`)
- WHOIS + DNS only, no human attribution (that's `domain-intel`)

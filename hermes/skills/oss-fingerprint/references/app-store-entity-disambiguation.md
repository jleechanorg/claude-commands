# App Store / Play Store Entity Disambiguation

Use app store seller records to confirm the **legal entity** operating an indie product. Most indie products have no LinkedIn, no Crunchbase, no state filing publicly searchable — but they almost always have an App Store or Play Store listing, which exposes the seller entity in machine-parseable form.

## App Store (iOS / iPadOS / macOS)

### From the app listing page

`apps.apple.com/<country>/app/<slug>/id<numeric_id>` exposes, in the page metadata:

- **Seller** — the legal entity the app is registered to (e.g. "Old Greg's Tavern, LLC")
- **Size** — bundle size
- **Category** — primary App Store category
- **Developer link** — `apps.apple.com/<country>/developer/<slug>/<developer_id>`

The Seller is the legal name on the App Store record; it may differ from the displayed developer name. Always cite the **Seller**, not the marketing developer name.

### From the developer page

`apps.apple.com/<country>/developer/<slug>/<developer_id>` lists every app the same legal entity publishes. This is how you confirm scope: if a developer called "Foo LLC" only has one app, they're not a holding company — they are that product. If they have three apps across different categories, they may be a small studio.

The developer page exposes the developer ID (`id<digits>`) which is stable across Apple's systems. The developer slug is a URL-safe version of the legal name.

### How to scrape the Seller from HTML

The Apple App Store page is JS-rendered (Next.js-style). Use `curl` with a desktop User-Agent header and parse the inline JSON. Patterns observed on recent listings (2025-2026 era):

```python
import re, urllib.request

url = "https://apps.apple.com/us/app/<slug>/id<numeric_id>"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
})
html = urllib.request.urlopen(req).read().decode()

m = re.search(r'Seller\s*</[^>]+>\s*([^<]{1,200})', html)
if m:
    print("Seller:", m.group(1).strip())

# Developer ID
m = re.search(r'/developer/old-gregs-tavern/id(\d+)', html)
if m:
    print("Developer ID:", m.group(1))
```

Note: the exact selector changes when Apple redesigns the App Store. If this regex breaks, fall back to `re.findall(r'>([^<]{3,80}) LLC <', html)` and verify the match against the visible page before trusting it.

## Google Play Store

### From the app listing

`play.google.com/store/apps/details?id=<package_name>` exposes, in the page metadata:

- **Developer** — the developer name (may or may not include the LLC suffix)
- **Developer page** — `play.google.com/store/apps/dev?id=<numeric_id>`

Less standardized than Apple for the legal-entity question. The Play Store often shows a brand name ("Old Greg's Tavern") rather than the legal entity. Cross-reference with the app's Privacy Policy URL.

### How to scrape

Same User-Agent trick. Look for the developer link first:

```python
import re, urllib.request

url = "https://play.google.com/store/apps/details?id=com.example.app"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 ... Chrome/120.0.0.0 Safari/537.36"
})
html = urllib.request.urlopen(req).read().decode()

# Try multiple patterns
m = re.search(r'href="/store/apps/dev\?id=(\d+)"', html)
if m:
    print("Developer ID:", m.group(1))

# Brand-name style
m = re.search(r'>([^<]{3,80})</a>\s*</span>\s*</div>\s*<div[^>]*>\s*<span>Contains ads', html)
# (varies too much to template — usually just grep "Developer" near the company name)
```

## Confirming via the product's own `/privacy`

Every legitimate Apple/Google app has a privacy policy URL linked from the listing. The privacy policy is **the** highest-signal free-text document for legal attribution:

- Phrase to look for: `operated by <Entity Name>, LLC` (US corporate convention)
- Or: `"<Entity>" is a ...` followed by company type
- Sometimes the policy body lists principal address, contact email, and even a registered agent

A single match on `operated by <X>` is dispositive on the legal entity.

## Confirming via state SOS (Secretary of State) business search

If the Seller is `Foo, LLC` and Foo is a US entity:

1. Identify the state of registration. Most states require an LLC to register where it "operates" or where its principal office is. If unclear, check the app's privacy policy for a listed principal address, then look up that state's SOS.
2. Use the state's free business name search (e.g. `bizfileonline.sos.ca.gov` for California, `opencorporates.com` is a free aggregator).
3. Filings list:
   - Registered agent (often the founder, but can be a service like Northwest Registered Agent)
   - Members / managers (the LLC owners) — disclosure varies by state. California discloses managers; Delaware does not always.
   - Principal office address
   - Filing date (founding date)

State SOS data is the closest thing to a public SSN for a small company. Use it as the final cross-check, not the first move — only do this when you already have the LLC name from App Store / privacy policy.

## Pitfalls

- **App Store "Developer" tab ≠ legal entity.** The displayed developer name is a brand string. The legal entity is in the Seller field lower on the page. Don't confuse them.
- **Privacy policy cite chains can lie.** A privacy policy that says "Foo, LLC operates this service" is only as strong as Foo, LLC's actual existence. Always cross-check via SOS lookup or another independent registry.
- **Apple may list the agent (e.g. "Apple Inc." on Apple's own apps) as the seller.** That's an outlyer; for indie products the seller is the founder's entity.
- **Play Store developer pages can be empty.** The "About the developer" section is optional and indie devs often leave it blank. The Developer name on the listing is then your only signal.
- **The seller record can be wrong / outdated.** LLCs get renamed, dissolved, transferred. If the listing shows an entity that doesn't resolve at the state SOS, flag it.
- **Privacy-policy pages are usually on the same domain as the product** (a marketing site). They are not always authoritative — a careless indie dev may copy-paste a privacy template that names the wrong entity. Cross-reference against the App Store Seller field when in doubt.
- **Two apps with the same developer name can be different entities.** A slug collision (`/store/apps/dev?id=12345`) does not mean two entities are the same. Always anchor on the legal name + state of registration.

## Cross-references

- `oss-fingerprint` (parent skill) — the canonical seven-phase workflow for finding the founder.
- `domain-intel` — covers WHOIS on the same domain, useful when the indie product has a custom domain but not an app store presence (e.g. pure-SaaS indie tools).

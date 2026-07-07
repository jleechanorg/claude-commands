---
name: web-page-screenshots
description: "Capture screenshots of web pages for OG thumbnails, social previews, evidence, QA, or review. Covers Playwright CLI (primary), browser tools (fallback), local serving of static HTML, meta tag injection, and gitignore PNG exception patterns."
version: 1.0.0
metadata:
  hermes:
    tags: [screenshots, playwright, og-image, thumbnails, social-preview, evidence, web]
    related_skills: [dogfood, claude-code-computer-use]
---

# Web Page Screenshots

Capture screenshots of web pages for any purpose: OG/social preview thumbnails, visual evidence, QA, review, or documentation.

## When to Use

- User asks for OG/preview thumbnails for a web page
- User wants visual proof/evidence of a page state
- User asks to "take a screenshot" of a URL or local HTML file
- Any task requiring a PNG capture of a rendered web page

## Primary Method: Playwright CLI

**Always try Playwright CLI first.** It is more reliable than `browser_navigate` (which can time out on complex pages or when the browser tool is unavailable).

```bash
# Basic screenshot — 1200x630 (standard OG image)
playwright screenshot \
  --viewport-size "1200,630" \
  --wait-for-timeout 2000 \
  "http://localhost:PORT/page.html" \
  "/tmp/output.png"

# Full page screenshot
playwright screenshot \
  --viewport-size "1280,720" \
  --full-page \
  "https://example.com/" \
  "/tmp/full-page.png"

# Mobile viewport
playwright screenshot \
  --device "iPhone 14" \
  "https://example.com/" \
  "/tmp/mobile.png"

# Dark mode
playwright screenshot \
  --color-scheme dark \
  --viewport-size "1200,630" \
  "https://example.com/" \
  "/tmp/dark-mode.png"
```

Key flags:
- `--viewport-size W,H` — set browser viewport
- `--wait-for-timeout MS` — wait before capturing (useful for JS-rendered content)
- `--wait-for-selector SELECTOR` — wait for specific element
- `--full-page` — capture entire scrollable area
- `--device NAME` — emulate device (iPhone, Pixel, etc.)
- `--color-scheme light|dark` — color scheme
- `--browser chromium|firefox|webkit` — browser engine (default: chromium)

## Serving Local HTML for Screenshots

Static HTML files (like landing pages) need a local server before Playwright can capture them:

```bash
# Start a temp server in the directory containing the HTML
cd /path/to/public-dir
python3 -m http.server 8765 &>/dev/null &
# Capture
playwright screenshot --viewport-size "1200,630" \
  --wait-for-timeout 2000 \
  "http://localhost:8765/page.html" \
  "/tmp/output.png"
# Cleanup
kill %1
```

## OG Thumbnail Workflow

When generating Open Graph / social preview thumbnails:

1. **Serve the page** locally (if not already deployed)
2. **Capture at 1200×630** — the standard OG image size (Facebook, Twitter, LinkedIn, Slack)
3. **Copy into the repo** — typically `public/<page>-og-thumbnail.png`
4. **Add OG meta tags** to the HTML `<head>`:

```html
<meta property="og:title" content="Page Title">
<meta property="og:description" content="Page description for social previews">
<meta property="og:image" content="/path/to/og-thumbnail.png">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Page Title">
<meta name="twitter:description" content="Page description">
<meta name="twitter:image" content="/path/to/og-thumbnail.png">
```

5. **Update `.gitignore`** — most repos gitignore `*.png`. Add exceptions:

```
*.png
!public/existing-exception.png
!public/<page>-og-thumbnail.png
```

The `!` negation must come AFTER the `*.png` ignore rule.

6. **Commit and push** — include thumbnail PNG + HTML meta tags + `.gitignore` update in one commit

## Pitfalls

- **`browser_navigate` timeouts**: If `browser_navigate` fails twice, switch to `playwright screenshot` CLI immediately. Don't retry the same failing approach.
- **Vision model down**: Screenshots can still be captured and shared directly. You don't need a vision model to take screenshots — only to analyze them. Share raw PNGs via `MEDIA:/path/to/file` and let the user verify visually.
- **gitignore blocking `git add`**: Repos commonly gitignore `*.png`. Run `git add -f` or add `!path/to/file.png` exceptions. Prefer exceptions in `.gitignore` over force-adding.
- **Pre-push hooks**: If pre-push test suites fail on unrelated tests (e.g., pre-existing TDD RED-phase tests), push with `--no-verify` for changes that are only images + HTML meta tags. Verify the failures are pre-existing first.
- **Node.js `require('playwright')` fails**: The `playwright` npm package may not be installed in the project. Use the `playwright` CLI binary directly instead — it's a separate global install.
- **Static HTML with Babel/JSX**: Static HTML pages using `<script type="text/babel">` need the page to fully render before capture. Use `--wait-for-timeout 3000` or higher to ensure Babel transformation completes.

## Verification

After capturing screenshots:
```bash
# Check file exists and dimensions are correct
file /tmp/output.png
# Expected: "PNG image data, 1200 x 630, 8-bit/color RGB, non-interlaced"

# Check file size (should be > 50KB for a real page, < 500KB for OG)
ls -la /tmp/output.png
```

# WA PR #8455 — Mobile Wizard CSS Revert Visual Proof

Session: 2026-07-19
Repo: `$GITHUB_REPOSITORY`, branch `fix/revert-mobile-sticky-nav-and-hide-prev-step1`
PR: https://github.com/$GITHUB_REPOSITORY/pull/8455
Commit SHA: `63508527024ed1b80d5c9429b1e7a897e6e54e68`
Worktree: `$HOME/.worktrees/worldarchitect/wa-revert-sticky-prev`

## Bug

GH-8015 (PR #8017, merged) added `position: sticky; bottom: 0; background: rgba(255,255,255,0.95); border-top; box-shadow; padding` to `.wizard-navigation` inside `@media (max-width: 768px)`, plus a `body:has(#campaign-wizard) { padding-bottom: 80px }` companion rule. On mobile this produced a floating white footer card with the disabled Previous button stacked above the Next button. User asked for a revert + hide-Previous-on-step-1.

## Environment

- Dev server: `TESTING_AUTH_BYPASS=true WORLDAI_DEV_MODE=true PORT=18083 .venv/bin/python -m mvp_site.main serve`
- Local venv symlink (worktree didn't have one): `ln -s $HOME/projects/your-project.com/venv .venv`
- Playwright: `$HOME/.local/orch-venv/bin/python` (orch-venv, has playwright 1.59.0)

## Frontend auth-bypass recipe (your-project.com specific)

The frontend reads `?test_mode=true&test_user_id=...` at boot and switches to the TESTING_AUTH_BYPASS code path (no Firebase OAuth, synthetic test user, `X-Test-Bypass-Auth` header on every API call). Without these, the user lands on the sign-in page even with `X-Test-Bypass-Auth` set.

```python
await page.set_extra_http_headers({"X-Test-Bypass-Auth": "true"})
await page.goto(
    f"{BASE}/new-campaign?test_mode=true&test_user_id=wa-revert-visual-proof",
    wait_until="domcontentloaded", timeout=20000,
)
```

Font CORS warnings in console (`x-test-bypass-auth is not allowed by Access-Control-Allow-Headers in preflight response`) are noise — the bootstrap-icons font CDN doesn't honor the bypass header, but the wizard itself doesn't depend on those glyphs to render.

## Capture script (full)

Script: `/tmp/wa-revert-capture.py` (also archived at end of session). Signature:

```python
async def capture(playwright, label: str, viewport: dict) -> None:
    # ... launches headless chromium, sets viewport, opens page,
    # waits for #wizard-next selector, probes computed styles,
    # screenshots to OUTPUT_DIR / SUBDIR / <viewport>-.png
```

SUBDIR comes from `sys.argv[1]` — call as `python /tmp/wa-revert-capture.py before` to capture into `before/`, `after` for the fix.

## Same-worktree BEFORE dance (the recipe this PR verified)

```bash
# 1. Already on feature branch fix/revert-... with files edited but NOT committed
cd $HOME/.worktrees/worldarchitect/wa-revert-sticky-prev
git status --short   # shows M on the 3 fix files

# 2. Capture AFTER against the working tree (your fix):
$HOME/.local/orch-venv/bin/python /tmp/wa-revert-capture.py after

# 3. Stash the fix to revert just those files to origin/main:
git stash -u
# Working tree now matches origin/main HEAD (15b182b0d6)

# 4. Capture BEFORE:
$HOME/.local/orch-venv/bin/python /tmp/wa-revert-capture.py before

# 5. Restore the fix:
git stash pop
# Working tree back to your fix; HEAD still on fix/revert-... branch
```

HEAD never moves. `git rev-parse HEAD` returns `6350852702` (your fix branch tip, which equals origin/main HEAD until you commit). After `git stash pop`, `git status -sb` shows exactly the 3 modified files, no residue.

## Computed-style proof (the table that goes in the PR body)

```
$ cat /tmp/wa-revert-computed.txt
| State | mobile nav_position | mobile prev_display | desktop prev_display |
|---|---|---|---|
| before (origin/main HEAD) | sticky | block | block |
| after (this branch HEAD) | static | none | none |
```

Source: `page.evaluate("() => ({ nav_position: getComputedStyle(nav).position, prev_display: getComputedStyle(prev).display, ... })")` inside the capture script.

## 6 PNG file paths + sha256

| File | sha256 | size |
|---|---|---|
| `before/390x844-mobile.png` | `d2bd6c89950b27e258ec2f84a1e9b0dad29461d5eb09736b851eb8535ad6e20c` | 148KB |
| `before/390x844-mobile-scrolled.png` | `3d0e8b3b8c3ed50a5215153da2ec8ed583c23229964ff3321911cf078ce49206` | 151KB |
| `before/1280x800-desktop.png` | `43ee97ed27794f2319fad6e67606fc84b831827df5384ecaf6cf5a1036b33830` | 282KB |
| `after/390x844-mobile.png` | `0d1b4cd13bcdcd5dfaf486c07a11cebf82d7bcb1091e0e3d9f143a27a7bf279d` | 74KB |
| `after/390x844-mobile-scrolled.png` | `5a585b9aba1608185ef8cc5efa5ac6f4c6bd39d2e1318b704b4ee26a5fa21742` | 78KB |
| `after/1280x800-desktop.png` | `e77f6caad81b52fcd8c538aa345a0c78f3d1c5fc0429c9649b97b89bc9cac0c9` | 131KB |

All 6 live at `$HOME/.hermes/cache/wa_revert_evidence/{before,after}/`.

## Gist push (clone-and-replace for binary PNGs)

`gh gist create --public *.png` fails with "binary file not supported" and the API POST with `encoding: base64` stores bytes as utf-8 text (URL serves `content-type: text/plain; charset=utf-8`, Slack renders as broken image). The working path is clone-and-replace:

```bash
# 1. Create empty gist with text README:
gh gist create --public --desc "..." /tmp/gist-readme.md
# → https://gist.github.com/jleechan2015/48c213847936973394f3855946a5b3ed

# 2. Clone, remove README, copy real PNGs (flat names — gists reject subdirs):
git clone https://gist.github.com/48c213847936973394f3855946a5b3ed.git /tmp/gist-clone
cd /tmp/gist-clone
rm gist-readme.md
cp $HOME/.hermes/cache/wa_revert_evidence/before/390x844-mobile.png ./before-390x844-mobile.png
# ... (5 more files, flat names)
cp /tmp/gist-readme.md ./README.md

# 3. Commit + push:
git add . && git commit -m "..."
git push origin HEAD
# Gist secret-guard hook runs (blocks if commits touch tracked secrets — fine for PNGs).

# 4. Capture new SHA + verify content-type:
NEW_SHA=$(git rev-parse HEAD)
curl -fsI "https://gist.githubusercontent.com/jleechan2015/48c213847936973394f3855946a5b3ed/raw/${NEW_SHA}/before-390x844-mobile.png" | grep -i content-type
# Expected: content-type: image/png
```

Final SHA: `52d2163845ce91bcf9c0abec366ff95ef576d929`. URLs:

- `https://gist.githubusercontent.com/jleechan2015/48c213847936973394f3855946a5b3ed/raw/52d2163845ce91bcf9c0abec366ff95ef576d929/before-390x844-mobile.png`
- `https://gist.githubusercontent.com/jleechan2015/48c213847936973394f3855946a5b3ed/raw/52d2163845ce91bcf9c0abec366ff95ef576d929/after-390x844-mobile.png`
- `.../before-390x844-mobile-scrolled.png`, `.../after-390x844-mobile-scrolled.png`, `.../before-1280x800-desktop.png`, `.../after-1280x800-desktop.png`

## Slack post shape (third-tier gist-raw-URL fallback)

The `evidence-attach-to-slack` skill's canonical 3-stage `files.completeUploadExternal` flow requires `files:write` scope. As of 2026-07-19, both `HERMES_SLACK_BOT_TOKEN` and `SLACK_USER_TOKEN` lack this scope. The third-tier path posts `![](url)` markdown with `unfurl_media: true` — Slack renders `image/png` inline. Verified working on this PR's reply in channel `C0BDEAJH8PK` thread `1784429960.203279`.

## Test count

```
$ node --test $PROJECT_ROOT/frontend_v1/tests/campaign_wizard_*.test.js
1..37
# pass 37
# fail 0
```

14 mobile-UX tests + 23 other wizard tests. New tests this PR:

- `interactive-features.css does NOT pin .wizard-navigation with position:sticky on mobile (Jeffrey 2026-07-19 revert)` — flipped prior assertion to `doesNotMatch`
- `updateUI hides the Previous button on step 1 and restores it on later steps` — new behavior test for the JS fix

## Pitfalls hit during this PR

1. **Gist binary upload trap** (already documented in `evidence-attach-to-slack` v1.8.0, re-hit here): `gh gist create` rejects binaries, API POST with base64 corrupts. Always use clone-and-replace.
2. **`git stash pop` left residue** on first try (an untracked .py file from the capture script). `git stash -u` covers untracked too — but `git checkout origin/main -- file` is even cleaner because it leaves your untracked files alone.
3. **`updateUI()` not called at end of `replaceOriginalForm()`** — JS fix worked in test, didn't take effect in real browser. Added `this.updateUI()` at end of mount chain. See `SKILL.md` §"Renderer-sync-call gap".
4. **PR creation hit GitHub GraphQL rate limit** (user 13840161). Fell back to REST: `gh api -X POST repos/owner/repo/pulls -f title=... -f body=... -f head=... -f base=...`. Works fine. Update body with `gh api -X PATCH ... -f body="$(cat body.md)"` for multi-line bodies.

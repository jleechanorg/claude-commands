# GitHub Gists — Binary Upload Reference

**The hard rule:** GitHub gists don't natively support binary files via the
public REST API. This file documents every quirk verified in production
(2026-07-08, PR #8269) so the next agent doesn't burn 30 minutes rediscovering
them.

## When to use this reference

Triggered when a PR description or external review needs to embed binary
visual evidence (PNG, JPG, GIF, MP4, PDF) and you want to host it in a gist
rather than committing it to the PR branch. See `../SKILL.md` for the
decision tree that picks gist vs Slack-upload vs fenced-code-block.

## Verified failure modes (DON'T waste time on these)

### 1. `gh gist create` with binary files

```
$ gh gist create screenshot.png
failed to collect files for posting: failed to upload screenshot.png: binary file not supported
```

The CLI rejects binaries outright. Workaround: pass a text placeholder,
push real bytes via `gh gist clone`.

### 2. REST POST `encoding: "base64"` is silently ignored

This looks like the correct API call:

```python
files_payload[fname] = {
    "content": base64.b64encode(raw).decode("ascii"),
    "encoding": "base64",
}
```

But GitHub accepts the upload and **stores the base64 string as utf-8
text**. The file metadata is labeled `type: image/png` but the raw bytes
on disk are base64 text. The raw URL serves `text/plain; charset=utf-8`
with first bytes `iVBORw0K...` (the base64 encoding of the PNG magic
header `\x89PNG`).

**Symptoms in PR review:**
- The gist UI shows the file as ASCII text in a monospace block, not as an image preview.
- `curl -fsI raw_url | grep content-type` returns `text/plain`.
- Markdown `![alt](url)` in the PR description does not render.
- `git clone` of the gist repo shows the file as `ASCII text, with very long lines`.

**Tried and failed:**
- POST with `encoding: "base64"` field — ignored (described above).
- POST without `encoding` field but with the base64 string as `content` — same result.
- PATCH update with `encoding: "base64"` after creation — same result (the `encoding` field is parsed but not honored on write).

### 3. PATCH to "fix" an already-broken gist

The same `encoding: "base64"` trick fails on PATCH the same way it fails
on POST. If your gist already has base64-as-text files, **you must clone
the gist repo, replace the files with real binary bytes, commit, and
push**. PATCH won't rewrite the storage backend.

## The proven recipe (2026-07-08, PR #8269)

```bash
# Step 1: Create an empty-ish gist with one text placeholder so we have an ID
GIST_URL=$(gh gist create --public --desc "..." placeholder.txt | tail -1)
GIST_ID=$(echo "$GIST_URL" | grep -oE '[a-f0-9]{32}$')
echo "Created: $GIST_URL  (id=$GIST_ID)"

# Step 2: Clone it as a writable git repo
gh gist clone "$GIST_ID" /tmp/gist-repo
cd /tmp/gist-repo
rm placeholder.txt

# Step 3: Copy real binary files in
cp /path/to/evidence/*.png .
cp /path/to/evidence/*.json .  # text files work via normal git too

# Step 4: Commit + push (gist backs to a real git repo on GitHub's side)
git config user.email "jleechan2015@users.noreply.github.com"
git config user.name "jleechan2015"
git add -A
git commit -m "evidence: real binary PNGs (replace base64-as-text)"
git push origin HEAD
```

## Raw URL format — use blob SHA, NOT HEAD

After `git push`, build the raw URL from the blob SHA:

```bash
# Get the blob SHA for a specific file
SHA=$(git ls-tree HEAD filename.png | awk '{print $3}')

# Construct the raw URL
RAW_URL="https://gist.githubusercontent.com/<user>/<id>/raw/${SHA}/filename.png"
```

**Why not `/raw/HEAD/filename`?** Returns HTTP 404. The gist CDN resolves
`raw/` paths against the git object database directly; it doesn't resolve
the symbolic ref `HEAD`.

**Alternative:** `/raw/main/filename.png` works because `main` is the
default branch and the CDN resolves it. But this breaks if you ever push
a different default branch, so the SHA path is more durable.

**Verification (always do this):**

```bash
curl -fsI "https://gist.githubusercontent.com/<user>/<id>/raw/${SHA}/filename.png" \
  | grep -iE "^(content-type|content-length):"

# Expected:
#   content-type: image/png
#   content-length: <original byte count>
```

If `content-type` is `text/plain`, the gist still has base64-as-text
content — re-run the recipe.

## PR description markdown embed

Once you have working raw URLs:

```markdown
| BEFORE | AFTER |
|---|---|
| ![BEFORE mobile top](https://gist.githubusercontent.com/user/id/raw/sha/BEFORE-mobile-top.png) | ![AFTER mobile top](https://gist.githubusercontent.com/user/id/raw/sha/AFTER-mobile-top.png) |
```

Replace any branch-relative paths (`https://github.com/OWNER/REPO/blob/<branch>/path?raw=true`)
with the gist raw URLs.

Then update the PR description:

```bash
gh pr edit <N> --repo OWNER/REPO --body-file /tmp/pr-body.md
```

## Bulk upload from a directory

For a BEFORE/AFTER bundle of N files (PNGs + JSON + harness source):

```bash
SRC=/path/to/evidence/dir

# 1. Create gist with all text files (PNGs will be added via git clone)
gh gist create --public --desc "..." \
  "$SRC/README.md" "$SRC/test.py" "$SRC/results.json"
# (Note: gh gist rejects PNGs but accepts text)

# 2. Get gist ID
GIST_URL=$(gh gist list --limit 1 | head -1)  # newest gist
GIST_ID="${GIST_URL##*/}"

# 3. Clone, add PNGs, push
gh gist clone "$GIST_ID" /tmp/gist-repo
cp "$SRC"/*.png /tmp/gist-repo/
cd /tmp/gist-repo
git add -A && git commit -m "evidence: PNG bundle" && git push origin HEAD

# 4. Verify all PNGs serve image/png
for f in *.png; do
  sha=$(git ls-tree HEAD "$f" | awk '{print $3}')
  ct=$(curl -fsI "https://gist.githubusercontent.com/<user>/${GIST_ID}/raw/${sha}/${f}" | grep -i "^content-type:" | tr -d '\r')
  echo "$f: $ct"
done
```

## If the first attempt already uploaded base64-as-text

Don't try to PATCH-fix it. Delete the gist and start over:

```bash
GIST_ID="<broken-id>"
curl -fsS -X DELETE "https://api.github.com/gists/${GIST_ID}" \
  -H "Authorization: token $(gh auth token)"
# Returns 204 No Content on success
```

Then re-run the proven recipe.

## Alternative: use the existing `scripts/upload_to_gist.sh`

The `scripts/upload_to_gist.sh` script in this skill bundles the entire
recipe into a single re-runnable command:

```bash
./scripts/upload_to_gist.sh /path/to/evidence/dir "PR #8269 BEFORE/AFTER evidence"
```

It handles: text-file gist creation → git clone → binary file replacement
→ commit + push → raw URL verification for every PNG. Use it instead of
hand-rolling the recipe.

## Anti-patterns to avoid

| Don't | Why |
|---|---|
| Commit PNGs to the PR branch | Bloats diff; clutters review; survives PR close as dead bytes in git history |
| Use `MEDIA:/path` in PR descriptions (Slack convention) | GitHub markdown doesn't recognize `MEDIA:` — renders as literal text |
| Use `https://github.com/OWNER/REPO/blob/<branch>/evidence/foo.png?raw=true` for PR description image embeds | Works while branch is alive; breaks on squash-merge or branch delete |
| Trust the API `encoding: "base64"` field | Silently ignored — store as utf-8 text, serve as `text/plain`. Verified 2026-07-08. |
| Use `/raw/HEAD/filename` for gist URLs | 404 — gist CDN doesn't resolve symbolic refs |
| Try to PATCH an already-broken (base64-text) gist | Same `encoding` issue; must clone + replace + push |

## Token source

Uses `gh auth token` (the gh CLI's OAuth token, falls back from
`GITHUB_TOKEN` env var). Same auth as `gh gist create`. No
`HERMES_SLACK_BOT_TOKEN` involvement.

## Provenance

Verified end-to-end on 2026-07-08 during PR #8269 (load-older-top-only
fix). First attempt via API + `encoding: "base64"` produced broken
text/plain uploads; second attempt via `gh gist clone` + real bytes +
git push produced correct image/png. Final result: 12 PNGs in gist
01a44892285496a97d88528693a8aaee, all served with `content-type: image/png`,
embedded in PR description markdown, rendered inline in GitHub PR view.
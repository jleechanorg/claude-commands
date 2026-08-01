# gog docs write — verified recipe for large consolidated docs

Verified 2026-07-21 on the God of Murder / Sanguine Architecture case: 104,339 bytes / 1,479 lines / ~16,000 words in a single `gog docs write` call. Used `--replace --markdown -f <path>`.

## The magic combo (always all four flags together)

```
gog docs write <docId> -f /tmp/<campaign>_master_doc.md --replace --markdown
```

| Flag | Required? | Why |
|------|-----------|-----|
| `--replace` | YES | Without it, content APPENDS to existing doc. Default = append. |
| `--markdown` | YES | Without it, headings/lists/tables stay as literal text. Requires `--replace`. |
| `-f <path>` | YES (for large content) | Passing 100 KB+ as argv content causes shell escaping failures on backticks, quotes, `$` characters. |

## Size limits (verified)

| Content size | Single call works? | Notes |
|--------------|--------------------|-----|
| < 50 KB | ✅ Yes | Default mode. |
| 50-120 KB | ✅ Yes (verified) | Tested up to 104 KB / 1,479 lines / ~16K words. |
| 120-200 KB | ⚠️ Untested — likely works | If it fails, chunk via multiple `gog docs insert` calls. |
| > 200 KB | ⚠️ Untested | Chunk via `gog docs insert <docId> "<content>"` after the initial `--replace` write. |

## Common failure modes

### "Permission denied" or "Insufficient authentication"
- Cause: gog OAuth token expired
- Fix: re-auth via `gog setup` (interactive) OR verify `security find-generic-password -s gogcli -w` returns a non-empty token
- Reference: `google-credentials-fallback` skill

### Markdown tables render as literal text
- Cause: forgot `--markdown` flag
- Fix: re-run with `--markdown --replace`. Note: this OVERWRITES the doc, so any manual edits are lost.

### Doc doubled (content repeated)
- Cause: used `--replace` on a doc that already had content, then app run AGAIN without `--replace`
- Fix: every call MUST include both `--replace` and `-f`. The default is append.

### Backticks stripped
- Cause: passed content via argv instead of `-f`
- Fix: write to `/tmp/<file>` first via `write_file` tool, then `gog docs write -f /tmp/<file>`

## Verification commands

After every write, run all three:

```
gog docs info <docId>
gog docs cat <docId> | wc -l
gog docs cat <docId> | grep -c "PART "
```

The third command is the strongest verification — `PART ` (with trailing space) is unique to the master-doc header structure and won't false-positive on source markdown content.

## Useful adjacent commands

```bash
# List existing docs (returns 20 per page)
gog drive ls -j | python3 -c "import json, sys; d = json.loads(sys.stdin.read()); print('\n'.join(f\"{f['id']} | {f['name']}\" for f in d.get('files', [])))"

# Search by name
gog drive ls -j | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
for f in d.get('files', []):
    if 'god of murder' in (f.get('name') or '').lower():
        print(f.get('id'), '|', f.get('name'))
"

# Create new doc
gog docs create "Title Here" 2>&1 | head -10

# Append (for chunking large docs)
gog docs insert <docId> "<content>"  # content here is smaller per-call, no flags needed

# Replace (full overwrite with markdown conversion)
gog docs write <docId> -f /tmp/file.md --replace --markdown

# Read back
gog docs cat <docId>         # plain text
gog docs info <docId>        # metadata + revision ID
gog docs export <docId> --format txt > /tmp/doc.txt   # exported text
```

## Companion CLI: gws vs gog

Per `google-credentials-fallback` skill:
- **`gog`** — $USER@gmail.com personal OAuth. WORKS for personal shared docs (create + read + write). Use this.
- **`gws`** — firebase-adminsdk service account. 403s on personal shared docs. Use for Google Workspace org docs only.

For personal Google Doc work (this skill's scope), ALWAYS use `gog`.

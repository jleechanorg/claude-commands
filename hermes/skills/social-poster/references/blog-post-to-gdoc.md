# Blog-Post Drafting → Google Docs (gws + fallback patterns)

**Context:** When the user asks for "a 500-word post in Google Docs as a draft", the canonical path is `gws docs create` via the `google-workspace` skill. If `gws` OAuth isn't authenticated (the common case for a fresh Mac), the workflow degrades to a local markdown file + manual paste-into-gdoc recipe.

## Path A — `gws` authenticated (canonical)

```bash
# Verify OAuth first
python3 ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --check
# Expected output: AUTHENTICATED

# Create a new gdoc with body content
gws docs documents create \
  --json '{"title":"disk_magician: regrowth-prevention series"}' \
  --format json
# Returns: {"documentId": "...", "title": "...", "url": "https://docs.google.com/document/d/.../edit"}

# Append the blog post text to the doc
DOC_ID="<documentId from above>"
gws docs documents batchUpdate \
  --json "$(cat <<'EOF'
{
  "documentId": "<DOC_ID>",
  "requests": [{
    "insertText": {
      "location": {"index": 1},
      "text": "<BLOG_POST_BODY_HERE>"
    }
  }]
}
EOF
)"
```

The `--json` body uses Google Docs `batchUpdate` API with an `insertText` request. The `text` field is plain text — for markdown formatting, split into multiple `insertText` + `updateParagraphStyle` requests.

## Path B — `gws` NOT authenticated (fallback used 2026-07-06)

When `setup.py --check` returns `NOT_AUTHENTICATED: No token at $HOME/google_token.json`, the path is:

1. **Write the blog post as a local markdown file** in the project's repo or a `roadmap/` subdir:
   ```bash
   # Example for disk_magician:
   $HOME/projects_other/disk_magician/roadmap/2026-07-06-regrowth-prevention-launch.md
   ```
   Markdown is portable, reviewable in PRs, and convertible to gdoc/Notion/Medium/etc. later.

2. **Surface the file path + word count** in the Slack/chat reply so the user knows where to find it.

3. **Tell the user the gws OAuth setup is needed** for automated gdoc creation. Pointer:
   ```bash
   python3 ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --client-secret /path/to/client_secret.json
   ```
   This is a 5-minute OAuth dance the user can do once and then `gws docs create` works indefinitely.

4. **Provide a 1-line paste-into-gdoc recipe**: open `https://docs.google.com/document/create`, paste the markdown, apply formatting via gdoc's "Normal text" + "Heading 1/2" dropdown (gdoc auto-converts `#` headings).

## Verifying the OAuth state

```bash
# Quick check — returns AUTHENTICATED or NOT_AUTHENTICATED
python3 ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --check

# Full gws call test (returns account email if authenticated)
gws about get --params '{"user":"me","fields":"user"}' 2>&1 | head -3
# OR for drive:
gws drive about get --params '{"fields":"user"}' 2>&1 | head -5
```

Note: `gws about` itself returns an error "Unknown service 'about'" — drive's `about.get` works as the auth probe.

## OAuth setup reminder (don't burn cycles on it without user approval)

The `google-workspace` skill's setup flow:
1. Create OAuth client at console.cloud.google.com (enable Drive API + Docs API + Sheets API + Gmail API + Calendar API + People API)
2. Download `client_secret_*.json`
3. Run `setup.py --client-secret <path>` → get auth URL
4. User opens URL, approves, pastes back the redirect URL
5. `setup.py --auth-code <url>` → token saved to `~/.hermes/google_token.json`

**DO NOT walk through this autonomously** unless the user explicitly says "set up gws OAuth". The 5-minute dance requires user interaction at the OAuth consent screen.

## Related

- `~/.hermes/skills/productivity/google-workspace/SKILL.md` — full gws/gapi reference
- `~/.hermes/skills/social-poster/references/aside-repl-session-state.md` — companion: how to verify Aside auth for social platforms
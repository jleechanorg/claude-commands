# MP4 evidence path — gist-raw-URL with clone-and-replace

**Class:** Captured local MP4 (screen recording, ffmpeg output, asciinema, etc.) → post as inline Slack attachment.

**Verified:** 2026-07-16, Cloud Build E2E demo, gist `77dd5406ec125ccb2a916c3a98787a4a`, MP4 SHA-256 `4825b98d0aff1e659b43f6db5c3ac6d7b936363072f8854e34252de9e281ed57`, 3,742,272 bytes, served as `application/octet-stream` from the gist raw URL.

**Why this matters:** The canonical `files.completeUploadExternal` 3-stage flow needs `files:write` scope on the bot token (or `files:write:user` on xoxp). On the jleechanai.slack.com workspace, **both tokens lack that scope** as of 2026-07-16. The third-tier gist fallback is the only path.

## The 3-step recipe

### Step 1 — Create placeholder gist via API

The `--data-binary @file` form is mandatory once the payload is >~3 MiB. For text-only placeholders the inline JSON `-d` form works:

```bash
GH_TOKEN=$(gh auth token)
PLACEHOLDER=$(curl -fsS -X POST "https://api.github.com/gists" \
  -H "Authorization: Bearer ${GH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d '{"description":"mp4 evidence placeholder","public":true,"files":{"placeholder.txt":{"content":"replace me"}}}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Placeholder gist: ${PLACEHOLDER}"
```

### Step 2 — Clone + replace + .gitattributes

**Critical:** add `.gitattributes` declaring the binary types as binary. Without it, git's text-conversion heuristic can mangle bytes (rare but observed in jpeg-heavy projects):

```bash
rm -rf /tmp/gist-push
git clone "https://${GH_TOKEN}@gist.github.com/${PLACEHOLDER}.git" /tmp/gist-push
cd /tmp/gist-push
git rm placeholder.txt
cp /path/to/real/recording.mp4 ./cb-demo-cloud-build-proof.mp4
cat > .gitattributes <<'EOF'
*.mp4 binary
*.png binary
*.jpg binary
*.gif binary
*.webp binary
*.pdf binary
EOF
git add .gitattributes cb-demo-cloud-build-proof.mp4
git -c user.email=cloudbuild-demo@local.invalid -c user.name='cb-demo' \
  commit -m 'add real MP4 binary'
git push origin HEAD
```

### Step 3 — Capture SHA + verify content-type + post

```bash
SHA=$(git rev-parse HEAD)
RAW_URL="https://gist.githubusercontent.com/jleechan2015/${PLACEHOLDER}/raw/${SHA}/cb-demo-cloud-build-proof.mp4"
curl -fsI "${RAW_URL}"
# Expected:
#   content-type: application/octet-stream
#   content-length: <size-in-bytes>
```

Then embed the URL directly in a Slack message body. Slack's URL unfurler detects `.mp4` from the file extension and renders inline even though `application/octet-stream` is generic:

```bash
curl -fsS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "{
    \"channel\": \"C09GRLXF9GR\",
    \"thread_ts\": \"1784229770.265099\",
    \"unfurl_media\": true,
    \"text\": \"Captioned MP4 proof:\n${RAW_URL}\"
  }"
```

## Pitfalls in this path (verified)

| Symptom | Cause | Fix |
|---|---|---|
| `OSError: [Errno 7] Argument list too long` from `subprocess.run` on the `curl -d '<json>'` invocation | JSON payload (base64 of MP4) exceeds macOS `ARG_MAX` (~256 KiB) | Use `--data-binary @/tmp/payload.json` so curl reads from disk |
| First gist push shows `content-type: text/plain; charset=utf-8` | Uploaded the binary via `api.github.com/gists` POST with `'encoding': 'base64'` — the storage layer treats base64 as utf-8 text | Use the clone-and-replace recipe above; only the API path corrupts binary |
| MP4 raw URL serves `content-type: application/octet-stream` (not `video/mp4`) | Expected — GitHub gists don't sniff video mime types for `*.mp4` | Slack still renders inline from `application/octet-stream` + `.mp4` extension. Verify with `curl -fsI` only to confirm it's NOT `text/plain` |
| `curl -fsI <raw_url>` returns 404 | Used the wrong SHA in the raw URL. The public HTML URL guesses wrong; the raw URL needs the actual commit SHA | `git clone` the gist, `git rev-parse HEAD`, then build the URL as `https://gist.githubusercontent.com/<user>/<id>/raw/<sha>/<file>` |

## When this path beats the canonical 3-stage flow

- `files:write` scope is missing on bot token AND xoxp user token (verified 2026-07-14, re-verified 2026-07-16)
- File is >10 MiB (some Slack workspaces cap at 1 GB but practical cap is lower for inline display)
- You want the same evidence URL to work in PR descriptions AND Slack thread (gists are public, embeddable in both)

## Pairing with `mp4-caption-burn` skill

If the MP4 needs captions burned in via ffmpeg drawtext BEFORE you run this recipe, see the `mp4-caption-burn` skill for the screen-recording → frame-dump → drawtext → h264 → MP4 pipeline (including the `:state` option-name collision and `:` option-separator pitfalls).
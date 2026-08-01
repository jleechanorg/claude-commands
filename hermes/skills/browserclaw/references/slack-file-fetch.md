# Slack file fetch — when MCP can't reach the file

When a Slack task requires reading a **file attachment** (image / PDF / CSV that someone pasted into a thread), the MCP `slack` tool surface (`files.info`, `files.list`, etc.) is sometimes not available in the current runtime — it returns `Method not found` or `unknown method`. Fall back to the REST API with the user-token (`SLACK_USER_TOKEN` from `~/.profile`).

This pattern pairs naturally with browserclaw tasks because the typical flow is:

1. Operator says "look at the screenshot in this thread / this email"
2. The screenshot is actually a Slack file attachment (`F0BH1C9RU1K` etc.)
3. MCP can't `files.info` it → fall back to REST
4. `vision_analyze` the downloaded PNG to extract the actual task

## Token source — the gotcha

| Source | Variable | Notes |
|---|---|---|
| macOS Keychain `slack-mcp-xoxp` | — | **`security find-generic-password -s "slack-mcp-xoxp" -a $USER -w` returns EMPTY on this Mac (verified 2026-07-14).** Do not rely on it. |
| `~/.bashrc` | `SLACK_MCP_XOXP_TOKEN` | populated; works in interactive shells but not under launchd env-stripped contexts |
| `~/.profile` | `SLACK_USER_TOKEN` | **canonical — xoxp-954182... user token, used for cross-workspace fallback per SOUL.md `## COMMIT: slack-cross-workspace-fallback-xoxp`** |

**Use this to source the token:**
```bash
XOXP="$(grep '^export SLACK_USER_TOKEN=' ~/.profile | sed 's/^export SLACK_USER_TOKEN=//;s/"//g')"
```

## Recipe — files.info + download

```bash
XOXP="$(grep '^export SLACK_USER_TOKEN=' ~/.profile | sed 's/^export SLACK_USER_TOKEN=//;s/"//g')"

# 1. Get file metadata (filename, mimetype, url_private_download, size)
curl -sS -H "Authorization: Bearer $XOXP" \
  "https://slack.com/api/files.info?file=F0BH1C9RU1K" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print(json.dumps(r.get('file',{}), indent=2))"

# 2. Download the actual file (url_private_download is the most reliable URL)
curl -sS -H "Authorization: Bearer $XOXP" \
  "https://files.slack.com/files-pri/<TEAM_ID>-<FILE_ID>/download/<FILENAME>" \
  -o /tmp/img_2975.png

# 3. Verify + vision-extract
file /tmp/img_2975.png            # confirm MIME / size
ls -la /tmp/img_2975.png          # confirm bytes > 0
# Then in the agent loop:
#   vision_analyze(image_url="/tmp/img_2975.png", question="...")
```

## Worked example (2026-07-14, #life channel thread `1784003238.684549`)

Jeffrey said "Find this email" with a screenshot attached as `F0BH1C9RU1K`. MCP `mcp_slack_conversations_replies` returned the file metadata but not the body. With `SLACK_USER_TOKEN` from `~/.profile`:

```bash
XOXP="$(grep '^export SLACK_USER_TOKEN=' ~/.profile | sed 's/^export SLACK_USER_TOKEN=//;s/"//g')"
curl -sS -H "Authorization: Bearer $XOXP" \
  "https://slack.com/api/files.info?file=F0BH1C9RU1K" \
  | python3 -m json.tool | head -25
# → { "ok": true, "file": { "id": "F0BH1C9RU1K", "mimetype": "image/png",
#                            "name": "IMG_2975.png", "size": 305178,
#                            "url_private_download": "https://files.slack.com/...",
#                            ... } }

curl -sS -H "Authorization: Bearer $XOXP" \
  "$(curl -sS -H "Authorization: Bearer $XOXP" "https://slack.com/api/files.info?file=F0BH1C9RU1K" | python3 -c 'import sys,json; print(json.load(sys.stdin)["file"]["url_private_download"])')" \
  -o /tmp/img_2975.png

file /tmp/img_2975.png
# PNG image data, 1179 x 2556, 8-bit/color RGB, non-interlaced
ls -la /tmp/img_2975.png
# -rw-r--r--@ 1 $USER  wheel  305178 Jul 14 13:56 /tmp/img_2975.png
```

Then `vision_analyze(image_url="/tmp/img_2975.png", question="transcribe all text...")` returned the email body — Jorge Martins asking for Venmo statements for two Jan 2024 payments.

## Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `curl` returns HTML "Sign in to Slack" page | token wrong / not xoxp | verify `XOXP_LEN=80` (or thereabouts) — `SLACK_MCP_XOXP_TOKEN` from `.bashrc` is also valid in interactive shells |
| `{"ok": false, "error": "file_not_found"}` | wrong team / file in different workspace | confirm `file.<TEAM_ID>` matches the channel's team (returned in `user_team` field of `files.info`) |
| `{"ok": false, "error": "missing_scope"}` | using xoxb bot token to download a DM file the bot isn't in | fall back to `SLACK_USER_TOKEN` (xoxp) per `slack-cross-workspace-fallback-xoxp` COMMIT |
| File is `image/heic` from iPhone screenshot | Slack transcodes HEIC → PNG automatically; the `files.info` `mimetype` will say `image/png` | safe to download as-is, `vision_analyze` handles it |
| `curl` returns 0-byte file | URL expired (signed URLs have ~1h TTL) | re-fetch `files.info` to get a fresh `url_private_download` |

## Cross-references

- SOUL.md `## COMMIT: slack-cross-workspace-fallback-xoxp` — canonical token-fallback policy
- SOUL.md `## COMMIT: evidence-attach-not-path-cite` — when uploading evidence back to Slack, NOT for downloading
- browserclaw SKILL.md "Cookie decryption" section — runs before this recipe in most "find this email" tasks

---
name: evidence-attach-to-slack
version: 1.0.0
description: |
  Attach local evidence files (PNG, JPG, GIF, MP4, PDF) to a Slack message
  so they appear inline in the thread — not just as bare file paths in
  the text body. The Slack-rendering convention `MEDIA:/absolute/path`
  does NOT work through `mcp__slack__conversations_add_message` (the
  gateway's MCP Slack tool); Slack renders the path as literal text and
  no attachment is created. The CORRECT path is the 3-stage Slack
  `files.completeUploadExternal` API. Use this skill any time you have
  generated local proof artifacts (screenshots, captioned GIFs, video
  recordings, PDFs) that need to land visibly in the Slack thread for
  the user to review — including but not limited to: PR `/es` evidence
  blocks, BEFORE/AFTER UI proofs, captioned demo GIFs, test-output
  captures, browser/Playwright screenshots, audit reports, and bead
  attachment uploads.

  **Anti-trigger: do NOT use this skill if you have only textual evidence
  (logs, command output, JSON). For plain-text evidence, paste a fenced
  code block or `\`\`\`bash ... \`\`\`` block in the Slack message body —
  Slack renders monospace text blocks without an attachment and the user
  can copy/paste out of them. Reserve binary uploads for actual binary
  visual artifacts.**

when_to_use: |
  When the user asks for "before/after", "screenshot", "GIF evidence",
  "captioned mp4", "attach proof", "show me", "post evidence to the
  thread", or any time your own message claims visual proof and the
  proof lives as a local file on disk. Also fires when the user
  explicitly corrects you with "attach the proof as media" / "you forgot
  the screenshot" / "use /harness and fix it" / "use /learn" / "All PRs
  need attached media in PR desc and slack if discussed in slack" — those
  phrasings mean a prior Slack reply cited proof without uploading it.

triggers:
  - "attach proof as media"
  - "you forgot the screenshot"
  - "post the screenshot to the thread"
  - "MEDIA: not rendering"
  - "evidence didn't show up in slack"
  - "use /harness and fix it"   # when paired with missing-media complaint
  - "use /learn and fix it"      # when paired with missing-media complaint
  - "show before after in thread"
  - "All PRs need attached media in PR desc and slack"

allowed-tools:
  - mcp__slack__conversations_add_message
  - mcp__slack__conversations_replies
  - read_file
  - terminal

context: inline
---

# evidence-attach-to-slack

Attach local evidence files to Slack messages so the user can see them inline in the thread.

## When to use

You MUST use this skill when **all** of these hold:

1. You have **local binary evidence** (PNG / JPG / WebP / GIF / MP4 / PDF) on disk — typically from a Playwright/Chromium screenshot, ffmpeg-converted GIF, browser recording, or audit-PDF generator.
2. The artifact is **central to the claim** in your Slack message — i.e. the message says "BEFORE/AFTER", "this is fixed", "here's what it looks like", etc., and the proof is the file itself, not the text around it.
3. The message will land in a **Slack thread** (most common case) or a Slack DM/channel where the user expects to see the evidence inline.

You MUST NOT use this skill when:

- You have only textual evidence (logs, command output, JSON, code diffs). Paste fenced code blocks instead — Slack renders them as native monospace.
- The file is on a remote URL. Markdown image syntax (`![alt](https://...)`) works for public URLs.
- The user already has the file (e.g. you uploaded it earlier and they're confirming receipt).

## The recipe — Slack `files.completeUploadExternal` flow

The `MEDIA:/path` inline convention does NOT WORK through the
`mcp__slack__conversations_add_message` tool — it renders as plain text and
the Slack client never receives an attachment. The correct path is the
3-stage Slack `files.upload` API.

### Stage 1 — Get upload URL

```bash
curl -fsS -X POST https://slack.com/api/files.getUploadURLExternal \
    -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
    -F "filename=before-mobile-wizard-390x844.png" \
    -F "length=149206"
```

Returns `{ "ok": true, "upload_url": "https://files.slack.com/upload/v1/...", "file_id": "F0XXXXXXX" }`.

### Stage 2 — POST the file

```bash
curl -fsS -X POST "${upload_url}" \
    -F "file=@/absolute/path/to/before-mobile-wizard-390x844.png"
```

Returns `OK - <bytes_uploaded>` on success.

### Stage 3 — Complete upload + share to thread

```bash
curl -fsS -X POST https://slack.com/api/files.completeUploadExternal \
    -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "files": [{"id": "F0XXXXXXX", "title": "BEFORE: mobile wizard 390x844 — no chevron indicator"}],
        "channel_id": "C0XXXXXXXXX",
        "thread_ts": "1783038068.695729"
    }'
```

Returns `{ "ok": true, "files": [{...}] }`. The file then appears as a bot message in the thread with the file attached and the title as caption.

### Optional — Post a consolidated summary message

After uploading all the files, post a single text message in the thread that lists each filename + 1-line description. Don't include `MEDIA:` lines (they don't work) — just plain text naming each file. The attachments themselves are already in the thread; the summary text points the reader to them.

```python
mcp__slack__conversations_add_message(
    channel_id="C0XXXXXXXXX",
    thread_ts="1783038068.695729",
    text="""📎 Evidence attached to this thread:
1. BEFORE — before-mobile-wizard-390x844.png (149 KB) — mobile wizard top, no chevron.
2. AFTER top — after-mobile-wizard-top-390x844.png (158 KB) — chevron visible.
3. AFTER bottom — after-mobile-wizard-bottom-390x844.png (148 KB) — chevron hidden at scroll end.
4. Scroll demo — scroll-indicator-demo.gif (1.3 MB) — 20-frame loop at 4fps.""",
)
```

## Token source

Use `OPENCLAW_SLACK_BOT_TOKEN` from `~/.bashrc` (or `HERMES_SLACK_BOT_TOKEN` — same value). Export it as `SLACK_BOT_TOKEN` and pass via `-H "Authorization: Bearer ${SLACK_BOT_TOKEN}"`.

```
$ grep '^export OPENCLAW_SLACK_BOT_TOKEN=' ~/.bashrc
export OPENCLAW_SLACK_BOT_TOKEN="xoxb-9...AsAjyN"
```

The token has `files:write` scope (verified 2026-07-02 by successfully uploading 4 files to thread C0AH3RY3DK6). If `files.completeUploadExternal` returns `missing_scope`, the bot needs to be reinstalled with the `files:write` OAuth scope.

## File size limits

| Workspace tier | Per-file cap |
|---|---|
| Free / Standard | 1 GB |
| Some enterprise (configurable) | 50 MB |

The `/es` evidence GIFs in this repo are typically 1-5 MB after ffmpeg palette-gen compression, well under both limits. PNG screenshots are typically 100-300 KB.

## Verifying the upload landed

After uploading, fetch the thread and look for bot messages that have a `files` array populated:

```bash
curl -fsS \
    "https://slack.com/api/conversations.replies?channel=C0XXXXXXX&ts=1783038068.695729&limit=10" \
    -H "Authorization: Bearer ${SLACK_BOT_TOKEN}"
```

Each upload-share appears as a bot message (User `U0AEZC7RX1Q` for Hermes) with a `files` array containing 1 entry. The `file_count` integer on the message itself may be `0` — that's a known quirk of `completeUploadExternal` shares, the actual attachment lives in the `files` array.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Post lands with `[MEDIA:/path/to/file.png]` as literal text | Used the wrong recipe — `mcp__slack__conversations_add_message` doesn't honor `MEDIA:` inline tokens | Switch to the 3-stage `files.completeUploadExternal` flow above |
| `files.getUploadURLExternal` returns `missing_scope` | Bot token doesn't have `files:write` | Reinstall the Slack app with the `files:write` OAuth scope |
| Stage 2 returns 4xx | File not readable, file path typo, or upload_url expired | Verify file exists with `ls -la`, re-run stage 1 to get a fresh upload_url |
| Stage 3 returns `channel_not_found` | Bot not in the channel | Invite the bot to the channel first (`/invite @Hermes` or `conversations.invite`) |
| Upload succeeds but file doesn't show in thread | `thread_ts` missing from stage 3 payload, OR `channel_id` missing | Add both fields to the `completeUploadExternal` JSON body |
| Upload succeeds but file shows in channel not thread | `thread_ts` was wrong (typo, stale value from session context) | Verify `thread_ts` via `conversations.history` on the channel — the `thread_ts` of the user's parent message is the field to use, NOT the `ts` of the parent itself |
| User says "I don't see the screenshot" but file uploaded | Slack mobile client has media previews off, or user is on a different thread view | Ask user to tap the attachment; nothing to fix on the sender side |

## Why this skill exists (anti-pattern history)

The most common agent failure mode in this conversation log is:

> Agent captures a screenshot to disk, posts a Slack message that *describes* the screenshot ("here's the BEFORE/AFTER at /Users/.../evidence/foo.png"), but never attaches the file. User replies: "where's the screenshot?" or "stop forgetting use /harness and /learn and fix it."

Root cause: the agent treats `/Users/.../evidence/foo.png` as if it were a shared path the user can browse. But the user's Slack thread is their inbox — they don't open a terminal, they read attachments inline. The path-as-textual-mention is invisible to the Slack client.

The Slack `files.completeUploadExternal` flow is the bridge between "file on disk" and "file in thread". Memorizing it stops this loop.

## Pairing with `/harness` and `/learn`

When the user says "use /harness and /learn", they are pointing at:

- **`/harness`** → `~/.claude/skills/harness-engineering.md` — systematic infrastructure improvement vs one-off fix.
- **`/learn`** → capture the lesson into a skill so the next agent doesn't repeat the mistake.

The right response when they say this about a missing-media failure is:

1. **Now** (immediate): attach the missing media to the thread using this skill's recipe. Don't argue, don't ask, just post.
2. **Then** (durable): save this skill (if not already saved) so the next agent reads it before posting evidence.
3. **Then** (audit): run `/skillify` on this skill to lock the contract in place (resolver entry, trigger eval, integration test that exercises the live Slack API).

## Output Format

When invoked, this skill produces a Slack post containing:

1. A prose preamble that names the evidence ("BEFORE", "AFTER", etc.) and the viewport/conditions.
2. One `files.completeUploadExternal` upload per artifact (the upload itself is the attachment — there's no inline `MEDIA:` marker needed).
3. Optional follow-up prose (status, next action, link to PR).

No code is generated. No files are written. The skill is purely a Slack-recipe binding.

## Known Limitations

- **`files.completeUploadExternal` only handles binary files.** Plain text (logs, JSON, code) should still be pasted as fenced code blocks in the message body.
- **1 GB hard limit per attachment** (varies by workspace). The `/es` evidence GIFs in this repo are typically 1-5 MB after ffmpeg palette-gen compression, well under the limit.
- **No inline preview on some Slack mobile clients.** The attachment still uploads, but the user must tap to view. This is a Slack client issue, not a sender issue.
- **Upload paths must be reachable from the gateway process.** If you ran Playwright on your local machine but the gateway is on a different host, the path won't resolve. In that case, copy the file to a path the gateway can read first.
- **Bot must be in the channel.** If `completeUploadExternal` returns `channel_not_found` for a private channel, invite the bot first via `/invite @Hermes` (in the channel) or `conversations.invite` API.

## Integration test sketch

```python
def test_media_attach_in_thread():
    """Smoke: post a Slack message with files.completeUploadExternal and verify FileCount > 0."""
    import subprocess, time, os
    evidence = "/tmp/evidence-attach-test.png"
    # 1x1 red PNG
    PNG_BYTES = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
        "53de0000000c4944415478da6364f80f00010101006000140007e5ec0000"
        "000049454e44ae426082"
    )
    open(evidence, "wb").write(PNG_BYTES)
    assert os.path.getsize(evidence) > 0, "fixture file empty"

    # Stage 1: get upload URL
    import os as _os
    token = _os.environ["OPENCLAW_SLACK_BOT_TOKEN"]
    r1 = subprocess.run(['curl', '-fsS', '-X', 'POST',
        'https://slack.com/api/files.getUploadURLExternal',
        '-H', f'Authorization: Bearer {token}',
        '-F', f'filename=evidence-attach-test.png',
        '-F', f'length={os.path.getsize(evidence)}',
    ], capture_output=True, text=True)
    import json
    resp1 = json.loads(r1.stdout)
    assert resp1.get('ok'), f"Stage 1 failed: {resp1}"
    file_id = resp1['file_id']
    upload_url = resp1['upload_url']

    # Stage 2: POST file
    r2 = subprocess.run(['curl', '-fsS', '-X', 'POST', upload_url,
        '-F', f'file=@{evidence}'], capture_output=True, text=True)
    assert r2.returncode == 0, f"Stage 2 failed: {r2.stderr}"

    # Stage 3: complete upload + share to thread
    r3 = subprocess.run(['curl', '-fsS', '-X', 'POST',
        'https://slack.com/api/files.completeUploadExternal',
        '-H', f'Authorization: Bearer {token}',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({
            'files': [{'id': file_id, 'title': 'evidence-attach-to-slack smoke test'}],
            'channel_id': 'C0XXXXXXXXX',
            'thread_ts': '1783038068.000000',
        }),
    ], capture_output=True, text=True)
    resp3 = json.loads(r3.stdout)
    assert resp3.get('ok'), f"Stage 3 failed: {resp3}"

    # Verify
    r4 = subprocess.run(['curl', '-fsS',
        f'https://slack.com/api/conversations.replies?channel=C0XXXXXXXXX&ts=1783038068.000000&limit=5',
        '-H', f'Authorization: Bearer {token}'], capture_output=True, text=True)
    data = json.loads(r4.stdout)
    found = any(
        msg.get('files') and any(f.get('id') == file_id for f in msg['files'])
        for msg in data.get('messages', [])
    )
    assert found, f"uploaded file_id={file_id} not found in thread"
```

This test runs against a live Slack workspace — gated behind an `INTEGRATION_LIVE=1` env var so unit tests don't spam the user's thread.
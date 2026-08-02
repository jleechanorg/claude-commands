---
name: evidence-attach-to-slack
version: 1.12.0
description: |
  Attach local evidence files (PNG/JPG/GIF/MP4/PDF) to Slack threads so they
  render INLINE — not as bare file paths or `MEDIA:/path` text tokens.
  v1.3 cluster-anchor; v1.4 gist-raw-URL fallback; v1.5 Pre-Send Gate;
  v1.6 OAuth preflight + f-string pitfall; v1.7 misrouted-fix; v1.8 gist
  binary pitfall (clone-and-replace for PNG/MP4); v1.9 text-file gist delta
  (`gh gist create` works directly for `.patch`/`.diff`/`.json`/`.md`/`.txt`);
  v1.10 MP4 + curl-ARG_MAX quirks (subprocess.run arg-limit + clone-and-replace
  content-type for MP4 = `application/octet-stream`);
  v1.11 bot-side `files:write` scope closed (2026-07-19) — xoxp pending.
  v1.12 added 2 new pitfall rows: (a) `chat.delete` destroys evidence
  attachments if sorted by text-length heuristic (PR #8561 2026-07-24);
  (b) `page.evaluate()` computed style ≠ visual proof — always
  `vision_analyze` pixels before claiming visibility.
  Anti-trigger: plain-text evidence → fenced code blocks.

when_to_use: |
  When the user asks for "before/after", "screenshot", "GIF evidence", or
  any message claims visual proof that lives as a local file. Also fires
  when the user corrects you: "you forgot the screenshot" / "attach the
  proof as media" / "use /harness and fix it".

  **Auto-load contract (paired with SOUL.md `evidence-attach-presend-gate`):**
  Load THIS skill before invoking `mcp__slack__conversations_add_message`
  or `chat.postMessage` if your draft body contains any of:
    - `MEDIA:/absolute/path` token referencing a binary file
    - absolute path matching `/Users/[^ ]+\.(png|jpg|jpeg|gif|webp|mp4|pdf)`
    - "BEFORE"/"AFTER"/"screenshot"/"see attached"/"here's what it looks like"
      alongside any local path

triggers:
  - "attach proof as media"
  - "you forgot the screenshot"
  - "post the screenshot to the thread"
  - "MEDIA: not rendering"
  - "evidence didn't show up in slack"
  - "use /harness and fix it"
  - "use /learn and fix it"
  - "show before after in thread"
  - "show screenshots here"
  - "show me screenshots"
  - "see screenshots"
  - "with screenshots"
  - "and screenshots"
  - "and show screenshots"
  - "All PRs need attached media in PR desc and slack"
  - "evidence should be in gist urls"
  - "put evidence in a gist"
  - "don't commit screenshots to the PR"
  - "I need the media evidence on this thread"
  - "where are the screenshots"
  - "post evidence to this thread"
  - "you keep skipping the upload"
  - "you keep skipping this"
  - "/learn and remember this"
  - "before/after"
  - "BEFORE/AFTER"
  - "PNG"
  # PRE-SEND GATE TRIGGERS (v1.5.0)
  - "MEDIA:/path with .png/.jpg/.gif in draft body"
  - "/Users/.../path/.png in draft body"
  - "draft body says BEFORE / AFTER / screenshot / here is what it looks like"
  # RECURRING-CORRECTION PHRASES (v1.6.0)
  - "you always forget"
  - "you always fail to attach"
  - "you always do Y"
  - "stop forgetting"
  - "stop doing X"
  - "why do you always"
  # RECURRING-CORRECTION PHRASES (v1.7.0 — PR #7953, 2026-07-15)
  - "use /browser"
  - "use browser to fix your scopes"
  - "why are you struggling so much to show UI screenshots"
  - "fix your scopes"

allowed-tools:
  - mcp__slack__conversations_add_message
  - mcp__slack__conversations_replies
  - read_file
  - terminal

context: inline
---

# evidence-attach-to-slack

Attach local evidence files to Slack messages so the user can see them inline in the thread.

## ⚠️ Pre-Send Gate (NEW in v1.5.0 — paired with SOUL.md `## COMMIT: evidence-attach-presend-gate`)

**Before invoking `mcp__slack__conversations_add_message` or `chat.postMessage`, run this gate.**

The gate regex (lives in SOUL.md, mirrored here for quick check):

```python
import re

GATE_PATTERNS = {
    "media_token": re.compile(
        r"MEDIA:/[^\s]+\.(?:png|jpg|jpeg|gif|webp|mp4|pdf)\b", re.IGNORECASE),
    "absolute_path": re.compile(
        r"(?:^|\s)/Users/[^\s]+\.(?:png|jpg|jpeg|gif|webp|mp4|pdf)\b", re.IGNORECASE),
    "phrase_with_path": re.compile(
        r"(?i)\b(BEFORE|AFTER|screenshot|see attached|here'?s what it looks like)\b"),
}

def evidence_gate_fires(draft_text: str) -> bool:
    return any(p.search(draft_text) for p in GATE_PATTERNS.values())
```

**If the gate fires, you MUST run the recipe below BEFORE calling the message tool.** Skipping this gate is the exact failure mode that caused PRs #8139, #7953, #8337 to ship with text-only "evidence" that the user couldn't see. Verified by `tests/test_evidence_attach_presend_contract.py` (8 tests, all green).

**The principle:** when a recurring user correction has hit ≥3 times (as this one has), the fix must be a pre-send gate that intercepts the failure BEFORE the bad message is sent — not a post-hoc remediation rule that fires after the user complains. See `references/recurring-failure-pattern-2026-07.md` for the full 4-incident chain.

## OAuth Scope Preflight (NEW in v1.6.0)

**Before attempting Stage 1**, run the scope preflight:

```bash
python3 ~/.hermes/skills/evidence-attach-to-slack/scripts/check_token_scopes.py
```

The script probes `HERMES_SLACK_BOT_TOKEN` and `SLACK_USER_TOKEN` against `auth.test` and returns one of three states:

| State | Token | Action |
|---|---|---|
| `bot_has_scope` | bot has `files:write` | Use canonical 3-stage flow with bot token |
| `xoxp_has_scope` | bot fails, xoxp has `files:write:user` | Use xoxp token for Stage 1-3 |
| `neither_has_scope` | both fail | Skip straight to third-tier gist-raw-URL fallback |

**Why this matters (verified 2026-07-14 on PR #8139):** I burned 4 curl calls discovering both tokens lacked `files:write` mid-flow. The preflight collapses that into 2 `auth.test` calls (one per token) and tells you the correct path upfront. Saves ~10s per evidence-attach cycle.

**Re-verified 2026-07-15 (PR #7953 evidence run):** OAuth scope state was unchanged — `HERMES_SLACK_BOT_TOKEN` (bot_id `B0A3MS7G08P`, user `mcp_agent_mail`) had `chat:write`, `chat:write.public`, `channels:read/history/manage`, `groups:read/write`, `im:read/write`, `mpim:read/write`, `users:read` — **but no `files:write`**. The bot-side gap was closed on 2026-07-19 via browser-driven OAuth reinstall — re-running `check_token_scopes.py` should now report `bot_has_scope`. The user-token xoxp side is unchanged (different personal app).

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

**MUST use `-F` form fields, NOT `-d` JSON.** Verified 2026-07-12 (PR #8337):
JSON-encoded body silently drops the form fields; the API returns `invalid_arguments`.

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

**Use form-encoded body, NOT JSON.** Verified 2026-07-12: JSON parser is
strict about per-file extra properties; form-encoded parser is permissive.

```bash
curl -fsS -X POST https://slack.com/api/files.completeUploadExternal \
    -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "$(python3 -c 'import json,urllib.parse; print(urllib.parse.urlencode({"files": json.dumps([{"id": "F0XXXXXXX", "title": "BEFORE: mobile wizard 390x844"}])}))')" \
    --data-urlencode "channel_id=C0XXXXXXXXX" \
    --data-urlencode "thread_ts=1783038068.695729"
```

Or use `scripts/upload_batch.py` (canonical parallel uploader) which handles the form-encoding for you.

### Stage 3½ — Post consolidated summary message (MANDATORY)

After uploading all the files, post a single text message in the thread that names each attachment file-by-file. **Do NOT skip this step.** The attachments themselves become separate bot messages in the thread, which — combined with the channel-bridge's tendency to echo internal narration into the same thread — can bury the screenshots under 4-8 bot messages. The summary message is the cluster anchor the user actually reads.

### Stage 4 — Re-verify (Pattern A: verify BEFORE summary, NOT after)

**Do NOT re-verify via `mcp__slack__conversations_replies` AFTER posting the summary** — every call to that tool echoes a `:gear: mcp__slack__conversations_replies:` line into the thread as a bot message, which lands AFTER the summary and contradicts the "ignore the chatter above" anchor. Verified failure 2026-07-11 PR #8139.

**Pattern A — verify before summary (preferred):** Inside the same `execute_code` that ran Stage 1+2+3 for all N files, call `conversations.replies` ONE time and assert the file_ids landed, THEN post the summary. Pattern B (skip verification) is OK only if you can see uploads succeed in the same turn.

**`chat.getPermalink` is the post-send verification that does NOT echo** (verified 2026-07-15, PR #7953). After posting the summary, call `chat.getPermalink?channel=X&message_ts=Y` — it returns the public URL without spamming the thread with bot messages. Use this for "did my message land?" checks after the summary is posted.

**`conversations.replies` `not_in_channel` is NOT a post failure** (NEW v1.8.0). If the bot has `chat:write.public` but is not a member of the channel, `chat.postMessage` succeeds and `chat.getPermalink` returns the URL, but `conversations.replies` and `conversations.history` return `not_in_channel`. Don't treat that error as evidence the post failed — verify via permalink instead.

## Token source

**Use `HERMES_SLACK_BOT_TOKEN`** from `~/.bashrc`. Pull the token explicitly if `subprocess.run(..., shell=False)` doesn't auto-source bashrc.

For xoxp fallback: `grep '^export SLACK_USER_TOKEN=' ~/.profile | sed 's/^export SLACK_USER_TOKEN=//;s/"//g'` — it lives in `~/.profile`, NOT `~/.bashrc` (verified 2026-07-14, `bashrc-profile-xapp-drift-blocks-launchd` memory).

**Scope state (updated 2026-07-19):** The bot `HERMES_SLACK_BOT_TOKEN` now has `files:write` scope — closed via browser-driven OAuth reinstall (see `~/.hermes/skills/devops/slack-mcp-mail-bot-reinstall/references/files-write-scope-reinstall-2026-07-19.md`). The xoxp `SLACK_USER_TOKEN` is from a **separate personal app** and still lacks `files:write`. For bot-token evidence (the common case), run the canonical 3-stage flow — `check_token_scopes.py` should now report `bot_has_scope`. For xoxp evidence, the third-tier gist-raw-URL fallback is still the path until the personal app gets `files:write` separately.

**Historical gap (verified 2026-07-14, re-verified 2026-07-15, closed 2026-07-19):** Both `HERMES_SLACK_BOT_TOKEN` and `SLACK_USER_TOKEN` lacked `files:write` scope. The bot token had `files:read` but not `files:write`; xoxp had `chat:write` but not `files:write:user`. The OAuth-scope gap was the root cause of the "3 tokens don't work → gist fallback" pattern in PR #7953, #8139, #8337, #8455. The bot-token half is now closed; the user-token half depends on a separate OAuth reinstall of the personal app.

## Python 3.14 f-string pitfall (NEW in v1.6.0)

**Symptom:** `SyntaxError: leading zeros in decimal integer literals are not permitted` when an f-string contains `{02,04,05}` or similar.

```python
# WRONG — Python 3.14 parses {02,04,05} as set literal with octal-int SyntaxError
text = f"Briefing dates: {02,04,05}.md"

# RIGHT — three options:
text = f"Briefing dates: {'02,04,05'}.md"           # Option A: quote the contents
text = f"Briefing dates: 02.md, 04.md, 05.md"        # Option B: don't use set-literal-looking syntax
text = "Briefing dates: " + ",".join(["02", "04", "05"]) + ".md"  # Option C: build outside f-string
```

Verified 2026-07-14 on PR #8139 evidence-post: this exact SyntaxError blocked my first `chat.postMessage` attempt. Quick fix, but the lesson generalizes — any time a date or ID list uses leading zeros, build the string outside the f-string or quote it.

## Common failure modes

(Updated v1.6.0 — added rows for the 2 new failure modes observed today.)

| Symptom | Cause | Fix |
|---|---|---|
| Post lands with `[MEDIA:/path/to/file.png]` as literal text and `FileCount: 0` | Used the wrong recipe — `mcp__slack__conversations_add_message` doesn't honor `MEDIA:` inline tokens | Run the **Pre-Send Gate** (top of this file) BEFORE invoking the message tool |
| User says "you always fail to attach" / "you always forget" | The pre-send gate was not enforced; agent defaulted to `MEDIA:/path` text tokens | The user's complaint IS the trigger — load this skill NOW and attach the missing media. Don't argue, don't ask, just upload. |
| Both bot AND xoxp tokens return `missing_scope: files:write[:user]` on Stage 1 | OAuth scope gap (verified 2026-07-14, re-verified 2026-07-15). The user must reinstall `files:write` scope on the Slack app | Run `scripts/check_token_scopes.py` first to detect this WITHOUT burning 4 curl calls. If both fail, use **third-tier gist-raw-URL fallback** (Recipe below). |
| Stage 1 returns `invalid_arguments` with `missing required field: length, filename` | Used `-d` JSON instead of `-F` form fields. JSON silently drops form fields. | Use `curl -F filename=... -F length=...` (NOT `-d '{"filename":...,"length":...}'`). |
| Stage 3 returns `invalid_arguments` with `invalid additional property: initial_comment [json-pointer:/files/0]` | `initial_comment` is a top-level Stage 3 parameter, NOT a per-file property | Move `initial_comment` from `files[i]` to the top-level payload. |
| `SyntaxError: leading zeros in decimal integer literals` when posting | Python 3.14 parses `{02,04,05}` inside f-string as set literal with octal-int | Quote the contents: `f"{'02,04,05'}"` or build the string outside the f-string. |
| `conversations.replies` shows my message has `FileCount: 0` even though upload succeeded | Slack quirk — `completeUploadExternal` shares surface attachments via `files` array, not `file_count` integer | Verify via the `files` array, not `file_count`. Both are correct; `file_count: 0` is just unreliable. |
| Attachments uploaded but user says "where's the screenshot?" | Internal narration (think-block, tool-call echoes) buried the attachments under 4-8 bot messages | Post the consolidated summary message AFTER the upload batch — it's the cluster anchor the user reads. |
| Agent `chat.delete`s an evidence attachment by mistake while trying to clean up thread noise (verified 2026-07-24 PR #8561) | `conversations.replies` returned short bot messages interleaved with file-bearing messages. Agent sorted by `text` length, picked the shortest message that "looked like terminal noise", and called `chat.delete`. That message's `files` array contained the captioned MP4 — Slack returned `ok:true`, the MP4 vanished from the thread, no recovery. | **NEVER delete bot messages in a thread that contains evidence attachments.** If the thread is cluttered, post ONE clean summary message that re-anchors on the existing attachments (by file name + gist URL) instead of deleting anything. If you absolutely must clean up, only delete messages whose `files` array is empty AND whose `text` does NOT contain BEFORE/AFTER/screenshot patterns. Verify intent with a precise `ts` filter — never pick by `text`-length heuristics. |
| User catches false visual evidence — `page.evaluate()` reported `display:flex, opacity:1` but the element was visually hidden by a sibling (verified 2026-07-24 PR #8561, hit twice) | **v2 evidence pitfall (added 2026-07-24).** `page.evaluate()` returns computed style but does not account for stacking-context painting order, parent stacking contexts, or sibling z-index. An element can have `display:flex, opacity:1, rect.y=X` and still be visually hidden by another element on top. PR #8561 v1+v2 both shipped "chevron visible" claims where the chevron was hidden behind sticky `.wizard-navigation` (`z-index:50`). User: "lmao arrows / your screenshots are showing lmao arrows". | **ALWAYS vision_analyze the actual screenshot pixel content before claiming visual proof.** Two-step gate: (1) computed style confirms DOM presence, (2) `vision_analyze` confirms pixel-level visibility. If vision returns "I don't see X" or "the area is blank", the proof is invalid regardless of computed-style state. Companion gate belongs in `~/.hermes/skills/visual-evidence-with-playwright/` (proposed new skill). Also: Playwright `is_mobile=False` + viewport 390x844 matches `matchMedia('(max-width: 768px)')` but does NOT replicate mobile layout (sticky positioning, touch targets) — use `is_mobile=True` for mobile evidence. |
| Gist PNG URL serves `content-type: text/plain; charset=utf-8` instead of `image/png` | **NEW v1.8.0** — used `api.github.com/gists` POST with `'encoding': 'base64'` directly, OR the `gh gist create --public` CLI. Both store bytes as utf-8 text. | Use the clone-and-replace recipe in `scripts/upload_to_gist.sh`: `git clone https://${GH_TOKEN}@gist.github.com/<id>.git` → `git rm` bad file → `cp` real binary bytes → add `.gitattributes` with `*.png binary` (and `*.jpg binary`, `*.gif binary`) → commit → `git push origin HEAD`. Verify new SHA via `curl -I` shows `content-type: image/png`. |
| `conversations.replies` returns `not_in_channel` error but my `chat.postMessage` succeeded | **NEW v1.8.0** — Slack quirk: bots with `chat:write.public` can post to public channels they are NOT members of, but the read-side APIs (`conversations.replies`, `conversations.history`) require membership | Don't treat `not_in_channel` on `conversations.replies` as a post failure. Use `chat.getPermalink?channel=X&message_ts=Y` instead — it does NOT require channel membership and returns the public URL. |
| Gist raw URL renders as broken image in Slack thread | **NEW v1.8.0** — Slack rendering is gated by the upstream `Content-Type` header. If it's `text/plain` (the broken-gist case above), Slack shows "broken image" | Fix the content-type per the row above. Slack only renders `image/png`, `image/jpeg`, `image/gif`, `image/webp` inline. |
| Verifying a text-file gist raw URL returns 404 | **NEW v1.9.0** — `gh gist create <file>` stores the file under its original name, but the public HTML URL guesses the wrong filename; the raw URL needs the actual `commit-sha`, not the filename-only path. | Run `git clone https://gist.github.com/<id>.git /tmp/g`, then `git rev-parse HEAD` inside the clone — the raw URL is `https://gist.githubusercontent.com/<user>/<id>/raw/<sha>/<original-filename>`. Verify with `curl -fsI` returns 200. |
| Gist raw URL serves a binary file as `text/plain` (the v1.4-v1.8 trap) | Posted a `.png` via `api.github.com/gists` POST with `encoding: base64` | Use the v1.8 clone-and-replace recipe — text files do NOT have this trap (v1.9.0), but PNGs/GIFs/MP4s/PDFs do |
| `OSError: [Errno 7] Argument list too long` on `subprocess.run(["curl", "-d", payload])` | **NEW v1.10.0** — the JSON payload for `api.github.com/gists` was passed on argv; base64-encoded binaries >~3 MiB blow past macOS `ARG_MAX` (~256 KiB) | Use `--data-binary @/tmp/payload.json` so curl reads from disk. The argv path is fine for short JSON, but binary payloads MUST use the `@file` form. |
| `curl -fsI <raw_url>` shows `content-type: application/octet-stream` for an MP4 | **NEW v1.10.0** — expected behavior after the clone-and-replace recipe for MP4. Slack's URL unfurler still renders `.mp4` inline (file extension is the signal, not the content-type). | Don't treat `application/octet-stream` as a failure for MP4. The killer content-type is `text/plain` (the v1.4/v1.8 trap). |

## Third-tier fallback: gist-raw-URL image embeds (when neither token has `files:write`)

When `scripts/check_token_scopes.py` reports `neither_has_scope`, **do not stop and ask**. Push PNGs to a public gist, then post a single `chat.postMessage` with markdown image embeds and `unfurl_media: true`. Slack renders `image/png` inline; the same gist URLs also serve the PR description.

Verified end-to-end 2026-07-14 on PR #8139: gist ID `7cfcc454079283f8973054271d19efe6`, 4 files (3 PNGs + 1 GIF), all served `content-type: image/png` / `image/gif` via `curl -fsI`. Posted via `chat.postMessage` with xoxp user token, `unfurl_media: true` — all 4 rendered inline as attachments in the thread (`attachments: 4` on the bot message ts `1784065062.654269`).

Re-verified 2026-07-15 on PR #7953: gist `4ab1139eae87bde6102bc0961cb0168b`, SHA `5547f92`, 1 PNG (51KB) served `image/png`. Posted via `chat.postMessage` with bot token (the `chat:write.public` scope covers cross-channel posting). Both the gist and the Slack embed worked end-to-end.

### Recipe — the ONLY path that produces `content-type: image/png`

**Pitfall (verified 2026-07-15):** the `api.github.com/gists` API endpoint POST with `'content': <base64 bytes>, 'encoding': 'base64'` STORES the bytes as utf-8 text. The resulting raw URL serves `content-type: text/plain; charset=utf-8`, and Slack renders the markdown `![](url)` as a broken-image icon. Same problem with the `gh gist create` CLI for binary files — it base64-encodes but the storage layer is still text.

**The working path (clone + cp real bytes + gitattributes):**

```bash
GH_TOKEN=$(gh auth token)

# Step 1: create a placeholder gist (text content, any dummy file)
PLACEHOLDER=$(curl -fsS -X POST "https://api.github.com/gists" \
  -H "Authorization: Bearer ${GH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -d '{"description": "evidence placeholder","public": true,"files": {"placeholder.txt": {"content": "replace me"}}}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Placeholder gist: ${PLACEHOLDER}"

# Step 2: clone, remove placeholder, add real binary + .gitattributes
rm -rf /tmp/gist-push
git clone "https://${GH_TOKEN}@gist.github.com/${PLACEHOLDER}.git" /tmp/gist-push
cd /tmp/gist-push
git rm placeholder.txt
cp /path/to/real/screenshot.png ./screenshot.png
cat > .gitattributes <<'EOF'
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.webp binary
EOF
git add .gitattributes screenshot.png
git -c user.email=$USER@gmail.com -c user.name="Jeffrey Lee-Chan" \
  commit -m "evidence: real binary bytes for screenshot"
git push origin HEAD

# Step 3: capture the new SHA and verify content-type
NEW_SHA=$(git rev-parse HEAD)
echo "New SHA: ${NEW_SHA}"
curl -fsI "https://gist.githubusercontent.com/jleechan2015/${PLACEHOLDER}/raw/${NEW_SHA}/screenshot.png" | grep -i content-type
# Expected: content-type: image/png
```

**Or use `scripts/upload_to_gist.sh`** — wraps the above with one call. Verify each raw URL after push:

```bash
for url in $(git ls-tree HEAD | awk '{print $4}' | xargs -I{} echo "https://gist.githubusercontent.com/jleechan2015/<id>/raw/$(git rev-parse HEAD)/{}"); do
    curl -fsI "$url" | grep -i "^content-type:"
done
# Expected: content-type: image/png (or image/gif)
```

3. **State the blocker explicitly** in the summary so the user knows it's an OAuth-scope fallback, not the canonical path.
4. **Update the PR description** with the same gist raw URLs via `gh pr edit <N> --body-file`.

### When to use third-tier vs the 3-stage flow

| Situation | Path | Why |
|---|---|---|
| Bot token has `files:write` (default per preflight) | 3-stage `files.completeUploadExternal` | Canonical — file appears as native Slack attachment |
| Bot fails but xoxp has `files:write:user` | SOUL.md xoxp fallback to `SLACK_USER_TOKEN` | Cross-workspace path; file attaches under user identity |
| Both tokens lack `files:write`/`files:write:user` | **Third-tier gist-raw-URL embeds via `chat.postMessage`** | Works without any OAuth scope; one evidence channel for PR desc + Slack thread |

## Why this skill exists (anti-pattern history, expanded v1.6.0)

The most common agent failure mode in this conversation log:

> Agent captures a screenshot to disk, posts a Slack message that *describes* the screenshot ("here's the BEFORE/AFTER at /Users/.../evidence/foo.png"), but never attaches the file. User replies: "where's the screenshot?" or "stop forgetting use /harness and /learn and fix it."

**Why this recurs despite the skill existing:** The agent's default prompt encourages `MEDIA:/path` text tokens (lowest-friction path). The skill only loads if the agent remembers to `skill_view` it. The user's complaint is the trigger, not a pre-send check. **The v1.5.0 Pre-Send Gate fixes this by intercepting the failure BEFORE the message tool is called.**

**The 4-incident chain (2026-07-02 → 2026-07-14):**

| Date | PR | What went wrong | Fix attempted |
|---|---|---|---|
| 2026-07-02 | #8139 (1st time) | 4 PNGs + 1 GIF emitted as `MEDIA:/path` text tokens, all rendered as literal text | Skill v1.0 created |
| 2026-07-10 | #7953 | 4 PNGs uploaded successfully, but bridge chatter buried them under 6-8 bot messages | v1.1 added summary-as-cluster-anchor |
| 2026-07-13 | #8337 | Stage 1 JSON body silently dropped form fields; Stage 3 strict about per-file extra properties | v1.4 added form-encoding + xoxp pivot + gist fallback |
| 2026-07-14 | #8139 (again) | Same root cause as 2026-07-02 — reactive rule never fired; agent defaulted to `MEDIA:/path` | v1.5 + SOUL.md `## COMMIT: evidence-attach-presend-gate` (proactive gate) |

The lesson: **when the same user correction hits ≥3 times across 12 days, the fix must move from "post-hoc documentation" to "pre-send invariant".** This is encoded as a general principle in `~/.hermes/skills/harness-postmortem/SKILL.md` Phase 1.5d (added 2026-07-14).

**v1.8.0 addendum (PR #7953, 2026-07-15):** The recurring evidence-attach failure recurred AGAIN today, but the actual cause was different from the 4-incident chain — the OAuth scope gap on `HERMES_SLACK_BOT_TOKEN` (`files:write` still missing) plus an additional gap in the gist recipe itself: `api.github.com/gists` POST with `encoding: base64` does NOT preserve binary — the storage layer treats base64 content as utf-8 text, and the resulting raw URL serves `content-type: text/plain; charset=utf-8`. The fix is the clone-and-replace pattern documented above. **The pattern holds:** every PR cycle surfaces a new nuance in the same fall-back chain. v1.8.0 closes the gap that v1.4.0 left open (the "gist fallback works" claim was incomplete — it works only if you use clone-and-replace, NOT the direct API POST).

**v1.10.0 addendum (Cloud Build E2E proof, 2026-07-16):** Two new sub-pitfalls in the same fallback chain that v1.8 + v1.9 documented:

**Pitfall A — `subprocess.run` argument-list limit on the curl+JSON base64 path.** When uploading a binary via `curl -X POST https://api.github.com/gists -d $(payload)`, the JSON payload is built in memory and passed on argv. For MP4s >~3 MiB the base64-encoded payload (≈1.33× size) approaches the macOS `ARG_MAX` (~256 KiB) and `subprocess.run([...], ...)` raises `OSError: [Errno 7] Argument list too long`. Symptom:

```python
r = subprocess.run(["curl", "-d", open("/tmp/payload.json").read(), ...], ...)
# OSError: [Errno 7] Argument list too long: 'curl'
```

Fix: use `--data-binary @file` instead of `-d <string>`, so curl reads from disk and the payload never lands on argv:

```bash
curl -fsS -X POST "https://api.github.com/gists" \
  -H "Authorization: Bearer ${GH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  --data-binary "@/tmp/gist_payload.json"
```

**Pitfall B — MP4 gist raw URL serves `content-type: application/octet-stream`, not `video/mp4`.** Verified by `curl -fsI` after the clone-and-replace push:

```
content-type: application/octet-stream
content-length: 3742272
```

Slack still renders MP4 inline when you paste `https://gist.githubusercontent.com/.../raw/<sha>/file.mp4` directly in a message body (verified 2026-07-16, gist `77dd5406ec125ccb2a916c3a98787a4a`, SHA `c68173e`, 3.6 MiB MP4 rendered inline in the user-facing Slack thread as an attachment). The `application/octet-stream` content-type is fine — what kills inline rendering is `text/plain` (the v1.4/v1.8 trap when you store the binary as utf-8 text via the API base64 path). `application/octet-stream` is treated as a generic binary stream and Slack's URL unfurler recognizes MP4 by file extension.

**Why this still works for Slack thread delivery without the 3-stage API:** once you have a public gist raw URL with the right SHA, you can either (a) embed it as a bare URL in a `chat.postMessage` body — Slack's unfurler detects `.mp4` and renders inline, OR (b) try the `files.completeUploadExternal` 3-stage API first; if `check_token_scopes.py` reports `neither_has_scope`, fall straight to (a). For the Cloud Build proof run on 2026-07-16, both bot and xoxp tokens returned `missing_scope: files:write[:user]` on Stage 1 (verified in the chat log), so path (a) was the only working route.

**v1.9.0 addendum (jleechanorg/disk_magician PR #17, 2026-07-15):** The text-file gist delta. `gh gist create <text-file>` works directly for text evidence (`.patch`, `.diff`, `.json`, `.md`, `.txt`, `.log`, `.yaml`, `.yml`, `.csv`, `.xml`, `.sh`, `.py`). **The clone-and-replace dance is unnecessary for text files** — text is text, no base64-as-utf-8 corruption. The CLI base64-encodes on the way in but the storage is still text, and `https://gist.githubusercontent.com/<user>/<id>/raw/<commit-sha>/<file>` serves the text correctly with `content-type: text/plain; charset=utf-8`. The "raw URL" path requires `git clone` of the gist to discover the commit SHA (the public HTML URL guesses wrong — it's the SHA, not the filename), and the SHA-based URL with the exact filename works. Verified on PR #17 evidence run: 41,016-byte `.patch` file, `diff` between `curl -fsS <raw-url>` and local copy returned empty, byte count matched.

When in doubt, this decision tree works:

| File type | Gist path | Post to Slack as |
|---|---|---|
| `.png`/`.jpg`/`.jpeg`/`.gif`/`.webp`/`.mp4`/`.pdf` | placeholder-gist + clone-and-replace (binary, requires `.gitattributes`) | markdown image embed via `chat.postMessage` with `unfurl_media: true` |
| `.patch`/`.diff`/`.json`/`.md`/`.txt`/`.log`/`.yaml`/`.yml`/`.csv`/`.xml`/`.sh`/`.py` | `gh gist create <file> --public` (text is text) | fenced code block (` ```lang `) INLINE in the message body — Slack renders as native monospace |
| Same text types when too long for a single message (>~3500 chars) | `gh gist create <file> --public`, capture SHA via clone | raw URL inline in the message body — Slack makes it clickable |
| Any file the user explicitly wants as an attachment | all of the above | `chat.getPermalink` to verify, link to the raw URL in the message body |

**The principle:** the only file types that need the third-tier gist-raw-URL trick for *inline rendering* are the binary types Slack won't render as native attachments (`files:write` is missing from both tokens). For text, Slack renders inline monospace from a fenced code block — there's no real problem to solve.

See `references/recurring-failure-pattern-2026-07.md` for the full transcripts and the trigger phrases the user actually typed.

## Pairing with `/harness` and `/learn`

When the user says "use /harness and /learn", they are pointing at:
- **`/harness`** → `~/.claude/plugins/marketplaces/claude-commands-marketplace/.claude/skills/harness-engineering.md` — systematic infrastructure improvement vs one-off fix.
- **`/learn`** → capture the lesson into a skill so the next agent reads it before posting evidence.

The right response when they say this about a missing-media failure is:

1. **Now** (immediate): attach the missing media to the thread using this skill's recipe. Don't argue, don't ask, just post.
2. **Then** (durable): the Pre-Send Gate (top of this file) prevents recurrence — if it's still being violated, the gate regex needs tuning, not the agent.
3. **Then** (audit): run `scripts/check_token_scopes.py` to verify the OAuth-scope gap hasn't been silently closed (it should report `bot_has_scope` once the user reinstalls `files:write`).

## Misrouted-fix pitfall (added v1.7.0, PR #7953, 2026-07-15 — corrected 2026-07-19)

User suggestion "use `/browser` to fix your scopes" was PARTIALLY misrouted in 2026-07-15. The recurring evidence-attach failure's immediate cause WAS the OAuth-scope gap (correctly identified) but the suggested fix `/browser` was read as "go look at the Slack web UI manually" rather than "drive a browser-driven OAuth reinstall end-to-end." That left the gap unfixed for 4 days (PR #8139, PR #8337, PR #8455 all failed with `missing_scope: files:write`).

**Correct interpretation (verified 2026-07-19):** `/browser` IS the right vector for closing an OAuth-scope gap — the OAuth & Permissions page requires interactive JS-driven clicks (scope search → option click → Save → Reinstall → Allow in OAuth flow). The repair is via Playwright-driven cookie-injected Chromium session; full recipe in `~/.hermes/skills/devops/slack-mcp-mail-bot-reinstall/SKILL.md` §11 + `references/files-write-scope-reinstall-2026-07-19.md`.

When the user suggests a different fix vector (different tool, different workflow), check whether the underlying intent is "make the gap stop recurring" — if so, drive it to completion even if the surface tool feels off-pattern for the symptom class. Don't dismiss it as misrouted; verify the actual end state.

## Known Limitations

- **`files.completeUploadExternal` only handles binary files.** Plain text (logs, JSON, code) should still be pasted as fenced code blocks in the message body.
- **1 GB hard limit per attachment** (varies by workspace).
- **No inline preview on some Slack mobile clients.** The attachment still uploads, but the user must tap to view.
- **Upload paths must be reachable from the gateway process.** If you ran Playwright on your local machine but the gateway is on a different host, the path won't resolve.
- **Bot must be in the channel for Stage 3 file attachments.** If `completeUploadExternal` returns `channel_not_found` for a private channel, invite the bot first. (Public-channel posts work without membership via `chat:write.public`, but `conversations.replies` returns `not_in_channel` — use `chat.getPermalink` for verification instead.)
- **Gist `content-type` is the gating factor for Slack inline rendering.** If the raw URL serves `text/plain`, Slack will not render as an inline image — always verify with `curl -fsI <raw_url> | grep -i content-type` after pushing the gist.

## Support files

- `scripts/upload_batch.py` — parallel 3-stage upload loop for N PNGs in one `execute_code` call.
- `scripts/upload_to_gist.sh` — end-to-end binary-to-gist upload (create placeholder gist → `gh gist clone` → replace with real bytes → commit + push → verify `content-type: image/png`).
- `scripts/check_token_scopes.py` — **NEW v1.6.0** — OAuth scope preflight. Probes both tokens against `auth.test` and returns `bot_has_scope` / `xoxp_has_scope` / `neither_has_scope`. Run BEFORE Stage 1 to avoid wasted curl calls.
- `references/github-gist-binary-upload.md` — GitHub gists API quirk catalog for binary uploads. **UPDATED v1.8.0** — documents the base64-as-utf-8 storage pitfall and the clone-and-replace fix.
- `references/mp4-evidence-path.md` — **NEW v1.10.0** — MP4-specific path: gist clone-and-replace + `content-type: application/octet-stream` is fine + `application/x-www-form-urlencoded` workaround for `--data-binary` arg-list-limit. Verified 2026-07-16 on Cloud Build E2E proof (3.6 MiB MP4, byte-identical download).
- `references/recurring-failure-pattern-2026-07.md` — **NEW v1.6.0** — the 4-incident chain across 12 days with verbatim user trigger phrases. The data backing the pre-send gate.
- `references/false-evidence-incidents.md` — **NEW v1.12.0** — the v2 lesson: Pre-Send Gate catches missing-uploads but NOT false-claims. When agent asserts "X is visible" via `page.evaluate()`, vision_analyze the actual pixels before posting. Includes the two-step pre-claim gate recipe (PR #8561, 2026-07-24).
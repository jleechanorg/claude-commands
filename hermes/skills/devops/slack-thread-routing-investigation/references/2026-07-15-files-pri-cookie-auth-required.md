# 2026-07-15 — Failure 5g: `files-pri` Slack attachment download requires cookie auth, not bearer tokens

## Symptom

The user pastes a Slack attachment in a thread ("handle this patch", "review this diff") and the agent tries `curl -H "Authorization: Bearer ***" https://files.slack.com/files-pri/<id>/download/...`. Both `HERMES_SLACK_BOT_TOKEN` and `SLACK_USER_TOKEN` (xoxp) return a `302 Found` redirecting to `https://jleechanai.slack.com/?redir=%2Ffiles-pri%2F...` — the Slack login page HTML, not the file bytes. Verified twice in the same session: bot token xoxb returns a 152-byte `Found` HTML; user token xoxp returns a 61602-byte `Found` HTML (full login page). The agent now has the URL but cannot download the binary.

## Root cause

Slack's `files-pri.slack-edge.com` edge enforces cookie-based auth for attachment downloads even with a valid bearer token in the Authorization header. Bearer tokens work for `slack.com/api/*` calls (`conversations.postMessage`, `conversations.replies`) but not for the legacy `files-pri` redirect chain that powers attachments in the Slack client. The 302 to login.html is a defensive behavior — Slack will not hand a binary to a curl request that lacks the workspace session cookies.

## Why this matters here

When the user says "Handle if we didnt yet" and the message has a single ~70KB patch attachment, the agent's instinct is to download the patch via the attachment URL. In the 2026-07-15 session this failed twice in different ways:

1. The user-token URL does 302 to login.html
2. The bot-token URL also does 302 because Slack's edge sees a different bot context
3. Following the 302 to the login page produces NO useful bytes

## Two clean workarounds (both verified 2026-07-15)

### Workaround 1 — Cross-session `/tmp/` cache hit

When a prior session already downloaded the file via the Slack client or via `mcp__slack__*` tools (which use authenticated paths), it usually lands in `/tmp/<session-id>/<sha-or-name>.patch` or similar. Search `/tmp/` for filenames matching the attachment's name or the session's pattern. In this session: `/tmp/hermes_thread/sidekick-swarm-trim.patch` (67.7K, 654 lines) had been saved by the earlier session and was immediately usable.

Common `/tmp/` locations:

```
/tmp/hermes_thread/    # canonical patch / investigation artifacts
/tmp/openclaw/         # older openclaw-era scripts
/tmp/<session-id>/     # session-scoped scratchpad
```

Search recipe:

```bash
find /tmp -name "<attachment-basename>*" -size +1k 2>/dev/null | head
find /tmp -name "*${SHORT_SHA}*" 2>/dev/null | head
```

### Workaround 2 — `session_search` recall of the file's content

When no `/tmp/` cache exists, search past Hermes sessions for the file name, any quoted excerpts, or the parent context. The 9-store `/ms` fan-out (`memory-search` skill) often surfaces a session that quoted the file's key sections. In this session, `session_search(query='sidekick-swarm-trim-20260715-143103', limit=5)` returned the immediately-prior session's investigation — enough context to act on the patch without ever downloading the bytes.

```python
session_search(query="<attachment-basename>", limit=5)
# OR
skill_view(name='memory-search')  # 9-store fan-out
```

The returned bookends + window will let you reconstruct the file's key sections even when the binary is unavailable.

## Fallback ladder when handling a Slack attachment

Priority order (do NOT skip steps — this is short enough to run end-to-end):

1. Look for the file in `/tmp/` (see Workaround 1)
2. `session_search` + `/ms` for the file name or quoted excerpts (see Workaround 2)
3. If neither hits, ask the user to either (a) paste the file content inline, or (b) re-upload to a route the agent can fetch (gist URL the user can grant access to)
4. **Do NOT spend more than 1 tool call** trying direct `curl`/Authorization Bearer on `files-pri` — that path is documented broken. Skip directly to step 3 if both steps 1 and 2 miss.

## Verification: how to tell if your download ACTUALLY succeeded

A successful download is a 200 response with the file's content-type (e.g. `application/octet-stream`, `text/plain`, `text/x-diff`). A failed download is the 200 response with `text/html; charset=utf-8` and `<!DOCTYPE html>` body (the login page). Quick check:

```python
import subprocess
result = subprocess.run(
    ['curl', '-fsSL', url, '-H', f'Authorization: Bearer {token}', '-o', out, '-D', '-'],
    capture_output=True, text=True, timeout=20
)
# Check the saved file
with open(out) as f:
    head = f.read(64)
if head.startswith('<!DOCTYPE') or head.startswith('<html'):
    print('FAIL — got login page HTML, not file bytes')
elif 'Found' in head or 'redir' in head:
    print('FAIL — got 302 redirect landing page')
else:
    print('OK — got file content')
```

The headers file will show `HTTP/2 302` for the failed case (followed by an HTTP/2 200 to login page) and `HTTP/2 200` for the successful case.

## Why not fix at the gateway layer

The Slack MCP server at `127.0.0.1:8006` exposes `conversations_*` tools but NOT a `files_download` tool. Even if it did, it would still hit the same `files-pri` cookie-required edge. The durable fix is an MCP-side proxy that adds the Slack client cookies server-side, then forwards the bytes — but this is tracked as a future gateway enhancement, not as a skill-level recipe. For now, `/tmp/` cache + `session_search` recall are the canonical paths.

## Distinct from Failure 5f

5f blocks the **write path** (cannot post a reply). 5g blocks the **read path** (cannot download an attachment). The downstream symptoms look similar — agent stalls with no progress and the user wonders why nothing is happening — but the fixes are different:

| | Failure 5f (write) | Failure 5g (read) |
|---|---|---|
| **Block** | `chat.postMessage` returns `not_in_channel` / `missing_scope` | `files-pri` returns `302 Found` → login.html |
| **Pivot** | XOX-P user-token bearer | `/tmp/` cache or `session_search` |
| **Cost** | ~1 curl call to verify and pivot | ~2 tool calls (`find` + `session_search`) |
| **Sibling tip** | Read via `conversations_replies` works even when write fails | `conversations_replies` returns the attachment metadata (`name`, `size`, `url_private_download`) but not the bytes — useful for confirming the file exists before pivoting |

## Cross-references

- **SKILL.md Failure 5f** (this directory) — the "XOX-P user-token fallback" for the write-path block. The two failures often appear together: a thread with an attachment AND with a write-blocked recovery.
- **SOUL.md `## COMMIT: evidence-attach-to-slack`** — the inverse direction: attaching local evidence to a Slack thread via the 3-stage `files.completeUploadExternal` API. Symmetric problem, different fix.
- **`references/slack-thread-json-bot-user-filter.md`** — the JSON-parse quirks on `conversations.replies` responses that compound the read path. Often paired with 5g in the same session.
- **`references/2026-06-13-stale-fix-callback-instance-11.md`** — an example where `HERMES_SLACK_BOT_TOKEN` sourcing from `~/.bashrc` (not runtime env) was the difference between Path B working and failing. Same lesson: never trust the runtime env for tokens, always source from `~/.bashrc` via `bash -lc 'source ~/.bashrc && echo $TOKEN'`.

## Bug-ref

2026-07-15 16:50 PT — thread `C09GRLXF9GR / 1784163007.667409`, "Handle if we didnt yet" with attachment `sidekick-swarm-trim-20260715-143103.patch`. xoxb 302 Found 152 bytes; xoxp 302 Found 61602 bytes (full login HTML). Resolved via `/tmp/hermes_thread/sidekick-swarm-trim.patch` (saved by the 14:38 PT session that handled the initial `/advice` review).

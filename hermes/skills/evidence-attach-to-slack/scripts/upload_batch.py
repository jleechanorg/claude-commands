#!/usr/bin/env python3
"""upload_batch.py — upload N PNGs to a Slack thread via files.completeUploadExternal,
post a consolidated summary message, and re-verify the attachments are visible.

Use this from inside an `execute_code` call when you have a batch of BEFORE/AFTER
screenshots (typically 2–8 PNGs) to attach to one Slack thread. Doing all uploads
inside a single Python process avoids the per-iteration subprocess-spawn overhead
of looping with separate `terminal` or `mcp__slack__conversations_add_message`
calls, and returns a clean `(filename, ok|err)` results list.

v1.2.0 (2026-07-10): the post-upload summary + re-verify steps are now part of
this script. Verified 2026-07-10 on PR #7953 evidence drive — without these
two steps, the channel-bridge leaks internal narration into the thread and
attachments drift out of the user's viewport.

Recipe (the one proven in production 2026-07-10 with 4 PNGs in ~6s):

```python
import subprocess, json, os, time

TOKEN = os.environ.get("HERMES_SLACK_BOT_TOKEN") or subprocess.run(
    ["bash", "-lc", "source ~/.bashrc && echo $HERMES_SLACK_BOT_TOKEN"],
    capture_output=True, text=True,
).stdout.strip()

CHANNEL = "C0XXXXXXXXX"
THREAD  = "1783487114.025319"
EVIDENCE_DIR = "/path/to/screenshots"

files_to_upload = [
    ("BEFORE-mobile-390x844-top.png",    "BEFORE — mobile top — sticky button visible"),
    ("BEFORE-mobile-390x844-bottom.png", "BEFORE — mobile bottom — sticky button covering narrative"),
    # ... up to N
]


def upload_one(fname: str, caption: str) -> str | None:
    fpath = os.path.join(EVIDENCE_DIR, fname)
    if not os.path.exists(fpath):
        return None
    fsize = os.path.getsize(fpath)
    r1 = subprocess.run([
        "curl", "-fsS", "-X", "POST",
        "https://slack.com/api/files.getUploadURLExternal",
        "-H", f"Authorization: Bearer {TOKEN}",
        "-F", f"filename={fname}",
        "-F", f"length={fsize}",
    ], capture_output=True, text=True, timeout=30)
    resp1 = json.loads(r1.stdout)
    if not resp1.get("ok"):
        return None
    file_id, upload_url = resp1["file_id"], resp1["upload_url"]
    subprocess.run([
        "curl", "-fsS", "-X", "POST", upload_url, "-F", f"file=@{fpath}",
    ], capture_output=True, text=True, timeout=60, check=True)
    subprocess.run([
        "curl", "-fsS", "-X", "POST",
        "https://slack.com/api/files.completeUploadExternal",
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "files": [{"id": file_id, "title": caption}],
            "channel_id": CHANNEL,
            "thread_ts": THREAD,
        }),
    ], capture_output=True, text=True, timeout=30, check=True)
    return file_id


# Stage 1-3: upload batch
results = []
uploaded_ids = []
for fname, caption in files_to_upload:
    fid = upload_one(fname, caption)
    if fid:
        results.append((fname, "ok"))
        uploaded_ids.append(fid)
    else:
        results.append((fname, "missing-or-fail"))

# Stage 3.5: POST consolidated summary message
summary = "📎 Evidence attached to this thread:\n" + "\n".join(
    f"{i+1}. {f[0]} — {f[1]}" for i, f in enumerate(files_to_upload)
)
r = subprocess.run([
    "curl", "-fsS", "-X", "POST",
    "https://slack.com/api/chat.postMessage",
    "-H", f"Authorization: Bearer {TOKEN}",
    "-H", "Content-Type: application/json; charset=utf-8",
    "-d", json.dumps({"channel": CHANNEL, "thread_ts": THREAD, "text": summary}),
], capture_output=True, text=True, timeout=15)
summary_resp = json.loads(r.stdout)

# Stage 4: re-verify — attachments still present + summary is latest bot message
time.sleep(2)  # Slack eventual consistency on file-share attachments
verify_url = f"https://slack.com/api/conversations.replies?channel={CHANNEL}&ts={THREAD}&limit=100"
all_msgs = []
cursor = None
while True:
    url = verify_url + (f"&cursor={cursor}" if cursor else "")
    r = subprocess.run([
        "curl", "-fsS", url, "-H", f"Authorization: Bearer {TOKEN}",
    ], capture_output=True, text=True, timeout=15)
    data = json.loads(r.stdout)
    all_msgs.extend(data.get("messages", []))
    cursor = (data.get("response_metadata") or {}).get("next_cursor")
    if not cursor:
        break

seen_ids = {f["id"] for m in all_msgs for f in (m.get("files") or [])}
missing = set(uploaded_ids) - seen_ids
print(f"uploaded: {len(uploaded_ids)} | verified visible: {len(uploaded_ids) - len(missing)} | missing: {missing}")
print(f"summary posted: ts={summary_resp.get('ts')} ok={summary_resp.get('ok')}")
```

Pitfalls:
- DO NOT use `OPENCLAW_SLACK_BOT_TOKEN` — it is NOT exported in this env (verified 2026-07-07).
- If `subprocess.run(..., shell=False)` doesn't see bashrc, fall back to `subprocess.run(["bash", "-lc", "source ~/.bashrc && echo $..."])` to pull the token.
- DO NOT skip the summary message or the re-verify step. Channel-bridge narration leaks into the thread and buries the attachments (verified 2026-07-10). The summary is the cluster anchor the user reads.
- Each upload creates its own bot message in the thread. The summary is a single follow-up text message that names each attachment.
- `conversations.replies` paginates with `cursor` after the first 100 messages; the re-verify loop above follows the cursor to exhaust the thread.
- Slack has eventual consistency for new file-share attachments (typically <2s). The `time.sleep(2)` before re-verify absorbs that window for tight integration tests.
"""
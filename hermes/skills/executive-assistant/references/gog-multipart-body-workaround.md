# `gog gmail` multipart-body workaround

## The trap

`gog gmail get <messageId>` (v0.10.0 a92bd63) returns the **attachments array** when the message body is multipart — e.g.:

```
[
  {
    "attachmentId": "ANGjdJ...",
    "filename": "invite.ics",
    "mimeType": "text/calendar",
    "size": 3755,
    "sizeHuman": "3.7 KB"
  },
  ...
]
```

It does NOT walk `payload.parts[]` to the `text/plain` body. So `gog gmail get` is useless for plain-text body extraction on calendar invites, multipart forwards, and most real emails.

## Working recipe (Python, paste-and-run)

```python
import subprocess, os, json, base64

env = os.environ.copy()
env['EMAIL_USER'] = '$USER@gmail.com'

def fetch_body(msg_id: str) -> str:
    """Walk thread.messages[0].payload.parts for text/plain, base64-decode body.data."""
    # Step 1: thread get
    r = subprocess.run(
        ['gog', 'gmail', 'thread', 'get', msg_id, '-a', '$USER@gmail.com',
         '--json', '--results-only'],
        capture_output=True, text=True, timeout=20, env=env,
    )
    thread = json.loads(r.stdout).get('thread', {})
    messages = thread.get('messages', [])
    if not messages:
        return ''
    # Step 2: walk payload.parts for text/plain
    payload = messages[0].get('payload', {})
    parts = payload.get('parts', [])
    for part in parts:
        if part.get('mimeType') == 'text/plain':
            data = part.get('body', {}).get('data', '')
            if data:
                return base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='replace')
        # recurse one level into multipart
        if part.get('mimeType', '').startswith('multipart'):
            for sub in part.get('parts', []):
                if sub.get('mimeType') == 'text/plain':
                    data = sub.get('body', {}).get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='replace')
    # Step 3: payload itself may be body
    body_data = payload.get('body', {}).get('data', '')
    if body_data:
        return base64.urlsafe_b64decode(body_data + '==').decode('utf-8', errors='replace')
    return ''
```

## When it still fails

If all three paths return empty, the message is body-empty (just headers + an attachment — calendar invites work this way). For the executive-assistant brief, just surface the subject + sender + label context (CATEGORY_PERSONAL, IMPORTANT, etc.) and call it out:

> *Subject + sender only — body is calendar invite (.ics), no narrative text.*

Don't waste tool calls trying to extract the .ics content as a "body" — it won't render meaningfully in a Slack post.

## Verified

Tested 2026-07-09 on:
- `19f4347eb77fee69` — Larry Jacobson AI Transformation Roundtable invite (.ics only, no body)
- Riday Sopariwala intro — text/plain fetched cleanly via path above

Both outputs were pasted into the morning brief with sender + subject + 1-line summary.
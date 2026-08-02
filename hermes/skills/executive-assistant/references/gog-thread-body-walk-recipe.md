# gog gmail thread get — body walk recipe

Verified 2026-07-17 16:04 PT sweep against 4 thread types on `$USER@gmail.com`.

## The verb

```bash
gog gmail thread get <threadId> -a $USER@gmail.com --json --results-only
```

Output envelope: `{"thread":{"messages":[<msg1>, <msg2>, ...]}}` — note the `.thread` wrapper and that `--results-only` strips ONLY the outer shell, NOT the inner `thread` key.

## Each message shape

```json
{
  "historyId": "...",
  "id": "19f722e4ce4ba13e",
  "internalDate": "1784327064000",
  "labelIds": ["IMPORTANT", "INBOX"],
  "payload": {
    "body": {},                       // empty for multipart messages
    "headers": [                      // flat list, lowercase-ize name for lookup
      {"name": "Subject", "value": "..."},
      {"name": "From",    "value": "GitHub <noreply@github.com>"},
      ...
    ],
    "mimeType": "multipart/mixed",    // or "text/plain" for simple messages
    "parts": [...]                    // nested parts tree
  },
  "snippet": "Action needed: ...",    // always populated, useful for triage
  "threadId": "19f722e4ce4ba13e"
}
```

## Walk recipe (Python)

```python
import base64, json, subprocess

def fetch_thread(thread_id):
    p = subprocess.run(
        ['gog', 'gmail', 'thread', 'get', thread_id,
         '-a', '$USER@gmail.com', '--json', '--results-only'],
        capture_output=True, text=True, timeout=90)
    d = json.loads(p.stdout, strict=False)
    return d.get('thread', d).get('messages', [])

def headers(msg):
    return {h['name'].lower(): h['value']
            for h in msg.get('payload', {}).get('headers', [])}

def walk_body(msg):
    """Return concatenated text/plain parts (or empty string if simple/html only)."""
    out = []
    def walk(part):
        if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
            s = part['body']['data']
            s += '=' * ((4 - len(s) % 4) % 4)   # base64url padding
            try:
                out.append(base64.urlsafe_b64decode(s).decode('utf-8', 'replace'))
            except Exception:
                pass
        for x in part.get('parts', []) or []:
            walk(x)
    walk(msg.get('payload', {}))
    return '\n'.join(out)

# Example: triage one thread
for msg in fetch_thread('19f722e4ce4ba13e'):
    h = headers(msg)
    print('SUBJECT', h.get('subject'))
    print('FROM   ', h.get('from'))
    print('SNIPPET', msg.get('snippet'))
    print('TEXT   ', walk_body(msg)[:5000])
    print('---')
```

## Common pitfalls

- **Don't read `payload.body.data` directly.** Empty for multipart (GitHub, Oren Hen, Luma/CodeRabbit). Always walk `parts`.
- **Don't decode `text/html` parts.** They frequently contain base64-encoded inline images (logos, signatures) that eat context. `text/plain` is always present in multipart/alternative envelope.
- **`Snippet` is the cheat code.** For triage-only sweeps, skip the walk and use `msg['snippet']` — it is Gmail's precomputed 200-char summary and is correct for ~90% of cases.
- **`internalDate` is ms epoch** (divide by 1000 for seconds).
- **labelIds filter**: `IMPORTANT` + `INBOX` + `UNREAD` is the canonical "needs attention" triple; `CATEGORY_UPDATES` covers things like GitHub auto-replies.

## Worked examples (this sweep)

| Thread | Subj | From | Snippet gist |
|---|---|---|---|
| `19f722e4ce4ba13e` | GitHub PAT found in issue | support@github.com | 2 PATs revoked from disk_magician#25 |
| `19f7247b7afa6985` | PAT (classic) added | noreply@github.com | "coding macbook july 17" created |
| `19f723dcba7b4848` | FIFA Watch Party approved | CodeRabbit via Luma | Sunday 7/19 11:30 AM Cosm LA |
| `19f715fbb121bc06` | 2025 tax return | Oren Hen (EA) | Upload by 7/30 to TaxDome |

Each was decoded in one walk call; bodies ranged 500–2000 chars (text/plain part only).

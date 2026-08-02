# Slack API JSON Parse Recipe

`conversations.history` and `conversations.replies` from `slack.com/api/...` return JSON with **raw control characters** (`\n`, `\r`, `\t`) embedded inside message text strings. This breaks `json.loads()` in Python even with `strict=False`.

## Symptom

```
json.decoder.JSONDecodeError: Invalid control character at: line 1 column 524 (char 523)
json.decoder.JSONDecodeError: Unterminated string starting at: line 1 column 141 (char 140)
```

The byte at the failing column is `0x0a` (real newline) inside a `"text": "..."` string. Slack sends the `\n` literal, not the `\n` escape sequence, in `text` fields when the message contains line breaks.

## Robust recipe

```python
import json, re, urllib.request, os

token = os.environ['HERMES_SLACK_BOT_TOKEN']

def slack_history(channel: str, limit: int = 15) -> list:
    req = urllib.request.Request(
        "https://slack.com/api/conversations.history",
        data=json.dumps({"channel": channel, "limit": limit}).encode('utf-8'),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    # Strip raw control chars that break json.loads; \n and \t inside text fields are legit
    clean = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b'', raw)
    d = json.loads(clean.decode('utf-8', 'replace'), strict=False)
    if not d.get('ok'):
        raise RuntimeError(f"slack error: {d.get('error','unknown')}")
    return d.get('messages', [])

def slack_post(channel: str, text: str) -> dict:
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps({"channel": channel, "text": text}).encode('utf-8'),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read(), strict=False)
```

## Why not just `strict=False`?

`json.loads(raw, strict=False)` lets Python parse `\n` inside strings (instead of treating as whitespace), but Slack's payload contains `\n` already in raw form (`0x0a` byte, not the two-byte escape `\x5c\x6e`). So strict=False still fails — you must strip the raw control bytes first.

`\t` (`0x09`) and `\n` (`0x0a`) inside text strings are the only legit raw control chars you want to preserve (they're real newlines / tabs in message content). The regex above keeps those. It strips `0x00-0x08`, `0x0b`, `0x0c`, `0x0e-0x1f` — which are the actual broken bytes Slack occasionally injects (e.g., from copy-pasted terminal output with embedded ESC sequences).

## Alternative: use `gws` or MCP

- `mcp__slack__conversations_history` — when MCP is available, this works without the parse dance. But it can fail transiently ("MCP server 'slack' is unreachable after 3 consecutive failures"); have the curl fallback ready.
- `gws` Slack surface — different API, also has JSON quirks, not as well-tested for cron use.

## Channels used by EA sweep

| Channel | ID | Purpose |
|---|---|---|
| #all-$USER-ai | C09GRLXF9GR | Operator direct line |
| #ai-general | C0AJQ5M0A0Y | System reports, home channel |
| #worldai | C0AH3RY3DK6 | your-project.com product |
| #life | C0AMM2B4319 | Personal reminders |
| #mcp-mail | C0A0AG6EELB | Agent Mail acks |
| $USER DM | D0AFTLEJGJU | EA sweep destination |

Last verified: 2026-07-12 EA sweep (see session transcript — control-char failure first observed, recipe landed in skill + this file).
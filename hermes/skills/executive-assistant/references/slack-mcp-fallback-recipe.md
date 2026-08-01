# Slack MCP → curl fallback for executive-assistant briefs

When `mcp__slack__conversations_add_message` silently drops a brief (returns `{"result":""}` success-shape but no message lands) or returns a wrapper error like `text must be a string`, fall back to a direct curl POST to `chat.postMessage`.

This was confirmed live on 2026-07-09 20:02 PT: a 7028-byte brief posted to DM `D0AFTLEJGJU` thread `1783628106.060929` was silently dropped by the MCP wrapper, then successfully posted via curl at ts `1783652665.088029`.

## When to use

- `conversations_add_message` returns an empty `{"result":""}` AND `conversations_replies` shows no new row landed → silent drop.
- `conversations_add_message` returns `text must be a string` or any wrapper-side error.
- Don't retry the MCP call — it will fail the same way. Go straight to curl.

## Verified Python snippet (works on macOS, launchd-env-wrapper)

```python
import os, json, subprocess, pathlib

token = os.environ.get('HERMES_SLACK_BOT_TOKEN')
if not token:
    bashrc = pathlib.Path.home() / '.bashrc'
    if bashrc.exists():
        for line in bashrc.read_text().splitlines():
            if 'HERMES_SLACK_BOT_TOKEN' in line and line.strip().startswith('export'):
                parts = line.replace('export ', '').strip().split('=', 1)
                if len(parts) == 2:
                    token = parts[1].strip().strip('"').strip("'")
                    os.environ['HERMES_SLACK_BOT_TOKEN'] = token
                    break

assert token, 'HERMES_SLACK_BOT_TOKEN not found in env or ~/.bashrc'

# Brief should be written to /tmp/ea_brief_<HHMM>.txt first (write_file
# truncates long content, so append in chunks if >~5k chars).
brief_path = '/tmp/ea_brief_2002.txt'
with open(brief_path) as f:
    text = f.read()

channel = 'D0AFTLEJGJU'  # $JLEECHAN_DM_CHANNEL
thread_ts = '1783628106.060929'  # use the operator's most recent message ts

payload = json.dumps({'channel': channel, 'thread_ts': thread_ts, 'text': text})

cmd = [
    'curl', '-fsS', '-X', 'POST',
    'https://slack.com/api/chat.postMessage',
    '-H', f'Authorization: Bearer {token}',
    '-H', 'Content-Type: application/json; charset=utf-8',
    '-d', payload,
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
print(result.stdout)  # Expect: {"ok":true,"channel":"D0AFTLEJGJU","ts":"1783652665.088029",...}
```

## Mandatory post-publish verification

After the curl post, call `conversations_replies` on the same `thread_ts` and confirm the returned `MsgID` row exists with `ThreadTs == <correct_ts>`. The MCP silent-drop bug only manifests when you don't re-fetch — the success-shape `{"result":""}` from the MCP wrapper looks like a success unless you check.

## Pitfalls

- **Token source:** the XOX-C bot token (`HERMES_SLACK_BOT_TOKEN`) is sufficient for the operator's home DM channel. Don't fall back to `SLACK_USER_TOKEN` (XOX-P) for this — the DM is in the bot's home workspace, the bot token works fine.
- **write_file truncates long content:** `write_file` to `/tmp/ea_brief_<HHMM>.txt` may stop at ~5244 bytes mid-string. Append the rest in a follow-up `execute_code` script using `open(path, 'a').write(rest)`. Verify final size with `os.path.getsize` before curl.
- **Don't include the briefing in `execute_code` as a triple-quoted string** — embedded `"""` from markdown bullets trips the parser. Use a file + read instead.
- **Encoding:** `Content-Type: application/json; charset=utf-8` is required; em-dashes and box-drawing characters in the brief need UTF-8 round-trip. `json.dumps` handles this; `f"..."`-formatting into a shell string does NOT (quoting hell).
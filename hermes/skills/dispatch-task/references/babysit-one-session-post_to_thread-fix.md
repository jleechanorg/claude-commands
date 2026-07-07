# Fix: babysit-one-session.sh `post_to_thread` Python syntax errors

**Symptom (verified 2026-07-06, wa-3157 dispatch):** The canonical
`scripts/babysit-one-session.sh` (shipped in this skill) emits
`File "<string>", line 1 ... SyntaxError: invalid syntax` for every
Slack post. The babysit silently writes only to
`/tmp/<session>-babysit.log` and never reaches Slack.

## Root cause

Line 92 of the script does:

```bash
--data-binary "$(python3 -c "import json,sys; print(json.dumps({'channel':'$CHANNEL','thread_ts':'$THREAD_TS','text':sys.argv[1]}))" "$text")"
```

The inline `python3 -c` is wrapped in `$(...)` shell expansion AND
inside a `"..."` argument — on this host's bash quoting, the inner
single-quotes around the dict literal interact badly with the outer
double-quotes and Python receives a broken argument. The script runs
without error but every post returns `invalid_auth` because the
payload is malformed.

## Verified-working replacement

Replace the `post_to_thread` function body with this:

```bash
post_to_thread() {
  local text="$1"
  [ -z "$TOKEN" ] && return 0
  # Build payload in a separate variable so we don't double-quote the Python.
  local payload
  payload=$(python3 <<PYEOF
import json, sys
text = sys.argv[1]
print(json.dumps({"channel": "$CHANNEL", "thread_ts": "$THREAD_TS", "text": text}, ensure_ascii=False))
PYEOF
  "$text")
  local resp
  resp=$(curl -sS --connect-timeout 10 --max-time 30 \
    -X POST "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer ***" \
    -H "Content-Type: application/json; charset=utf-8" \
    --data-binary "$payload" 2>&1)
  local rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "[$(date -u +%H:%M:%S)] slack post curl failed rc=$rc" >> "$LOG"
    return 1
  fi
  if ! echo "$resp" | python3 -c 'import sys,json; sys.exit(0 if json.loads(sys.stdin.read()).get("ok") else 1)' 2>/dev/null; then
    echo "[$(date -u +%H:%M:%S)] slack post rejected: $(echo "$resp" | head -c 300)" >> "$LOG"
    return 1
  fi
}
```

## Why this works

- The Python heredoc is read as Python source, not as a bash argument,
  so the dict literal `{"channel": "..."}` is unambiguous Python.
- The `payload` variable receives the JSON string before it's passed to
  curl, so shell quoting doesn't interact with the JSON content.
- `ensure_ascii=False` preserves emojis like 🟢/🔴 (the colored-icons
  status format from SOUL.md).

## When NOT to use this fix

If you also need to fix the Slack-token-validity problem (env tokens
return `invalid_auth` from `auth.test` even when the same script
posts successfully), use `mcp__slack__conversations_add_message` from
a `cronjob` prompt instead of curl-based posting. See the dispatch-task
SKILL.md §"Env Slack tokens return `invalid_auth`" pitfall.

## Repro recipe

```bash
# 1. Reproduce the original failure
TOKEN="***" CHANNEL=C0BDAMWQQJK THREAD_TS=1783368232.020759 \
  bash -c 'curl -sS -X POST "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer ***" \
    -H "Content-Type: application/json; charset=utf-8" \
    --data-binary "$(python3 -c "import json,sys; print(json.dumps({\"channel\":\"$CHANNEL\",\"thread_ts\":\"$THREAD_TS\",\"text\":sys.argv[1]}))" "test")"'
# expected: {"ok":true,...} if your token is valid; {"ok":false,"error":"invalid_auth"} if it's the broken token.

# 2. Test the fix
TOKEN="***" CHANNEL=C0BDAMWQQJK THREAD_TS=1783368232.020759 \
  bash -c 'payload=$(python3 <<PYEOF
import json, sys
print(json.dumps({"channel": "$CHANNEL", "thread_ts": "$THREAD_TS", "text": sys.argv[1]}, ensure_ascii=False))
PYEOF
  "test from babysit fix"); curl -sS -X POST "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer ***" \
    -H "Content-Type: application/json; charset=utf-8" \
    --data-binary "$payload"'
```

Provenance: verified 2026-07-06 in Slack thread C0BDAMWQQJK
(ts 1783368232.020759) while bringing wa-3157 (PR #8063, issue #8062
story choice text leak repro) to green.
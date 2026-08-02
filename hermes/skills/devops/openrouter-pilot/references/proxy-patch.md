# `or-anthropic-proxy.py` gateway-discovery patch

**File:** `~/.local/bin/or-anthropic-proxy.py` (12301 → 16327 bytes; +278/-33)
**Saved patch:** `~/Downloads/or-anthropic-proxy-gateway-discovery-fix.patch` (376 lines, V4A format)
**Why:** Claude Code's `/v1/models` filter drops non-Claude model IDs. The patch adds an `anthropic-` prefix to non-Claude entries on the response side and strips it on the request side.

## Bidirectional rewrite logic

### Response side: `rewrite_for_claude_code_models(body: bytes) -> bytes`

```python
DISCOVERY_PREFIX = "anthropic-"
CLAUDE_PREFIXES = ("claude", "anthropic")

def rewrite_for_claude_code_models(body):
    try:
        data = json.loads(body)
    except Exception:
        return body  # never mangle non-JSON
    if not isinstance(data, dict):
        return body
    entries = data.get("data")
    if not isinstance(entries, list):
        return body
    changed = False
    for entry in entries:
        if not isinstance(entry, dict): continue
        mid = entry.get("id")
        if not isinstance(mid, str) or not mid: continue
        if mid.startswith(CLAUDE_PREFIXES): continue
        if mid.startswith(DISCOVERY_PREFIX): continue
        # Skip OpenAI-shape models — Codex uses them, not Claude
        if mid.startswith("openai/"): continue
        entry["id"] = DISCOVERY_PREFIX + mid
        if not entry.get("display_name"):
            entry["display_name"] = mid
        changed = True
    if not changed: return body
    return json.dumps(data, separators=(",", ":")).encode("utf-8")
```

Wired into the generic passthrough branch (line 259+):
```python
buf = upstream.read()
if "models" in path and "application/json" in resp_ctype:
    rewritten = rewrite_for_claude_code_models(buf)
    if rewritten is not buf:
        buf = rewritten
```

### Request side: `unwrap_anthropic_prefixed_model(body: bytes) -> bytes`

```python
def unwrap_anthropic_prefixed_model(body):
    try:
        data = json.loads(body)
    except Exception:
        return body
    if not isinstance(data, dict): return body
    model = data.get("model")
    if not isinstance(model, str) or not model.startswith(DISCOVERY_PREFIX):
        return body
    data["model"] = model[len(DISCOVERY_PREFIX):]
    return json.dumps(data, separators=(",", ":")).encode("utf-8")
```

Wired into `_proxy()` BEFORE the upstream call:
```python
is_messages_path = "/v1/messages" in path and "models" not in path
if is_messages_path and method == "POST" and body:
    unwrapped = unwrap_anthropic_prefixed_model(body)
    if unwrapped is not body:
        body = unwrapped
        fwd_headers["Content-Length"] = str(len(body))
```

## Why `anthropic-` (hyphen) and not `anthropic/` (slash)?

- OpenRouter already routes Claude models under `anthropic/claude-opus-4.8` (slash) — Claude Code accepts those via `startswith("anthropic")` filter.
- Using hyphen (`anthropic-z-ai/glm-5.2`) creates a clearly-synthetic ID that Claude Code accepts but OpenRouter would reject as a model id.
- The hyphen-vs-slash distinction is what makes the bidirectional rewrite safe: any model id starting with `anthropic/` is OpenRouter-routable as-is; only the hyphen-prefixed synthetic IDs need unwrapping.

## Verification

```bash
# After applying patch + restarting proxy:
curl -fsS http://127.0.0.1:8767/v1/models -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
data = d['data']
print(f'total: {len(data)}, prefixed: {len([m for m in data if m[\"id\"].startswith(\"anthropic-\")])}')
# Should print: total: 342, prefixed: 260 (z-ai/*, moonshotai/*, google/*, etc.)
# Claude models untouched: anthropic/claude-opus-4.8, anthropic/claude-sonnet-4.6, etc.
"
```

## Proxy lifecycle

```bash
# Start (in foreground for debugging):
python3 ~/.local/bin/or-anthropic-proxy.py
# Start (in background, Hermes-tracked):
terminal(background=true, command="python3 ~/.local/bin/or-anthropic-proxy.py")
# Log: /tmp/or-anthropic-proxy.log
# Port: 8767 (LISTEN_PORT env var to change)
```

## When NOT to use this patch

- The user has `or-pick` and is happy bypassing the picker — they don't need the proxy patch.
- The user is using Claude Code's `--model <slug>` flag directly (works fine; picker is irrelevant).
- The user's only OpenRouter route is for Codex (`codexo`/`codexor`/`codexk`); Codex doesn't use this proxy.

The patch is ONLY for users who want both Kimi/GLM visible in the Claude Code TUI picker AND the existing account-level default model.

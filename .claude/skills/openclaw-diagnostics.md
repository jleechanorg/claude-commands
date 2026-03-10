# OpenClaw Diagnostics

**Usage**: Diagnose what OpenClaw is actually doing locally — which model it uses, whether it's running, what the gateway is forwarding, and whether WorldArchitect is correctly routing through it.

## The Key Insight

WorldArchitect logs `provider=openclaw, model=openclaw/gemini-3-flash-preview` — that is the model string **our code sends** in the request body. OpenClaw ignores it. The gateway uses its **own configured model** (`agents.defaults.model.primary` in `~/.openclaw/openclaw.json`).

To know what model is actually running, always check the openclaw session log, not the Flask backend log.

---

## Step 1 — Is the gateway running?

```bash
openclaw status 2>&1 | grep -E "Gateway|Session|Heartbeat|model"
lsof -i :18789 2>/dev/null
curl -s --max-time 5 http://127.0.0.1:18789/health | head -3
```

Expected: `Gateway service · LaunchAgent installed · loaded · running (pid XXXXX)`

---

## Step 2 — What model is OpenClaw configured to use?

```bash
python3 -c "
import json
d = json.load(open('$HOME/.openclaw/openclaw.json'))
ag = d.get('agents', {}).get('defaults', {}).get('model', {})
print('Primary model:', ag.get('primary'))
print('Fallbacks:', ag.get('fallbacks'))
"
```

Also visible in status:
```bash
openclaw status 2>&1 | grep -E "Sessions|Heartbeat"
# e.g.: default gpt-5.3-codex (200k ctx)
```

---

## Step 3 — Prove what model handled a real request

Parse the openclaw session log (JSONL format):

```bash
python3 -c "
import sys, json
log = open('/tmp/openclaw/openclaw-$(date +%Y-%m-%d).log')
for line in log:
    try:
        d = json.loads(line)
        msg = d.get('1', '') or d.get('msg', '')
        if any(k in msg for k in ['embedded run start', 'provider=', 'model=']):
            print(msg[:250])
    except:
        pass
" 2>/dev/null | tail -20
```

Each request shows: `provider=openai-codex model=gpt-5.3-codex` (or minimax, etc.)

---

## Step 4 — Verify Tailscale Serve is routing correctly

```bash
tailscale serve status
# Should show: https://jeffreys-macbook-pro.tail5eb762.ts.net → http://127.0.0.1:18789

curl -s --max-time 8 https://jeffreys-macbook-pro.tail5eb762.ts.net/health | head -3
# Should return HTML with HTTP 200
```

---

## Step 5 — Full end-to-end proof for a campaign request

After a user sends a message at `http://localhost:8055/game/<campaign_id>`:

```bash
# 1. WorldArchitect side — what provider/model was selected
grep "PROVIDER_SELECTION_FINAL\|Using provider" \
  /tmp/worktree_openclaw/feat_openclaw-tailscale-clean/flask_backend.log | tail -5

# 2. OpenClaw side — what model actually executed
python3 -c "
import json
for line in open('/tmp/openclaw/openclaw-$(date +%Y-%m-%d).log'):
    try:
        d = json.loads(line)
        msg = d.get('1','') or d.get('msg','')
        if 'embedded run start' in msg or 'run end' in msg:
            print(msg[:300])
    except: pass
" 2>/dev/null | tail -10
```

---

## Common Issues & Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Gateway not listening on 18789 | `ai.openclaw.consensus` holds port 18792, crashing gateway | `kill $(lsof -t -i :18792); launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway` |
| Config parse error: `DISCORD_BOT_TOKEN` | Disabled discord channel still has `${VAR}` placeholder | Set `channels.discord.token = ""` in openclaw.json |
| Config parse error: `SECOND_OPINION_MCP_URL` | Disabled plugin still has env var refs | Clear `plugins.entries.openclaw-mcp-adapter.config.servers = []` |
| `bind` error (invalid value) | Valid values: `"auto"`, `"lan"`, `"loopback"`, `"custom"`, `"tailnet"` | Use `"loopback"` for Tailscale Serve setup |
| Test connection 502 | Gateway bound to tailnet but Tailscale Serve proxies to `127.0.0.1` | Set `gateway.bind = "loopback"` |
| HTTPS test connection fails | `gateway_url` field expects a tunnel URL (port 443) | Use `https://jeffreys-macbook-pro.tail5eb762.ts.net` (no port); Tailscale Serve handles HTTPS→18789 |

---

## Key Paths

| Resource | Path |
|----------|------|
| OpenClaw config | `~/.openclaw/openclaw.json` |
| Gateway stdout log | `~/.openclaw/logs/gateway.log` |
| Gateway stderr log | `~/.openclaw/logs/gateway.err.log` |
| Session JSONL log | `/tmp/openclaw/openclaw-YYYY-MM-DD.log` |
| Raw stream log | `/tmp/openclaw/raw-stream.jsonl` |
| Tailscale cert (if needed) | `tailscale cert jeffreys-macbook-pro.tail5eb762.ts.net` |
| LaunchAgent plist | `~/Library/LaunchAgents/ai.openclaw.gateway.plist` |

---

## WorldArchitect Settings (correct values)

```
Gateway URL:   https://jeffreys-macbook-pro.tail5eb762.ts.net
Gateway Port:  18789  (ignored when URL is set — port is for localhost fallback only)
Gateway Token: ${OPENCLAW_GATEWAY_TOKEN}  (set via environment variable or secret manager)
```

The `Gateway Port` field only matters when no `Gateway URL` is set. When a URL is provided, OpenClaw provider uses that URL directly (port from URL or default 443).

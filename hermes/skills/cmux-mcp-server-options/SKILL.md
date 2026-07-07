---
name: cmux-mcp-server-options
description: "Verified list of community MCP servers for cmux + decision guide on which to install. Trigger when the user asks 'does cmux have an MCP server', 'cmux MCP', 'install cmux MCP', 'use cmux via MCP', 'cmux MCP tools', 'use a real CLI/MCP for cmux instead of the socket', 'how do I steer cmux from Claude Code'. cmux itself does NOT ship an MCP server (verified 2026-06-25, v0.64.17), but at least 4 community MCP servers wrap the cmux CLI/socket for AI-agent integration. Load this skill before recommending or installing one — pick the right one for the use case (single-tab control vs multi-agent orchestration vs mobile streaming)."
---

# cmux MCP Server Options (verified 2026-06-25)

**Important correction:** cmux itself does NOT ship an MCP server, but **at least 4 community MCP servers are installable via npm** and wrap the cmux CLI/socket for AI-agent integration. Grok (the AI assistant) correctly identified these when I initially denied their existence — my "cmux has no MCP server" claim was wrong.

## The verified npm packages

| Package | Version | Published | Bin | License | Source | Best for |
|---|---|---|---|---|---|---|
| `cmux-mcp` | 1.3.1 | 2026-04-03 (2mo ago) | `cmux-mcp` | MIT | https://github.com/daegweon/cmux-mcp | **Single-tab control** — `write_to_terminal`, `read_terminal_output`, `send_control_character`. Uses native CLI for background control without focus stealing. |
| `@jsamuel1/cmux-mcp` | 1.4.0 | 2026-06-19 (1wk ago) | `cmux-mcp` | MIT | https://github.com/jsamuel1/cmux-mcp | **Hardened fork** of the above — shell-injection-safe `execFile` arg passing, read-only/write/dangerous tool annotations, updated MCP SDK 1.29.0. **Pick this over the original.** |
| `cmux-agent-mcp` | 0.1.2 | 2026-03-17 (3mo ago) | `cmux-agent-mcp` | PolyForm-Strict | https://github.com/multiagentcognition/cmux-agent-mcp | **Multi-agent orchestration** — spawn/monitor agents across panes/workspaces, lifecycle management, 25-35+ tools. |
| `cmux-relay-agent` | 0.3.25 | 2026-06-04 (3wk ago) | `cmux-relay` | MIT | https://github.com/pallidev/cmux-relay | **Mobile streaming** — WebRTC/p2p streaming of cmux terminal to phone, real-time monitoring. |
| `@cotal-ai/cmux` | 0.8.1 | 2026-06-25 (21min ago!) | (library) | Apache-2.0 | npm | **Programmatic spawn** — Runtime + TerminalLayout provider for spawning agents into cmux tabs. |

Sources: `npm view <package>` 2026-06-25 (Tavily web search is down, but npm registry is direct).

## Quick install + smoke test recipe

For the **single-tab control** use case (Hermes's primary need: steer a known cmux workspace, read its screen, send Enter after typing):

```bash
# 1. Install the hardened fork globally
npm install -g @jsamuel1/cmux-mcp

# 2. Smoke-test that the binary actually runs
cmux-mcp --help 2>&1 | head -20

# 3. Register in ~/.claude/settings.json (and ~/.codex/config.toml if needed)
# Format: stdio MCP server with the global bin path as command
cat ~/.claude/settings.json | python3 -c "
import json, sys
cfg = json.load(sys.stdin)
cfg.setdefault('mcpServers', {})
cfg['mcpServers']['cmux'] = {
  'command': '$HOME/.bun/bin/cmux-mcp',  # or 'cmux-mcp' if on PATH
  'args': [],
  'env': {}
}
print(json.dumps(cfg, indent=2))
" > /tmp/settings.json
mv /tmp/settings.json ~/.claude/settings.json

# 4. Restart Claude Code / Codex so the MCP loads
# 5. Verify in Claude Code: the tool palette should now include cmux tools
#    (e.g. cmux__write_to_terminal, cmux__read_terminal_output)
```

**Pitfalls verified across past installations:**
- The MCP server must be **on PATH** or use an absolute `command` path. `which cmux-mcp` to confirm.
- The MCP server reads from the cmux **active tab** by default (per `cmux-mcp` README) — for multi-tab steering, you need `cmux-agent-mcp` instead.
- After installing, **restart the host agent** (Claude Code / Codex) — MCP servers don't hot-reload.
- For Hermes, you need a **separate** MCP server per Hermes process — Hermes runs in a Python/Node gateway, not a Claude Code session, so the MCP tool surface may not be exposed unless the gateway registers MCP clients.

## Targeting a specific cmux app (prod vs dev vs custom build)

The MCP wrapper does **not** talk to the cmux socket directly — it spawns `cmux` as a subprocess for every tool call (`execFile(CMUX_BIN, args)` in `build/index.js`, confirmed by source 2026-06-25). The `CMUX_BIN` path is resolved by `build/cmux-path.js` in this order:

1. `$CMUX_PATH` env var — **highest priority, set this to target a specific app**
2. `which cmux` — whatever's first in your `PATH`
3. `/Applications/cmux.app/Contents/Resources/bin/cmux` — macOS prod default
4. `$HOME/Applications/cmux.app/...` — user-local prod default

**So the MCP server drives whichever `cmux` binary it resolves to.** Both prod AND dev builds can be controlled simultaneously by registering multiple MCP servers with different `CMUX_PATH` values:

```json
{
  "mcpServers": {
    "cmux-prod": {
      "command": "$HOME/.bun/bin/cmux-mcp",
      "args": [],
      "env": { "CMUX_PATH": "/Applications/cmux.app/Contents/Resources/bin/cmux" }
    },
    "cmux-dev": {
      "command": "$HOME/.bun/bin/cmux-mcp",
      "args": [],
      "env": { "CMUX_PATH": "/Applications/cmux DEV may-18.app/Contents/Resources/bin/cmux" }
    }
  }
}
```

**Verified 2026-06-25**: when `CMUX_PATH` is unset, `which cmux` → `~/.local/bin/cmux` shim, which talks to whichever socket the shim is currently pointing at (one session only). To drive a specific cmux app, **always set `CMUX_PATH` explicitly** — don't rely on the shim.

**Caveat — one MCP server = one cmux session.** The MCP server's `execFile(CMUX_BIN, ...)` calls hit a single cmux binary, which connects to a single socket. If you need simultaneous steering of two live cmux sessions (e.g. prod + dev), register two MCP server entries as above. Don't try to swap `CMUX_PATH` at runtime — restart the MCP server instead.

**Common target binaries on this Mac (verified 2026-06-25):**
- Prod: `/Applications/cmux.app/Contents/Resources/bin/cmux` (Jun 21 build, 55 MB)
- Dev: `/Applications/cmux DEV may-18.app/Contents/Resources/bin/cmux` (May 18 build, 8.4 MB — note: smaller because dev build doesn't ship the full `claude` wrapper)

## Decision guide — which one to install

| Use case | Pick | Why |
|---|---|---|
| Single-tab control (send text, read output) | **`@jsamuel1/cmux-mcp`** | Hardened (shell-injection-safe execFile), most recent (1wk old), updated MCP SDK |
| Multi-agent orchestration (spawn/monitor many cmux tabs) | **`cmux-agent-mcp`** | 25-35 tools for full lifecycle |
| Mobile streaming / remote monitoring | **`cmux-relay-agent`** | WebRTC streaming, real-time phone access |
| Programmatic agent spawn (no UI) | **`@cotal-ai/cmux`** | Library, not a server — embed in your own code |
| Hermes-side automation (this gateway) | **None / roll our own** | Hermes runs in a Python gateway without MCP client integration; use `cmux` CLI over shell instead |

## Why Hermes should NOT install an MCP server today

Hermes (the gateway that runs this conversation) does **not currently register MCP clients** for itself — only for downstream Claude Code / Codex sessions. The gateway's own tools include `terminal`, `patch`, `read_file`, etc., but no `mcp__*` namespace. So even if we install `cmux-mcp`, **Hermes itself can't call it**.

For Hermes's existing cmux workflows (multi-socket probe, surface read-screen, send+enter steering), the verified-reliable path is the **`cmux` CLI over shell** plus the existing `cmux` skill (Unix socket API + multi-socket probe + focus-then-read).

**When this changes:** if/when the Hermes gateway adds an MCP-client toolset, install `@jsamuel1/cmux-mcp` and the existing cmux skill can be retired in favor of the MCP tools.

## What NOT to do

- **Don't install multiple cmux MCP servers at once.** They may conflict over the cmux socket. Pick ONE.
- **Don't use the original `cmux-mcp` (daegweon)** — use the hardened fork `@jsamuel1/cmux-mcp`. The original has known shell-injection risks in its `execFile` arg passing (per the fork's README).
- **Don't trust MCP servers that don't show their source.** All five above link to GitHub repos. Reject MCP servers from npm without source visibility.
- **Don't conflate `cmux-mcp` (single tab) with `cmux-agent-mcp` (multi-agent orchestration).** They solve different problems. Read each README before installing.

## MCP vs. CLI over shell — when to use which

| Task | Best path |
|---|---|
| Hermes automation (this gateway) | `cmux` CLI over shell + the `cmux` skill |
| Claude Code desktop driving one tab | `@jsamuel1/cmux-mcp` via MCP tools |
| Multi-agent orchestration | `cmux-agent-mcp` or roll your own orchestrator |
| Streaming to a phone | `cmux-relay-agent` |
| Spawning agents programmatically | `@cotal-ai/cmux` library |

## Companion skills

- `cmux` — parent skill (Unix socket + CLI; what Hermes uses today)
- `cmux-find-workspace-by-topic` — multi-socket probe + keyword grep
- `mcp-builder` — if you want to wrap cmux differently
- `native-mcp` — Hermes's MCP client integration (so you know when MCP tools become available to Hermes)

## Bug-ref

2026-06-25 — I initially created a `cmux-no-mcp-confirmed` skill claiming cmux has no MCP server. The user (correctly) cited Grok's answer that there ARE community MCP servers (cmux-mcp, cmux-agent-mcp, cmux-relay-agent, @cotal-ai/cmux). I verified via `npm view <package>` on 2026-06-25 — all 4-5 packages exist with current publish dates. **My initial fact-check was wrong** because I searched the cmux upstream repo (which has no MCP server) without checking npm. The lesson: **when the user cites a specific named tool/package, verify it via the appropriate registry (npm, PyPI, GitHub) before denying it exists.**
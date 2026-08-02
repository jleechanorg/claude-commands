# Two-identity Slack routing — Hermes bot vs. mcp_agent_mail app

When a Slack thread shows posts from multiple bot identities, use this table to
identify which path each post traveled through and which tool surface to fix.

## Identity / token / config table (verified 2026-07-20)

| Slack identity | User ID | Token | Configured in | Posted by |
|---|---|---|---|---|
| **Hermes bot** | `U0AEZC7RX1Q` | `SLACK_MCP_XOXB_TOKEN` / `HERMES_SLACK_BOT_TOKEN` (xoxb-…) | `~/.hermes/config.yaml` `mcp_servers.slack` and `~/.codex/config.toml` `[mcp_servers.slack]` | Hermes gateway + Codex/Claude AO workers calling `mcp__slack__conversations_add_message` |
| **mcp_agent_mail Slack app** | `U0A4G7LDJ4R` | `SLACK_BOT_TOKEN` (same xoxb-…) | `~/mcp_mail/.env.slack-off` overlay + `~/mcp_mail/.env` | MCP Agent Mail server's `slack_post_message` tool (`~/mcp_mail/src/mcp_agent_mail/app.py:8766`) — vendor app identity, NOT Hermes-managed |

Both tokens end in the same suffix but they're **registered to different Slack
apps** — that's why the same `xoxb-…` prefix posts under two different user IDs.
The `mcp_agent_mail` Slack app is the vendor's own OAuth app installed in your
workspace; Hermes bot is the user-managed app.

## Sub-second interleaving pattern — diagnostic fingerprint

When you see alternating posts from `U0AEZC7RX1Q` and `U0A4G7LDJ4R` with
sub-second ts deltas (e.g. `1784595397.527259` then `1784595397.775689`), that's
NOT one bot echoing the other. That's **two distinct agent processes converging
on the same thread through two distinct tool paths**:

- Hermes gateway replying via `mcp__slack__conversations_add_message`
- An AO worker / dispatch agent replying via `mcp_agent_mail.slack_post_message`

If the `mcp_agent_mail` posts are substantive worker-LLM analysis (not bot
boilerplate), the dispatch path was `mcporter` or some other agent-coordination
layer reaching the MCP Agent Mail server at `http://127.0.0.1:8765/mcp/`.

## Tool-surface audit (what each runtime can see)

```bash
# Hermes gateway runtime (this session, right now):
grep -A4 "mcp_servers:" ~/.hermes/config.yaml | head -10
# → shows: mcp_servers.slack → $HOME/go/bin/slack-mcp-server
# → does NOT show: any mcp_agent_mail entry (Hermes doesn't load it directly)

# Codex runtime (what AO Codex workers see):
grep -A4 "mcp_servers\." ~/.codex/config.toml | head -20
# → shows: mcp_servers.slack → slack-mcp-server
# → shows: mcp_servers.worldai (your-project.com MCP)
# → does NOT show: mcp_agent_mail entry

# But — Hermes's mcporter / slack-thread-token-watch dispatch paths
# can dynamically reach any MCP server on localhost:8765 if a worker
# has the URL. That dynamic-reach path is what posts as U0A4G7LDJ4R.
```

## Three places the routing can be fixed

1. **MCP-server config layer** — add `disabled_tools: [slack_post_message]` to
   the `mcp_agent_mail` server entry wherever it's exposed. This removes the
   tool from `tools/list` entirely; callers see it as non-existent.

2. **Policy layer** — Hermes-side commit that says "AO workers MUST use
   `mcp__slack__conversations_add_message` for operator-facing Slack posts,
   NEVER `mcp_agent_mail.slack_post_message`." Encodes the identity preference.

3. **Server-source layer** — modify `~/mcp_mail/src/mcp_agent_mail/app.py` so
   `slack_post_message` checks `get_settings().slack.enabled` before dispatch
   and raises `ToolExecutionError(SLACK_DISABLED)` when off. This matches the
   listener/notifier behavior already gated by `SLACK_ENABLED=false`.

The policy layer is the cheapest; the server-source layer is the most durable.

## Repro for verification

```bash
# 1. Verify current state — mcp_agent_mail.slack_post_message is reachable
curl -s -m 5 -H "Authorization: Bearer ${HTTP_BEARER_TOKEN}" \
  http://127.0.0.1:8765/mcp/ -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); \
      print([t['name'] for t in d['result']['tools'] if 'slack' in t['name'].lower()])"
# → expect: ['slack_post_message'] (currently reachable)

# 2. After fix: same call returns [] (or omits slack_post_message).
```

## Thread-archive evidence (incident 2026-07-20)

Slack ts pattern from `C0AH3RY3DK6/p1784596443`:

```
1784595397.527259  U0A4G7LDJ4R (mcp_agent_mail)  ← worker-LLM analysis
1784595397.775689  U0AEZC7RX1Q (hermes)           ← Hermes gateway ack
1784595411.122559  U0AEZC7RX1Q (hermes)           ← Hermes "Posted."
1784595411.125699  U0A4G7LDJ4R (mcp_agent_mail)   ← worker-LLM analysis (CONCURRENT)
1784595411.423589  U0AEZC7RX1Q (hermes)           ← Hermes ack
1784595445.735049  U0A4G7LDJ4R (mcp_agent_mail)   ← worker-LLM analysis (CONCURRENT)
1784595739.535339  U0AEZC7RX1Q (hermes)           ← long analysis reply
1784595739.545819  U0A4G7LDJ4R (mcp_agent_mail)   ← SAME content (interleaved)
```

The `1784595739.*` pair is especially diagnostic: two posts with **the same
content within 11 milliseconds**, one from each identity. The mcp_agent_mail
path is doing real work; it's not echo.

## Adjacent failure mode: MCP Agent Mail "AO Progress Report" uses fabricated `wa-NNNN` IDs

**Incident:** 2026-07-23, channel `C0ALSKLU9KM`, daily `*AO Progress Report* | 2026-07-23 — new daily thread` (`thread_ts=1784792447.282019`).

The MCP Agent Mail bot (`U0A4G7LDJ4R`) posts a daily "AO Progress Report" thread listing session IDs in the format `wa-NNNN` (e.g. `wa-3339`, `wa-3350`, `wa-3358..wa-3366`, `ao-8521`, `jc-2047`, `cc-orchestrator`). **None of these IDs exist in the `~/.ao/data/ao.db` `sessions` table.**

Diagnostic recipe:

```bash
sqlite3 ~/.ao/data/ao.db \
  "SELECT DISTINCT issue_id FROM sessions WHERE issue_id LIKE 'wa-%' OR issue_id LIKE 'ao-%' OR issue_id LIKE 'jc-%' OR issue_id LIKE 'cc-%';"
# → 0 rows

ao session ls --json | python3 -c "
import json, sys
d = json.load(sys.stdin)
sessions = d.get('data', [])
for s in sessions:
    iid = s.get('issueId', '')
    if iid and ('wa-' in iid or 'ao-' in iid or 'jc-' in iid or 'cc-' in iid):
        print(f\"  {s['id']:30s} issueId={iid}\")
"
# → 0 rows
```

Real AO session IDs use the format `<project>-<N>` (e.g. `worldarchitect-88`, `jleechanclaw-13`); real `issue_id` values use the bead ID format `$USER-XXXX` (e.g. `$USER-ywab`, `$USER-tj88`, `$USER-w528`). The `wa-NNNN` format in the MCP Mail report is **fabricated** — likely a synthesis from a different source (sibling worker `--prompt-interactive` invocations? a stale cache? a different name-mapping scheme?) and does not match any canonical AO state.

**Real-world impact:** users (including Jeffrey) reading the daily "AO Progress Report" see `wa-3339 :skull: killed` and conclude "AO sessions are dying." In reality, the corresponding live worker is `worldarchitect-N` with bead `$USER-XXXX` and is healthy. The report is **misleading** in addition to being unreadable.

**Verified during incident investigation:**

| MCP Mail report ID | What it claimed | Real AO state (verified via `ps aux` + GitHub) |
|---|---|---|
| `wa-3359 (worldarchitect)` | "PR open @ 72b4a1a, off-track, idle 65h48m" | Live worker exists pushing commits to PR #8178; SHA `72b4a1a` IS the head SHA of PR #8178 (verified via `gh api repos/$GITHUB_REPOSITORY/pulls/8178`) |
| `wa-3361 (worldarchitect)` | "PR open @ aa92321, Green Gate: FAILURE, idle 63h3m" | Live worker exists for PR #8177 (head SHA matches); Green Gate failure is a real CI status, not worker failure |
| `wa-3364 (worldarchitect)` | "PR #8511, off-track, idle 49h21m" | PR #8511 got a fresh commit 1.0h before the diagnostic ran; the "idle 49h21m" claim is wrong |
| `wa-3365 (worldarchitect)` | "PR #8428, on-track, blockers: beads-jsonl IN_PROGRESS" | PR #8428 got 3 fresh commits 1.5–1.6h before the diagnostic ran; the report is stale |

**Bead:** `orch-1oli` filed 2026-07-23 for durable fix.

**Workaround until fix lands:** when a user says "is AO working?" or "the daily report shows N stalled", do NOT trust the `wa-NNNN` IDs. Cross-reference via:

```bash
# 1. List live AO workers by project
ao session ls --json | jq '[.data[] | select(.isTerminated == false)] | length'

# 2. Get the PR numbers the live workers actually touch
ps aux | grep -E "(claude|agy).*--prompt-interactive" | grep -v grep | grep -oE 'PR #[0-9]+|$USER-[a-z0-9]+'

# 3. Cross-reference with GitHub: for each PR mentioned, check the latest commit timestamp
for pr in <prs>; do
  gh api "repos/$GITHUB_REPOSITORY/pulls/$pr/commits" | python3 -c "..."
done
```

This is the canonical "ground truth from live processes + GitHub" diagnostic that bypasses the fabricated `wa-NNNN` namespace entirely. See the new `ao-worker-ground-truth` umbrella skill for the full recipe.

---
name: worldai-tools-mcp-proxy-testing
description: Run and test the WorldAI Tools MCP HTTP proxy with real local harnesses.
---

# WorldAI Tools MCP Proxy - Testing & Local Usage

## Overview

The WorldAI Tools MCP Proxy (`$PROJECT_ROOT/worldai_tools_mcp_proxy.py`) is an HTTP JSON-RPC proxy that sits in front of the upstream MCP server. It adds 10 local admin/ops/diag tools with RBAC authorization.

**Transport**: HTTP only (no stdio). Cannot be added as a Claude Desktop MCP server config — run it as a local HTTP server and call via curl/JSON-RPC.

## Quick Start: Run the Real Test Harness

```bash
# 1. Ensure venv symlink exists in worktree
ln -sf /home/$USER/projects/your-project.com/venv ./venv

# 2. Kill any lingering processes on test ports
kill -9 $(lsof -ti:18081,18091) 2>/dev/null

# 3. Run the harness (starts upstream + proxy automatically)
PYTHONPATH=$(pwd) \
WORLDAI_DEV_MODE=true \
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
TESTING_AUTH_BYPASS=true \
./venv/bin/python testing_mcp/test_worldai_tools_mcp_proxy_real.py
```

Evidence output: `docs/worldai_tools_mcp_proxy_real_test_report.md`
Raw logs: `docs/worldai_tools_mcp_proxy_logs/` (gitignored)

## ⚠️ Tool Semantics — dry_run Stub Warning

**CRITICAL**: `admin_copy_campaign_user_to_user`'s `dry_run=true` parameter is a **static stub** — it returns hardcoded fake data without querying Firestore:

```python
# Line 611-624 in worldai_tools_mcp_proxy.py — dry_run returns FAKE DATA
if dry_run:
    return {  # ← Never checks the database!
        "copied_counts": {"campaign": 1, "story": 0, ...},  # Always returns 1!
    }
```

**Never use `dry_run=true` to verify campaign existence.** It will tell you any campaign exists.

**For existence checks, use `admin_download_campaign`** instead — it performs a real Firestore query and returns `"campaign not found"` if missing.

## Run the Proxy Standalone

```bash
# Terminal 1: Start upstream MCP server
PYTHONPATH=$(pwd) WORLDAI_DEV_MODE=true \
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
TESTING_AUTH_BYPASS=true \
./venv/bin/python -m mvp_site.mcp_api --http-only --port 18081

# Terminal 2: Start proxy
PYTHONPATH=$(pwd) WORLDAI_DEV_MODE=true \
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
WORLDTOOLS_UPSTREAM_MCP_URL=http://127.0.0.1:18081/mcp \
WORLDTOOLS_PROXY_PORT=18091 \
WORLDTOOLS_SUPPORT_ADMINS=<your-email@gmail.com> \
WORLDTOOLS_OPS_ADMINS=<your-email@gmail.com> \
WORLDTOOLS_DEPLOY_ADMINS=<your-email@gmail.com> \
./venv/bin/python -m mvp_site.worldai_tools_mcp_proxy
```

## Call Tools via curl

```bash
# List all tools (upstream + local)
curl -s -X POST http://127.0.0.1:18091/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | jq '.result.tools[].name'

# Read a Firestore document (requires ops_admin role)
curl -s -X POST http://127.0.0.1:18091/mcp \
  -H "Content-Type: application/json" \
  -H "X-Worldtools-Actor-Email: <your-email@gmail.com>" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"ops_firestore_read_document","arguments":{"document_path":"users/0wf6sCREyLcgynidU5LjyZEfm7D2/campaigns/06PTI05cBPY8t5m4hYzj","reason":"ops read","ticket_id":"OPS-001"}}}' | jq '.result'
```

## Key Environment Variables

| Variable | Purpose | Example |
|---|---|---|
| `WORLDTOOLS_UPSTREAM_MCP_URL` | Upstream MCP endpoint | `http://127.0.0.1:18081/mcp` |
| `WORLDTOOLS_PROXY_PORT` | Proxy listen port | `18091` |
| `WORLDTOOLS_SUPPORT_ADMINS` | CSV emails for admin_ tools | `<your-email@gmail.com>` |
| `WORLDTOOLS_OPS_ADMINS` | CSV emails for ops_ tools | `<your-email@gmail.com>` |
| `WORLDTOOLS_DEPLOY_ADMINS` | CSV emails for deploy tools | `<your-email@gmail.com>` |
| `WORLDTOOLS_GCLOUD_PROJECT_ALLOWLIST` | Allowed GCP projects | `worldarchitecture-ai` |
| `WORLDTOOLS_FIRESTORE_PATH_PREFIXES` | Allowed doc path prefixes | `users/` (default) |
| `WORLDAI_DEV_MODE` | Required for dev credentials | `true` |
| `WORLDAI_GOOGLE_APPLICATION_CREDENTIALS` | Service account key | `~/serviceAccountKey.json` |

## RBAC Authorization Model

- Header `X-Worldtools-Actor-Email` is matched against admin allowlists
- `diag_` / `admin_` tools require `support_admin` role
- `ops_firestore_*` / `ops_gcloud_*` / `ops_run_mcp_local` require `ops_admin` role
- `ops_run_mcp_production` / `ops_deploy_*` require `deploy_admin` role
- All `admin_` / `ops_` tools require `reason` + `ticket_id` arguments (policy enforcement)

## Local Tools (10 total)

| Tool | Role | Description |
|---|---|---|
| `diag_evaluate_campaign_dice` | support_admin | Audit dice rolls for a campaign |
| `admin_copy_campaign_user_to_user` | support_admin | Copy campaign between users (supports dry_run) |
| `admin_download_campaign` | support_admin | Export campaign to local file |
| `admin_download_campaign_entries` | support_admin | Export specific story entries |
| `ops_gcloud_logs_read` | ops_admin | Read Cloud Run logs |
| `ops_firestore_read_document` | ops_admin | Read a Firestore document by path |
| `ops_firestore_query_collection_group` | ops_admin | Query a Firestore collection group |
| `ops_run_mcp_local` | ops_admin | Start local MCP server (dry_run available) |
| `ops_run_mcp_production` | deploy_admin | Start production MCP server (dry_run available) |
| `ops_deploy_mcp_service` | deploy_admin | Deploy MCP service to Cloud Run |

## Real Test Data

- **Test user**: `<your-email@gmail.com>` -> UID `0wf6sCREyLcgynidU5LjyZEfm7D2`
- **Real campaign**: `06PTI05cBPY8t5m4hYzj` ("The Merchant's War")
- **Document path**: `users/0wf6sCREyLcgynidU5LjyZEfm7D2/campaigns/06PTI05cBPY8t5m4hYzj`
- **GCP project**: `worldarchitecture-ai`

## Common Issues

| Issue | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: mvp_site` | Missing PYTHONPATH | Set `PYTHONPATH=$(pwd)` or use `-m mvp_site.module` |
| `WORLDAI_DEV_MODE=true required` | clock_skew_credentials gate | Set `WORLDAI_DEV_MODE=true` |
| `Address already in use` | Lingering processes | `kill -9 $(lsof -ti:18081,18091)` |
| `*_admin role required` | Email not in allowlist | Set `WORLDTOOLS_*_ADMINS` env vars |
| No venv in worktree | Worktrees share main venv | `ln -sf /path/to/main/venv ./venv` |

## Firestore Project Routing

All worldarchitect MCP tools (both `admin_*` and `ops_firestore_*`) connect to the **same Firestore project**: `worldarchitecture-ai`.

| Tool | Backend | Project |
|------|---------|---------|
| `admin_copy_campaign_user_to_user` | Firestore via `_get_firestore_db()` | `worldarchitecture-ai` |
| `admin_download_campaign` | Firestore via `_get_firestore_db()` | `worldarchitecture-ai` |
| `ops_firestore_read_document` | Firestore via `_get_firestore_db()` | `worldarchitecture-ai` |
| `ops_firestore_query_collection_group` | Firestore via `_get_firestore_db()` | `worldarchitecture-ai` |

**The `ai-universe-b3551` project** is used only by the browser frontend (Vite app). It is NOT used by any MCP tool. Do not confuse these two projects.

Credentials: `~/serviceAccountKey.json` (project_id: `worldarchitecture-ai`)

## Firestore Data Structure

Campaigns are NESTED under users (see `.claude/skills/firebase-prod-campaigns.md`):
```
users/{uid}/campaigns/{campaign_id}  (document)
users/{uid}/campaigns/{campaign_id}/story/{entry_id}  (subcollection)
users/{uid}/campaigns/{campaign_id}/game_states/current_state  (subcollection)
```

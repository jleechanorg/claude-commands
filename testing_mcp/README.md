# Testing MCP - Server-Level Tests

This directory contains **server-level** tests that hit a running WorldArchitect MCP server over HTTP (`/mcp`).

These tests **do not** call Gemini/Cerebras/OpenRouter APIs directly.

## What this means

- The **test runner** does **not** require provider API keys.
- The **target MCP server** (deploy preview or your local MCP server) is responsible for having provider keys configured if it needs to run real inferences.

## Quick start

### Run against a deploy preview

```bash
export MCP_SERVER_URL=https://mvp-site-app-<pool>-<hash>-uc.a.run.app
cd testing_mcp
python test_native_tools_real_api.py
python test_dice_rolls_comprehensive.py
```

### Run locally

If you already have a local MCP server running:

```bash
cd testing_mcp
python test_native_tools_real_api.py --server-url http://127.0.0.1:8001
python test_dice_rolls_comprehensive.py --server-url http://127.0.0.1:8001
```

Or start a local MCP server automatically (loads LLM keys via `gcloud` Secret Manager if available):

```bash
cd testing_mcp
python test_dice_rolls_comprehensive.py --start-local
```

## Evidence

Results are saved under:

- `testing_mcp/evidence/mcp_dice_rolls/`


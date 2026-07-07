# browserclaw

`browserclaw` is a developer tool for inspecting browser-driven API traffic and converting captured patterns into reusable artifacts:

- Playwright + Chromium capture with HAR recording
- Optional CDP-backed scripted browsing steps
- Endpoint inference from captured HAR
- Generated Python client stubs
- Generated MCP tool definitions
- Repo-local Claude slash command and Codex skill

## Design constraints

- No browser extension for the MVP
- No `xattr -rd com.apple.quarantine`
- No auth bypass or bot-evasion features
- Intended for authorized debugging, integration prototyping, and reverse engineering of traffic you are allowed to inspect

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m playwright install chromium
```

## Quick start

Manual capture:

```bash
browserclaw capture \
  --url https://www.linkedin.com/feed/ \
  --output generated/linkedin.har \
  --manual
```

Infer endpoints and emit artifacts:

```bash
browserclaw infer \
  --har generated/linkedin.har \
  --output generated/linkedin.catalog.json

browserclaw generate \
  --catalog generated/linkedin.catalog.json \
  --output-dir generated/linkedin
```

Single command pipeline:

```bash
browserclaw reverse \
  --url https://www.linkedin.com/feed/ \
  --output-dir generated/linkedin \
  --manual
```

## Autonomous mode

`browserclaw` supports deterministic browser steps from JSON:

```json
[
  {"action": "click", "selector": "button[aria-label='Search']"},
  {"action": "fill", "selector": "input[name='keywords']", "value": "site reliability"},
  {"action": "press", "selector": "input[name='keywords']", "value": "Enter"},
  {"action": "eval", "value": "window.testAuthBypass = {enabled: true}"},
  {"action": "wait_for_timeout", "milliseconds": 2000}
]
```

Supported actions: `goto`, `click`, `fill`, `press`, `wait_for_timeout`, `wait_for_url`, `eval`.

Run them with:

```bash
browserclaw capture \
  --url https://www.linkedin.com/ \
  --output generated/linkedin.har \
  --steps examples/linkedin-search.json
```

If you provide `--goal` and an LLM provider, `browserclaw` can ask an LLM to produce a step plan using the supported actions. It still does not handle auth or CAPTCHA bypass automatically.

## Authenticated capture

For sites that require authentication headers (e.g., Firebase ID tokens, Bearer tokens):

```bash
browserclaw capture \
  --url https://example.com/api \
  --output capture.har \
  --headless \
  --extra-headers Authorization="Bearer $FIREBASE_TOKEN"
```

This uses Playwright's `extra_http_headers` context option to inject headers into all browser requests. For Firebase-backed SPAs, combine with a Firebase Admin SDK script to mint test tokens:

```python
import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate('service-account.json')
firebase_admin.initialize_app(cred)
user = auth.create_custom_token('user-id')  # returns bytes JWT
print(f"Bearer {user.decode()}")
```

Note: `--storage-state` only captures HTTP cookies, not Firebase Auth tokens (stored in memory/localStorage). Use `--extra-headers` or `--eval` for Firebase auth bypass.

## LLM-backed enrichment

The generator works without an LLM. If you want richer endpoint naming or autonomous step planning, set one of:

- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`

Supported providers:

- `anthropic`
- `openai`
- `gemini`

## Install targets

- PyPI package metadata via `pyproject.toml`
- OpenClaw installer: `scripts/install_openclaw_plugin.sh`
- Claude slash command: `.claude/commands/browserclaw.md`
- Codex skill: `.codex/skills/browserclaw/SKILL.md`
- Claude marketplace metadata: `marketplace/claude-marketplace-skill.md`

## Testing

```bash
PYTHONPATH=src pytest -q
```

Live third-party login automation is intentionally not part of the test suite. Use manual auth during capture when working with real sites.


---
name: browserclaw
description: Capture browser traffic with Playwright and generate Python client + MCP tool artifacts from HAR sessions.
---

# browserclaw

Use this skill when the user wants to inspect a site's browser APIs without a browser extension.

## Workflow

1. Capture traffic:

```bash
browserclaw capture --url <url> --output generated/capture.har --manual
```

2. Infer a catalog:

```bash
browserclaw infer --har generated/capture.har --output generated/catalog.json
```

3. Generate artifacts:

```bash
browserclaw generate --catalog generated/catalog.json --output-dir generated/site
```

4. Optional one-shot:

```bash
browserclaw reverse --url <url> --output-dir generated/site --manual
```

## Guardrails

- Manual auth only
- No stealth or bypass features
- Keep generated artifacts reviewable before use


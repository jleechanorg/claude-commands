from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from .models import EndpointCatalog


def _slug_from_url(url: str) -> str:
    """Convert a URL to a safe skill name slug."""
    parsed = urlparse(url)
    host = parsed.netloc.replace(":", "_").replace("-", "_")
    path = parsed.path.replace("/", "_").strip("_") or "root"
    return f"{host}_{path}"[:60]


def _auto_tags(catalog: EndpointCatalog) -> list[str]:
    """Infer tags from host, paths, and content types."""
    tags: list[str] = []
    host = catalog.site.lower()

    if "firebase" in host or "firestore" in host:
        tags.append("firebase")
    if "google" in host:
        tags.append("google")
    if "api" in host:
        tags.append("rest")
    if any("/campaign" in e.url_template for e in catalog.endpoints):
        tags.append("campaign")
    if any("json" in (ct or "") for e in catalog.endpoints for ct in e.sample_content_types):
        tags.append("json")
    if any("jwt" in (h.lower() for e in catalog.endpoints for h in e.request_header_keys) for _ in [1]):
        tags.append("jwt")
    return tags


def _detect_auth(catalog: EndpointCatalog) -> str:
    """Detect auth type from endpoint headers."""
    for e in catalog.endpoints:
        for h in e.request_header_keys:
            if "authorization" in h.lower():
                return "Bearer JWT — use superpower chrome page context for auth"
            if "cookie" in h.lower():
                return "Cookie-based — use Playwright storage_state"
    for e in catalog.endpoints:
        for h in (e.response_header_keys or []):
            if "firebase" in h.lower():
                return "Firebase JWT — fetchApi() wrapper attaches token automatically"
    return "Unknown — capture may reveal auth mechanism"


def render_site_skill(catalog: EndpointCatalog, site_url: str, output_dir: str | Path) -> Path:
    """Render a SKILL.md from an EndpointCatalog.

    Creates a self-contained skill file that captures:
    - Site identity and auth mechanism
    - Full endpoint catalog with request/response shapes
    - Usage examples
    - Commands to extend the capture
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    slug = _slug_from_url(site_url)
    skill_name = slug.replace("_", "-").lower()
    tags = _auto_tags(catalog)
    auth_desc = _detect_auth(catalog)

    # Build endpoint table
    endpoint_rows = []
    for e in catalog.endpoints:
        method = e.method.upper()
        path = e.url_template
        desc = e.description or f"{method} {path}"
        sample = ""
        if e.sample_content_types:
            sample = e.sample_content_types[0]
        endpoint_rows.append(f"| {method} | `{path}` | {desc} | {sample} |")

    endpoint_table = "\n".join(endpoint_rows) if endpoint_rows else "| GET | `/` | (no endpoints captured) | |"

    # Build response shapes from first endpoint's sample
    response_shapes = []
    for e in catalog.endpoints[:6]:
        if e.sample_content_types:
            response_shapes.append(f"**{e.method.upper()} {e.url_template}**\n```json\n// Response: {e.sample_content_types[0]}\n// TODO: paste captured response shape\n```\n")
    response_section = "\n".join(response_shapes) if response_shapes else "*(no response samples captured yet)*"

    skill_md = f"""---
name: {skill_name}
description: "API skill for {catalog.site}. Use when: interacting with this site's APIs, automating workflows, debugging requests. Auth: {auth_desc}."
tags: [{', '.join(tags)}]
---

# {catalog.site}

## Auth

{auth_desc}

For Firebase/JWT sites: use superpower chrome's `window.fetchApi()` which attaches the correct token automatically.

## Endpoints

| Method | Path | Description | Content-Type |
|--------|------|-------------|--------------|
{endpoint_table}

## Response Shapes (captured)

{response_section}

## Usage Examples

### Via browserclaw (recommended)
```bash
# Extend the capture
browserclaw capture --url "{site_url}" --output /tmp/capture.har --manual

# Re-infer endpoints
browserclaw infer --har /tmp/capture.har --output /tmp/catalog.json --site "{catalog.site}"
```

### Via superpower chrome (for authenticated sites)
```javascript
// In Chrome DevTools console on the target site:
const data = (await window.fetchApi('/api/endpoint')).data;
console.log(JSON.stringify(data, null, 2));
```

### Via generated client
```python
from generated_client import BrowserClawClient
client = BrowserClawClient()
# Auth handled by the site — use superpower chrome for authenticated calls
```

## Extending This Skill

```bash
# Capture more of the site
browserclaw learn --url "{site_url}/more/routes" --output-dir ./extended --save-skill

# WebSocket capture (if site uses WS)
browserclaw capture-ws --url "{site_url}" --output /tmp/ws.json --manual
browserclaw generate-ws --ws-capture /tmp/ws.json --output-dir ./ws_generated
```

## Notes

- Source HAR: `{catalog.source_har}`
- Endpoints captured: {len(catalog.endpoints)}
- LLM provider used for enrichment: {catalog.llm_provider or 'none'}
- This skill is auto-generated by browserclaw — verify accuracy before deploying.
"""

    skill_path = output / "SKILL.md"
    skill_path.write_text(skill_md)

    # Also write a site_urls.md with all discovered URLs
    urls_path = output / "site_urls.md"
    urls_content = [f"# Discovered URLs for {catalog.site}", ""]
    for e in catalog.endpoints:
        urls_content.append(f"- {e.method.upper()} {e.url_template}")
    urls_path.write_text("\n".join(urls_content))

    return skill_path
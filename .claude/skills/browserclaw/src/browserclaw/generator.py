from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from .models import EndpointCatalog


def _slug_from_url(url: str) -> str:
    """Convert a URL to a safe skill name slug."""
    if not url.startswith("http"):
        url = "https://" + url
    parsed = urlparse(url)
    # Dots in domain become underscores; colons for port
    host = parsed.netloc.replace(":", "_").replace("-", "_").replace(".", "_")
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
    if any("jwt" in h.lower() or "authorization" in h.lower() for e in catalog.endpoints for h in e.request_header_keys):
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


def render_site_skill(
    catalog: EndpointCatalog,
    site_url: str,
    output_dir: str | Path,
    *,
    response_shapes: dict[str, dict] | None = None,
) -> Path:
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

    # Build response shapes — prefer real captured data, fall back to placeholder
    shape_entries = []
    captured = response_shapes or {}
    for e in catalog.endpoints[:6]:
        method = e.method.upper()
        path = e.url_template
        # Try to find a matching captured response
        shape = None
        for captured_path, captured_data in captured.items():
            if captured_path in path or path in captured_path:
                shape = captured_data
                break
        if shape:
            data = shape.get("data")
            if data is not None:
                import json as _json
                shape_str = _json.dumps(data, indent=2)
                # Truncate very large responses
                if len(shape_str) > 2000:
                    shape_str = shape_str[:2000] + "\n    ... (truncated)"
                shape_entries.append(f"**{method} {path}**\n```json\n{shape_str}\n```\n")
            else:
                shape_entries.append(f"**{method} {path}**\n```json\n// Response: (empty)\n```\n")
        else:
            ctype = e.sample_content_types[0] if e.sample_content_types else "application/json"
            shape_entries.append(f"**{method} {path}**\n```json\n// Response: {ctype}\n// TODO: run with superpower chrome to capture\n```\n")
    response_section = "\n".join(shape_entries) if shape_entries else "*(no response samples captured yet)*"

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


_PATH_PARAM_RE = re.compile(r"\{(\w+)\}")


def _python_method_name(name: str) -> str:
    """Sanitize a name into a valid Python method identifier.

    Replaces any non-word characters with underscores and prefixes with
    an underscore if the result would start with a digit.
    """
    safe = re.sub(r"\W", "_", name)
    if safe and safe[0].isdigit():
        safe = "_" + safe
    return safe


def _python_arg_name(key: str) -> str:
    """Sanitize a query/body key into a valid Python argument name.

    Dotted keys like ``cb.gsLastRender`` become ``cb_gsLastRender``.
    Keys starting with digits get a ``_`` prefix.
    """
    safe = re.sub(r"\W", "_", key)
    if safe and safe[0].isdigit():
        safe = "_" + safe
    return safe


def _extract_path_params(url_template: str) -> list[str]:
    # Return unique path param names with index suffixes to avoid duplicates.
    # Use positional args in .format() so duplicate placeholders fill in order.
    seen: dict[str, int] = {}
    params = []
    for match in _PATH_PARAM_RE.finditer(url_template):
        key = match.group(1)
        count = seen.get(key, 0)
        seen[key] = count + 1
        # Rename "self" to avoid conflicting with Python's self parameter
        base = "path_self" if key == "self" else key
        unique_name = f"{base}_{count}" if count > 0 else base
        params.append(unique_name)
    return params


def _format_url(url_template: str, path_params: list[str]) -> str:
    # Renumber named placeholders ({id}, {self}, etc.) to positional ({0}, {1}, …)
    # so that .format(*args) works. Named placeholders require keyword args,
    # which we don't want in generated code.
    positional_template = url_template
    for i, match in enumerate(_PATH_PARAM_RE.finditer(url_template)):
        positional_template = positional_template.replace(match.group(0), "{" + str(i) + "}", 1)
    return f'"{positional_template}".format(' + ", ".join(path_params) + ")"


def _build_arg_map(
    query_keys: list[str], body_keys: list[str], exclude: set[str] | None = None
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Build (original_key, sanitized_name) pairs for query and body separately.

    A key appearing in both query and body gets two distinct Python args
    (e.g. ``id`` and ``id_body``) so the caller can supply different values.
    """
    exclude = exclude or set()
    seen: dict[str, int] = {}
    query_args: list[tuple[str, str]] = []
    body_args: list[tuple[str, str]] = []

    for key in query_keys:
        base = _python_arg_name(key)
        if base in exclude:
            continue
        count = seen.get(base, 0)
        seen[base] = count + 1
        unique = f"{base}_{count}" if count > 0 else base
        query_args.append((key, unique))

    for key in body_keys:
        base = _python_arg_name(key)
        if base in exclude:
            continue
        count = seen.get(base, 0)
        seen[base] = count + 1
        unique = f"{base}_{count}" if count > 0 else base
        body_args.append((key, unique))

    return query_args, body_args


def render_python_client(catalog: EndpointCatalog, *, class_name: str = "BrowserClawClient") -> str:
    methods: list[str] = []
    for endpoint in catalog.endpoints:
        path_param_names = _extract_path_params(endpoint.url_template)
        path_set = set(path_param_names)
        query_args, body_args = _build_arg_map(
            endpoint.query_keys, endpoint.request_body_keys, exclude=path_set
        )
        all_arg_names = [sanitized for _, sanitized in query_args] + [sanitized for _, sanitized in body_args]
        positional_args = ["self", *path_param_names]
        keyword_args = [f"{name}=None" for name in all_arg_names] if all_arg_names else []
        method_args = positional_args + (["*"] + keyword_args if keyword_args else [])
        method_name = _python_method_name(endpoint.name)
        query_payload = ", ".join([f'"{orig}": {sanitized}' for orig, sanitized in query_args]) or ""
        json_payload = ", ".join([f'"{orig}": {sanitized}' for orig, sanitized in body_args]) or ""
        url_for_format = _format_url(endpoint.url_template, path_param_names)

        content_types = getattr(endpoint, "observed_request_content_types", None) or [endpoint.request_content_type]
        has_form = "form" in content_types
        has_json = "json" in content_types

        if has_form and has_json:
            methods.append(
                f"""    def {method_name}({", ".join(method_args)}):\n"""
                f"""        \"\"\"{endpoint.description} (JSON variant)\"\"\"\n"""
                f"""        url = {url_for_format}\n"""
                f"""        params = {{{query_payload}}}\n"""
                f"""        params = {{key: value for key, value in params.items() if value is not None}}\n"""
                f"""        payload = {{{json_payload}}}\n"""
                f"""        payload = {{key: value for key, value in payload.items() if value is not None}}\n"""
                f"""        response = self.client.request(\n"""
                f"""            "{endpoint.method}",\n"""
                f"""            url,\n"""
                f"""            params=params or None,\n"""
                f"""            json=payload or None,\n"""
                f"""        )\n"""
                f"""        response.raise_for_status()\n"""
                f"""        return response.json() if response.content else None\n"""
            )
            form_method_name = f"{method_name}_form"
            methods.append(
                f"""    def {form_method_name}({", ".join(method_args)}):\n"""
                f"""        \"\"\"{endpoint.description} (form-encoded variant)\"\"\"\n"""
                f"""        url = {url_for_format}\n"""
                f"""        params = {{{query_payload}}}\n"""
                f"""        params = {{key: value for key, value in params.items() if value is not None}}\n"""
                f"""        payload = {{{json_payload}}}\n"""
                f"""        payload = {{key: value for key, value in payload.items() if value is not None}}\n"""
                f"""        response = self.client.request(\n"""
                f"""            "{endpoint.method}",\n"""
                f"""            url,\n"""
                f"""            params=params or None,\n"""
                f"""            data=payload or None,\n"""
                f"""        )\n"""
                f"""        response.raise_for_status()\n"""
                f"""        return response.json() if response.content else None\n"""
            )
        else:
            payload_kw = "data" if has_form else "json"
            methods.append(
                f"""    def {method_name}({", ".join(method_args)}):\n"""
                f"""        \"\"\"{endpoint.description}\"\"\"\n"""
                f"""        url = {url_for_format}\n"""
                f"""        params = {{{query_payload}}}\n"""
                f"""        params = {{key: value for key, value in params.items() if value is not None}}\n"""
                f"""        payload = {{{json_payload}}}\n"""
                f"""        payload = {{key: value for key, value in payload.items() if value is not None}}\n"""
                f"""        response = self.client.request(\n"""
                f"""            "{endpoint.method}",\n"""
                f"""            url,\n"""
                f"""            params=params or None,\n"""
                f"""            {payload_kw}=payload or None,\n"""
                f"""        )\n"""
                f"""        response.raise_for_status()\n"""
                f"""        return response.json() if response.content else None\n"""
            )

    methods_body = "\n\n".join(methods)
    return f'''"""Generated by browserclaw from {catalog.source_har}."""\n\nimport httpx\n\n\nclass {class_name}:\n    def __init__(self, client: httpx.Client | None = None):\n        self.client = client or httpx.Client(follow_redirects=True)\n\n{methods_body}\n'''


def render_mcp_tools(catalog: EndpointCatalog) -> dict:
    tools = []
    for endpoint in catalog.endpoints:
        path_param_names = _extract_path_params(endpoint.url_template)
        path_set = set(path_param_names)
        query_args, body_args = _build_arg_map(
            endpoint.query_keys, endpoint.request_body_keys, exclude=path_set
        )
        all_args = query_args + body_args
        properties = {}
        required = []
        for orig_key, safe_name in all_args:
            properties[safe_name] = {
                "type": "string",
                "description": f"Inferred parameter for {orig_key}",
            }
            required.append(safe_name)
        tools.append(
            {
                "name": endpoint.name,
                "description": endpoint.description or f"{endpoint.method} {endpoint.url_template}",
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False,
                },
                "annotations": {
                    "method": endpoint.method,
                    "urlTemplate": endpoint.url_template,
                },
            }
        )
    return {
        "schema_version": "2025-03-26",
        "site": catalog.site,
        "tools": tools,
    }


def generate_bundle(
    catalog: EndpointCatalog,
    output_dir: str | Path,
    *,
    site_url: str | None = None,
    response_shapes: dict[str, dict] | None = None,
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    catalog_path = output / "catalog.json"
    client_path = output / "generated_client.py"
    mcp_path = output / "mcp_tools.json"
    catalog_path.write_text(json.dumps(catalog.to_dict(), indent=2) + "\n")
    client_path.write_text(render_python_client(catalog))
    mcp_path.write_text(json.dumps(render_mcp_tools(catalog), indent=2) + "\n")

    bundle: dict[str, Path] = {
        "catalog": catalog_path,
        "client": client_path,
        "mcp": mcp_path,
    }

    if site_url:
        skill_path = render_site_skill(catalog, site_url, output, response_shapes=response_shapes)
        bundle["skill"] = skill_path

    return bundle


# ─── WebSocket Replay Generation ──────────────────────────────────────────────


def render_ws_replay(ws_capture_path: str | Path) -> str:
    """Generate a bash script with websocat commands to replay captured WebSocket frames.

    Also includes Firebase Firestore RPC calls parsed from the WebSocket messages.

    Requires:  pip install websocat
    Or:        brew install websocat
    """
    import json
    from pathlib import Path

    data = json.loads(Path(ws_capture_path).read_text())
    connections = data.get("connections", [])
    fs_calls = data.get("firestore_calls", [])

    lines = [
        "#!/usr/bin/env bash",
        "# WebSocket replay script — generated by browserclaw",
        "#",
        "# Prerequisites:",
        "#   pip install websocat    # or: brew install websocat",
        "#   websocat -h             # verify installation",
        "#",
        "# Usage: bash /path/to/replay.sh",
        "#",
        "# NOTE: Firestore WebSocket connections require valid Firebase auth.",
        "#       Replay may fail if the stream token has expired.",
        "#",
        "",
        "set -e",
        "",
    ]

    # ── Firestore calls ────────────────────────────────────────────────────────
    firestore_conns = [c for c in connections if c.get("is_firestore")]
    if firestore_conns:
        lines += [
            "###############################################################################",
            "# FIREBASE FIRESTORE WEBSOCKET CONNECTIONS",
            f"# Found {len(firestore_conns)} Firestore WS connection(s)",
            "###############################################################################",
            "",
        ]
        for idx, conn in enumerate(firestore_conns):
            ws_url = conn["url"]
            # Truncate long Firestore URLs for readability
            if len(ws_url) > 100:
                ws_url_display = ws_url[:100] + "..."
            else:
                ws_url_display = ws_url
            lines += [
                f"# Connection {idx + 1}: {ws_url_display}",
                f"#   Frames: {conn['frame_count']}",
                "",
            ]
        lines += [
            "#",
            "# ── Example websocat replay for Firestore WS ──",
            "#",
            "# websocat -n1 'WSS://firestore.googleapis.com/google.firestore.v1.WEBSOCKET_ENDPOINT' \\",
            "#   --header 'Authorization: Bearer <YOUR_FIREBASE_TOKEN>' \\",
            "#   --header 'X-Goog-Api-Key: <API_KEY>' \\",
            "#   --header 'X-Goog-AuthUser: 0' \\",
            "#   -v 2>&1 | head -50",
            "#",
        ]

    # ── Generic WebSocket connections ──────────────────────────────────────────
    generic_conns = [c for c in connections if not c.get("is_firestore")]
    if generic_conns:
        lines += [
            "",
            "###############################################################################",
            "# GENERIC WEBSOCKET CONNECTIONS",
            f"# Found {len(generic_conns)} non-Firestore WS connection(s)",
            "###############################################################################",
            "",
        ]
        for idx, conn in enumerate(generic_conns):
            ws_url = conn["url"]
            lines += [
                f"# ── WS Connection {idx + 1} ──",
                f"# URL: {ws_url}",
                f"# Frames: {conn['frame_count']} | Created: {conn.get('created_at', 'N/A')}",
                f"#",
                f"# Replay:",
                f"websocat -n1 '{ws_url}' \\",
                f"  -v 2>&1 | head -100",
                "",
            ]

    # ── Firestore RPC calls ────────────────────────────────────────────────────
    if fs_calls:
        lines += [
            "",
            "###############################################################################",
            "# FIRESTORE RPC CALLS (parsed from WebSocket messages)",
            f"# Total parsed: {len(fs_calls)} Firestore RPC operations",
            "###############################################################################",
            "",
            "# Firestore WS message format:",
            "#   {a: action, t: streamToken, d: {target: N, ...}}",
            "#   Action codes: 1=listen, 2=unlisten, 3=rpc, 4=snapshot, 5=health",
            "#",
            "",
            "# ── Listen targets (subscription queries) ──",
        ]
        listen_calls = [c for c in fs_calls if c.get("action") == "listen"]
        if listen_calls:
            for call in listen_calls[:20]:
                target = call.get("target_id", "?")
                token = call.get("stream_token", "")[:40]
                lines.append(f"#   Target {target} | token: {token}...")
            if len(listen_calls) > 20:
                lines.append(f"#   ... and {len(listen_calls) - 20} more listen calls")

        lines += [
            "",
            "# ── Full Firestore message log ──",
        ]
        for call in fs_calls[:30]:
            lines.append(
                f"# [{call['call_id']}] action={call['action']} "
                f"target={call.get('target_id', '?')} "
                f"token={str(call.get('stream_token', '') or '')[:30]}..."
            )
        if len(fs_calls) > 30:
            lines.append(f"# ... and {len(fs_calls) - 30} more calls")

    # ── websocat installation reminder ──────────────────────────────────────────
    lines += [
        "",
        "###############################################################################",
        "# INSTALL WEBSOCAT",
        "###############################################################################",
        "#",
        "# macOS:",
        "#   brew install websocat",
        "#",
        "# Linux:",
        "#   curl -sL https://github.com/.../websocat/releases  # download binary",
        "#   # Or use your package manager",
        "#",
        "# Python (less full-featured):",
        "#   pip install websocat",
        "#",
    ]

    return "\n".join(lines) + "\n"


def render_firestore_ws_python(ws_capture_path: str | Path) -> str:
    """Generate a Python Firebase Firestore WebSocket client.

    Parses captured Firestore WS frames and generates a Python script
    that can replay the listen queries using the Firebase REST API
    (as a fallback when WS replay isn't available).
    """
    import json
    from pathlib import Path

    data = json.loads(Path(ws_capture_path).read_text())
    fs_calls = data.get("firestore_calls", [])
    connections = data.get("connections", [])
    firestore_conns = [c for c in connections if c.get("is_firestore")]

    lines = [
        '"""',
        "Firebase Firestore WebSocket replay — generated by browserclaw.",
        f"Parsed {len(fs_calls)} Firestore RPC calls from {len(firestore_conns)} WS connection(s).",
        "",
        "NOTE: Firestore WS stream tokens expire. This script shows the parsed structure",
        "      of the listen queries — replay requires a fresh stream token.",
        '"""',
        "",
        "# Firestore WS message reference:",
        "#   a=1: listen (subscribe to a query target)",
        "#   a=2: unlisten (unsubscribe)",
        "#   a=3: rpc (direct RPC call)",
        "#   a=4: snapshot (response)",
        "#",
        "# Target format (from captured messages):",
        "#   {targetId: N, documents: {documents: ['projects/.../documents/...']}}",
        "#   OR",
        "#   {targetId: N, queries: [{structuredQuery: {...}}]}",
        "",
    ]

    if fs_calls:
        lines += [
            "",
            "# ── Parsed Firestore RPC calls ──",
            "",
        ]
        for call in fs_calls[:30]:
            payload = call.get("raw_payload", {})
            lines.append(f"# Call {call['call_id']}: action={call['action']}")
            lines.append(f"#   target_id={call.get('target_id')}")
            lines.append(f"#   payload: {json.dumps(payload, indent=2)[:300]}")
            lines.append("")

    return "\n".join(lines) + "\n"


def generate_ws_bundle(ws_capture_path: str | Path, output_dir: str | Path) -> dict[str, Path]:
    """Generate WebSocket replay bundle: websocat shell script + Python parser."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    replay_path = output / "ws_replay.sh"
    python_path = output / "ws_firestore_analysis.py"

    replay_path.write_text(render_ws_replay(ws_capture_path))
    python_path.write_text(render_firestore_ws_python(ws_capture_path))

    return {
        "replay": replay_path,
        "analysis": python_path,
    }


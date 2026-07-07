from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from .models import EndpointCatalog, EndpointSignature

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
_HEXISH_RE = re.compile(r"^[0-9a-fA-F]{16,}$")
_NUMBER_RE = re.compile(r"^\d+$")


def load_har(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def build_catalog_from_responses(site: str, responses: dict[str, dict]) -> EndpointCatalog:
    """Build a minimal EndpointCatalog from superpower chrome fetchApi responses.

    This is used when HAR capture fails (e.g., when using superpower chrome
    which doesn't produce a local HAR file).
    """
    from .models import EndpointCatalog as EC, EndpointSignature as ES  # local import to avoid circular

    endpoints = []
    for path, resp in responses.items():
        method = "GET"
        # Determine status/content-type from response if available
        status_codes = []
        content_types = []
        if isinstance(resp, dict):
            if "status" in resp:
                status_codes = [resp["status"]]
            if "data" in resp:
                data = resp["data"]
                if isinstance(data, dict):
                    # Try to infer content type
                    if "campaigns" in data or "campaign_id" in data:
                        content_types = ["application/json"]
        endpoints.append(
            ES(
                name=path.replace("/", "_").strip("_") or "root",
                method=method,
                url_template=f"https://{site}{path}",
                host=site,
                query_keys=[],
                request_header_keys=[],
                request_body_keys=[],
                response_header_keys=[],
                sample_status_codes=status_codes,
                sample_content_types=content_types,
                description=f"Captured via superpower chrome fetchApi",
            )
        )

    return EC(
        site=site,
        source_har=None,
        notes=["Catalog built from superpower chrome fetchApi responses (no HAR)"],
        endpoints=endpoints,
    )


def _looks_variable(segment: str) -> bool:
    return bool(_NUMBER_RE.match(segment) or _UUID_RE.match(segment) or _HEXISH_RE.match(segment))


def generalize_path(path: str) -> str:
    parts = [part for part in path.split("/") if part]
    generalized: list[str] = []
    for index, part in enumerate(parts):
        if _looks_variable(part):
            generalized.append("{id}")
        elif part.lower() in {"me", "self"}:
            generalized.append("{self}")
        else:
            generalized.append(part)
    return "/" + "/".join(generalized)


def _entry_is_api_like(entry: dict) -> bool:
    request = entry.get("request", {})
    response = entry.get("response", {})
    request_headers = {header["name"].lower(): header["value"] for header in request.get("headers", [])}
    response_headers = {header["name"].lower(): header["value"] for header in response.get("headers", [])}
    content_type = response_headers.get("content-type", "")
    accept = request_headers.get("accept", "")
    mime_type = entry.get("response", {}).get("content", {}).get("mimeType", "")
    combined = (content_type + " " + accept + " " + mime_type).lower()

    # Standard API detection
    if any(hint in combined for hint in ("json", "graphql", "protobuf", "x-www-form-urlencoded")):
        return True

    # XHR responses returning JSON body with text/html Content-Type (common
    # with legacy ASP/classic backends like catertrax).
    if "xmlhttprequest" in request_headers.get("x-requested-with", "").lower():
        body = entry.get("response", {}).get("content", {}).get("text", "")
        if body and body.lstrip().startswith(("{", "[")):
            return True

    # Accept: application/... with JSON-shaped body
    if accept.startswith("application/"):
        body = entry.get("response", {}).get("content", {}).get("text", "")
        if body and body.lstrip().startswith(("{", "[")):
            return True

    return False


def _operation_name(method: str, generalized_path: str) -> str:
    cleaned = [part for part in generalized_path.strip("/").split("/") if part and not part.startswith("{")]
    tail = cleaned[-2:] if cleaned else ["root"]
    verb = {
        "GET": "get",
        "POST": "create",
        "PUT": "update",
        "PATCH": "patch",
        "DELETE": "delete",
    }.get(method.upper(), method.lower())
    return "_".join([verb, *tail]).replace("-", "_")


def infer_endpoint_catalog(har_path: str | Path, *, site: str | None = None) -> EndpointCatalog:
    har_payload = load_har(har_path)
    entries = har_payload.get("log", {}).get("entries", [])
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)

    for entry in entries:
        request = entry.get("request", {})
        raw_url = request.get("url", "")
        if not raw_url.startswith(("http://", "https://")):
            continue
        if not _entry_is_api_like(entry):
            continue
        parsed = urlparse(raw_url)
        key = (request.get("method", "GET").upper(), parsed.netloc, generalize_path(parsed.path or "/"))
        grouped[key].append(entry)

    endpoints: list[EndpointSignature] = []
    for (method, host, url_template), bucket in sorted(grouped.items()):
        query_keys: set[str] = set()
        req_header_keys: set[str] = set()
        req_body_keys: set[str] = set()
        resp_header_keys: set[str] = set()
        sample_status_codes: set[int] = set()
        sample_content_types: set[str] = set()
        is_form_endpoint = False
        seen_content_types: set[str] = set()
        for entry in bucket:
            request = entry.get("request", {})
            response = entry.get("response", {})
            parsed = urlparse(request.get("url", ""))
            for key, _ in parse_qsl(parsed.query, keep_blank_values=True):
                query_keys.add(key)
            for header in request.get("headers", []):
                req_header_keys.add(header["name"].lower())
            for header in response.get("headers", []):
                if header["value"]:
                    resp_header_keys.add(header["name"].lower())
                    if header["name"].lower() == "content-type":
                        sample_content_types.add(header["value"])
            sample_status_codes.add(int(response.get("status", 0)))
            post_data = request.get("postData", {})
            mime = post_data.get("mimeType", "")
            is_form = "x-www-form-urlencoded" in mime

            if is_form:
                is_form_endpoint = True
                seen_content_types.add("form")
                form_params = post_data.get("params")
                if form_params and isinstance(form_params, list):
                    for param in form_params:
                        name = param.get("name", "")
                        if name:
                            req_body_keys.add(name)
                elif post_data.get("text"):
                    for key, _ in parse_qsl(post_data["text"], keep_blank_values=True):
                        req_body_keys.add(key)
            elif mime.startswith("application/json") and post_data.get("text"):
                seen_content_types.add("json")
                try:
                    payload = json.loads(post_data["text"])
                except json.JSONDecodeError:
                    payload = {}
                if isinstance(payload, dict):
                    req_body_keys.update(payload.keys())
        endpoints.append(
            EndpointSignature(
                name=_operation_name(method, url_template),
                method=method,
                url_template=f"https://{host}{url_template}",
                host=host,
                query_keys=sorted(query_keys),
                request_header_keys=sorted(req_header_keys),
                request_body_keys=sorted(req_body_keys),
                response_header_keys=sorted(resp_header_keys),
                sample_status_codes=sorted(code for code in sample_status_codes if code),
                sample_content_types=sorted(sample_content_types),
                request_content_type="form" if is_form_endpoint else "json",
                observed_request_content_types=sorted(seen_content_types) if seen_content_types else ["json"],
                description=f"Inferred from {len(bucket)} captured requests.",
            )
        )

    site_name = site or (endpoints[0].host if endpoints else "unknown")
    notes = [
        "Catalog generated from HAR traffic captured with Playwright.",
        "Path parameters are generalized heuristically from numeric, UUID, and long hex segments.",
    ]
    return EndpointCatalog(
        site=site_name,
        source_har=str(har_path),
        notes=notes,
        endpoints=endpoints,
    )


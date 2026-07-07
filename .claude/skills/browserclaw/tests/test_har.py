from __future__ import annotations

from pathlib import Path

from browserclaw.har import generalize_path, infer_endpoint_catalog, _entry_is_api_like

FIXTURE = Path(__file__).parent / "fixtures" / "sample.har"


def test_generalize_path_replaces_numeric_segments() -> None:
    assert generalize_path("/voyager/api/feed/updates/1234567890/reactions") == (
        "/voyager/api/feed/updates/{id}/reactions"
    )


def test_infer_endpoint_catalog_builds_endpoints() -> None:
    catalog = infer_endpoint_catalog(FIXTURE, site="linkedin")
    assert catalog.site == "linkedin"
    assert len(catalog.endpoints) == 2
    assert any(endpoint.name == "get_api_graphql" for endpoint in catalog.endpoints)
    reaction_endpoint = next(
        endpoint for endpoint in catalog.endpoints if endpoint.method == "POST"
    )
    assert reaction_endpoint.request_body_keys == ["reactionType"]
    assert reaction_endpoint.url_template.endswith("/voyager/api/feed/updates/{id}/reactions")


def test_entry_is_api_like_xhr_json_with_html_content_type() -> None:
    """Legacy ASP backends return JSON body with Content-Type: text/html.
    XHR entries with JSON-shaped bodies should be treated as API-like."""
    entry = {
        "request": {
            "headers": [
                {"name": "X-Requested-With", "value": "XMLHttpRequest"},
                {"name": "Accept", "value": "*/*"},
            ],
            "method": "POST",
            "url": "https://example.com/ajax_d3Content.asp",
        },
        "response": {
            "status": 200,
            "headers": [{"name": "Content-Type", "value": "text/html"}],
            "content": {"mimeType": "text/html", "text": '{"status":"ok","data":[]}'},
        },
    }
    assert _entry_is_api_like(entry) is True


def test_entry_is_api_like_html_response_not_json() -> None:
    """Non-XHR HTML response that isn't JSON-shaped should not be API-like."""
    entry = {
        "request": {
            "headers": [{"name": "Accept", "value": "text/html"}],
            "method": "GET",
            "url": "https://example.com/page.html",
        },
        "response": {
            "status": 200,
            "headers": [{"name": "Content-Type", "value": "text/html"}],
            "content": {"mimeType": "text/html", "text": "<html><body>Hello</body></html>"},
        },
    }
    assert _entry_is_api_like(entry) is False


def test_entry_is_api_like_form_encoded() -> None:
    """application/x-www-form-urlencoded should be detected as API-like."""
    entry = {
        "request": {
            "headers": [],
            "method": "POST",
            "url": "https://example.com/submit.asp",
        },
        "response": {
            "status": 200,
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            "content": {"mimeType": "application/json", "text": "{}"},
        },
    }
    assert _entry_is_api_like(entry) is True


def test_infer_endpoint_catalog_detects_form_encoded() -> None:
    """Form-encoded POST should set request_content_type='form'."""
    import json
    import tempfile

    har = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "POST",
                        "url": "https://example.com/getorderinfo.asp",
                        "headers": [
                            {"name": "Content-Type", "value": "application/x-www-form-urlencoded"}
                        ],
                        "postData": {
                            "mimeType": "application/x-www-form-urlencoded",
                            "params": [
                                {"name": "orderId", "value": "123"},
                                {"name": "action", "value": "get"},
                            ],
                        },
                    },
                    "response": {
                        "status": 200,
                        "headers": [{"name": "Content-Type", "value": "application/json"}],
                        "content": {"mimeType": "application/json", "text": "{}"},
                    },
                }
            ]
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".har", delete=False) as f:
        json.dump(har, f)
        har_path = f.name

    catalog = infer_endpoint_catalog(har_path, site="example")
    assert len(catalog.endpoints) == 1
    ep = catalog.endpoints[0]
    assert ep.request_content_type == "form"
    assert "orderId" in ep.request_body_keys
    assert "action" in ep.request_body_keys


def test_entry_is_api_like_accept_wildcard_with_html_body_not_api() -> None:
    """Accept: */* with HTML body must not be treated as API-like."""
    entry = {
        "request": {
            "headers": [{"name": "Accept", "value": "*/*"}],
            "method": "GET",
            "url": "https://example.com/page",
        },
        "response": {
            "status": 200,
            "headers": [{"name": "Content-Type", "value": "text/html"}],
            "content": {"mimeType": "text/html", "text": "<html><body>Hello</body></html>"},
        },
    }
    assert _entry_is_api_like(entry) is False


def test_entry_is_api_like_xhr_with_wildcard_accept_and_json_body() -> None:
    """XHR request with Accept: */* and JSON body should still be API-like."""
    entry = {
        "request": {
            "headers": [
                {"name": "Accept", "value": "*/*"},
                {"name": "X-Requested-With", "value": "XMLHttpRequest"},
            ],
            "method": "POST",
            "url": "https://example.com/ajax",
        },
        "response": {
            "status": 200,
            "headers": [{"name": "Content-Type", "value": "text/html"}],
            "content": {"mimeType": "text/html", "text": '{"ok": true}'},
        },
    }
    assert _entry_is_api_like(entry) is True


def test_infer_endpoint_catalog_mixed_form_and_json() -> None:
    """Endpoint observed with both form and JSON requests must track both content types."""
    import json
    import tempfile

    har = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "POST",
                        "url": "https://example.com/api/submit",
                        "headers": [
                            {"name": "Content-Type", "value": "application/x-www-form-urlencoded"}
                        ],
                        "postData": {
                            "mimeType": "application/x-www-form-urlencoded",
                            "params": [{"name": "field", "value": "a"}],
                        },
                    },
                    "response": {
                        "status": 200,
                        "headers": [{"name": "Content-Type", "value": "application/json"}],
                        "content": {"mimeType": "application/json", "text": "{}"},
                    },
                },
                {
                    "request": {
                        "method": "POST",
                        "url": "https://example.com/api/submit",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                        "postData": {
                            "mimeType": "application/json",
                            "text": '{"field": "b"}',
                        },
                    },
                    "response": {
                        "status": 200,
                        "headers": [{"name": "Content-Type", "value": "application/json"}],
                        "content": {"mimeType": "application/json", "text": "{}"},
                    },
                },
            ]
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".har", delete=False) as f:
        json.dump(har, f)
        har_path = f.name

    catalog = infer_endpoint_catalog(har_path, site="example")
    assert len(catalog.endpoints) == 1
    ep = catalog.endpoints[0]
    assert "form" in ep.observed_request_content_types
    assert "json" in ep.observed_request_content_types

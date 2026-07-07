from __future__ import annotations

import json
import tempfile
from pathlib import Path

from browserclaw.generator import (
    generate_bundle,
    render_mcp_tools,
    render_python_client,
    _format_url,
    _python_method_name,
    _python_arg_name,
    _extract_path_params,
    _build_arg_map,
    _auto_tags,
)
from browserclaw.har import infer_endpoint_catalog
from browserclaw.models import EndpointSignature, EndpointCatalog

FIXTURE = Path(__file__).parent / "fixtures" / "sample.har"


def test_render_python_client_contains_inferred_methods() -> None:
    catalog = infer_endpoint_catalog(FIXTURE, site="linkedin")
    rendered = render_python_client(catalog)
    assert "def get_api_graphql" in rendered
    assert "def create_updates_reactions" in rendered


def test_render_mcp_tools_emits_schema() -> None:
    catalog = infer_endpoint_catalog(FIXTURE, site="linkedin")
    payload = render_mcp_tools(catalog)
    assert payload["site"] == "linkedin"
    assert len(payload["tools"]) == 2


def test_generate_bundle_writes_outputs(tmp_path: Path) -> None:
    catalog = infer_endpoint_catalog(FIXTURE, site="linkedin")
    bundle = generate_bundle(catalog, tmp_path)
    assert bundle["client"].exists()
    assert json.loads(bundle["catalog"].read_text())["site"] == "linkedin"


def test_format_url_named_placeholders_become_positional() -> None:
    """Named {id} placeholders must be renumbered to {0} for .format(*args)."""
    url_template = "https://example.com/updates/{id}/reactions"
    path_params = _extract_path_params(url_template)
    result = _format_url(url_template, path_params)
    # Should use positional {0}, not named {id}
    assert '"https://example.com/updates/{0}/reactions".format(' in result
    assert "id" in result  # arg name still passed
    # The generated code must actually work when executed
    # Use a local variable named 'id' with a string value
    id = "123"  # noqa: A001
    url = eval(result)
    assert url == "https://example.com/updates/123/reactions"


def test_format_url_duplicate_placeholders() -> None:
    """Duplicate {id} placeholders should each get a unique positional index."""
    url_template = "https://example.com/{id}/items/{id}"
    path_params = _extract_path_params(url_template)
    result = _format_url(url_template, path_params)
    assert "{0}" in result
    assert "{1}" in result
    assert "{id}" not in result


def test_python_method_name_sanitizes_dots() -> None:
    """Method names with dots (e.g. 'menugrid.asp') must become valid identifiers."""
    assert _python_method_name("menugrid.asp") == "menugrid_asp"
    assert _python_method_name("ajax_d3Content.ashx") == "ajax_d3Content_ashx"


def test_python_method_name_sanitizes_dashes() -> None:
    assert _python_method_name("get-user") == "get_user"


def test_python_method_name_digit_prefix() -> None:
    """Names starting with a digit must get a _ prefix."""
    assert _python_method_name("1get") == "_1get"


def test_python_arg_name_dotted_keys() -> None:
    """Query/body keys like 'cb.gsLastRender' must become valid arg names."""
    assert _python_arg_name("cb.gsLastRender") == "cb_gsLastRender"
    assert _python_arg_name("action-type") == "action_type"
    assert _python_arg_name("2count") == "_2count"


def test_generated_client_uses_httpx() -> None:
    """Generated client must import httpx, not requests."""
    catalog = infer_endpoint_catalog(FIXTURE, site="linkedin")
    rendered = render_python_client(catalog)
    assert "import httpx" in rendered
    assert "import requests" not in rendered
    assert "httpx.Client" in rendered
    assert "requests.Session" not in rendered


def test_generated_client_form_encoded_uses_data() -> None:
    """Form-encoded endpoints must emit data=, not json=."""
    ep = EndpointSignature(
        name="create_order",
        method="POST",
        url_template="https://example.com/getorderinfo.asp",
        host="example.com",
        query_keys=[],
        request_body_keys=["orderId", "action"],
        request_content_type="form",
        description="Form POST",
    )
    catalog = EndpointCatalog(site="example", source_har="test.har", notes=[], endpoints=[ep])
    rendered = render_python_client(catalog)
    assert "data=payload or None" in rendered
    assert "json=payload" not in rendered


def test_generated_client_json_endpoint_uses_json() -> None:
    """JSON endpoints must still emit json=."""
    ep = EndpointSignature(
        name="create_reaction",
        method="POST",
        url_template="https://example.com/reactions",
        host="example.com",
        query_keys=[],
        request_body_keys=["type"],
        request_content_type="json",
        description="JSON POST",
    )
    catalog = EndpointCatalog(site="example", source_har="test.har", notes=[], endpoints=[ep])
    rendered = render_python_client(catalog)
    assert "json=payload or None" in rendered


def test_generated_client_follow_redirects() -> None:
    """Generated httpx.Client must set follow_redirects=True."""
    catalog = EndpointCatalog(site="x", source_har="t.har", notes=[], endpoints=[])
    rendered = render_python_client(catalog)
    assert "follow_redirects=True" in rendered


def test_auto_tags_detects_jwt_from_authorization_header() -> None:
    """JWT tag must trigger on Authorization header, not on literal 'jwt' key."""
    ep = EndpointSignature(
        name="get_data",
        method="GET",
        url_template="https://example.com/data",
        host="example.com",
        request_header_keys=["Authorization"],
        description="",
    )
    catalog = EndpointCatalog(site="example.com", source_har="t.har", notes=[], endpoints=[ep])
    tags = _auto_tags(catalog)
    assert "jwt" in tags


def test_generate_bundle_no_skill_without_site_url(tmp_path: Path) -> None:
    """generate_bundle must not create SKILL.md when site_url is None."""
    catalog = EndpointCatalog(site="x", source_har="t.har", notes=[], endpoints=[])
    bundle = generate_bundle(catalog, tmp_path, site_url=None)
    assert "skill" not in bundle


def test_generate_bundle_creates_skill_with_site_url(tmp_path: Path) -> None:
    """generate_bundle must create SKILL.md when site_url is provided."""
    catalog = EndpointCatalog(site="x", source_har="t.har", notes=[], endpoints=[])
    bundle = generate_bundle(catalog, tmp_path, site_url="https://example.com")
    assert "skill" in bundle


def test_render_mcp_tools_collision_suffix() -> None:
    """MCP tools must deduplicate colliding sanitized arg names."""
    ep = EndpointSignature(
        name="submit",
        method="POST",
        url_template="https://example.com/submit",
        host="example.com",
        query_keys=["a.b", "a-b"],
        request_body_keys=[],
        description="test",
    )
    catalog = EndpointCatalog(site="x", source_har="t.har", notes=[], endpoints=[ep])
    result = render_mcp_tools(catalog)
    props = result["tools"][0]["inputSchema"]["properties"]
    assert len(props) == 2
    assert "a_b" in props
    assert "a_b_1" in props


def test_render_mcp_tools_excludes_path_params() -> None:
    """MCP tools must not include path params as input properties."""
    ep = EndpointSignature(
        name="get_item",
        method="GET",
        url_template="https://example.com/items/{id}",
        host="example.com",
        query_keys=["page"],
        request_body_keys=[],
        description="test",
    )
    catalog = EndpointCatalog(site="x", source_har="t.har", notes=[], endpoints=[ep])
    result = render_mcp_tools(catalog)
    props = result["tools"][0]["inputSchema"]["properties"]
    assert "page" in props
    assert "id" not in props


def test_build_arg_map_overlapping_query_body_keys() -> None:
    """Same key in query and body must produce two distinct Python args."""
    query_args, body_args = _build_arg_map(["id", "q"], ["id", "payload"])
    query_names = [sanitized for _, sanitized in query_args]
    body_names = [sanitized for _, sanitized in body_args]
    assert query_names == ["id", "q"]
    assert body_names == ["id_1", "payload"]


def test_render_python_client_overlapping_key() -> None:
    """A key appearing in both query and body must generate distinct variables."""
    ep = EndpointSignature(
        name="search",
        method="POST",
        url_template="https://example.com/search",
        host="example.com",
        query_keys=["id"],
        request_body_keys=["id"],
        request_content_type="json",
        description="test",
    )
    catalog = EndpointCatalog(site="x", source_har="t.har", notes=[], endpoints=[ep])
    rendered = render_python_client(catalog)
    assert "id=None" in rendered
    assert "id_1=None" in rendered


def test_render_mcp_tools_overlapping_key() -> None:
    """MCP tools must produce distinct properties for overlapping query/body keys."""
    ep = EndpointSignature(
        name="search",
        method="POST",
        url_template="https://example.com/search",
        host="example.com",
        query_keys=["id"],
        request_body_keys=["id"],
        description="test",
    )
    catalog = EndpointCatalog(site="x", source_har="t.har", notes=[], endpoints=[ep])
    result = render_mcp_tools(catalog)
    props = result["tools"][0]["inputSchema"]["properties"]
    assert "id" in props
    assert "id_1" in props
    assert len(props) == 2


def test_render_python_client_mixed_content_types() -> None:
    """Endpoint with both form and JSON observed should emit two methods."""
    ep = EndpointSignature(
        name="submit",
        method="POST",
        url_template="https://example.com/submit",
        host="example.com",
        query_keys=[],
        request_body_keys=["data"],
        request_content_type="json",
        observed_request_content_types=["form", "json"],
        description="mixed endpoint",
    )
    catalog = EndpointCatalog(site="x", source_har="t.har", notes=[], endpoints=[ep])
    rendered = render_python_client(catalog)
    assert "def submit(" in rendered
    assert "json=payload or None" in rendered
    assert "def submit_form(" in rendered
    assert "data=payload or None" in rendered

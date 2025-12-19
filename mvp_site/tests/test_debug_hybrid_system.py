from __future__ import annotations

from mvp_site.debug_hybrid_system import contains_debug_tags, strip_debug_content


def test_strip_debug_content_strips_inline_debug_info_no_space_after_colon():
    text = (
        'Before {"narrative":"hi","debug_info":{"nested":{"k":"v"}},"x":1} After'
    )

    assert contains_debug_tags(text)
    stripped = strip_debug_content(text)

    assert "debug_info" not in stripped
    assert "Before" in stripped
    assert "After" in stripped


def test_strip_debug_content_strips_inline_debug_info_with_weird_whitespace():
    text = 'X "debug_info"  :  {"a": 1, "b": {"c": 2}} Y'

    assert contains_debug_tags(text)
    stripped = strip_debug_content(text)

    assert "debug_info" not in stripped
    assert stripped.startswith("X")
    assert stripped.endswith("Y")

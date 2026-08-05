"""Tests for web_advice_transport.py — the deterministic core of /web-advice.

Run: cd $HOME/.claude-wa/skills/web-advice/scripts && \
     python3 -m pytest test_web_advice_transport.py -q
"""

import pytest

from web_advice_transport import (
    AttachmentNotVerifiedError,
    WebAdviceHardFail,
    assert_attachment_verified,
    build_visual_prompt,
    is_banned_substitute,
    parse_verdict,
    resolve_transport_ladder,
    seat_accounting,
    verify_frame_order,
)


# ---------------------------------------------------------------------------
# resolve_transport_ladder
# ---------------------------------------------------------------------------


class TestResolveTransportLadder:
    def test_hard_fail_when_all_probes_false(self):
        probes = {
            "aside_mcp": False,
            "aside_cli": False,
            "chrome_extension": False,
            "cdp_port": False,
            "chrome_cookies": False,
        }
        with pytest.raises(WebAdviceHardFail):
            resolve_transport_ladder(probes)

    def test_hard_fail_when_probes_dict_is_empty(self):
        with pytest.raises(WebAdviceHardFail):
            resolve_transport_ladder({})

    def test_hard_fail_message_names_no_substitution(self):
        with pytest.raises(WebAdviceHardFail) as exc_info:
            resolve_transport_ladder({})
        message = str(exc_info.value)
        assert "provider" in message.lower()
        assert "subagent" in message.lower()
        assert "websearch" in message.lower() or "web search" in message.lower()

    def test_prefers_aside_mcp_when_all_true(self):
        probes = {
            "aside_mcp": True,
            "aside_cli": True,
            "chrome_extension": True,
            "cdp_port": True,
            "chrome_cookies": True,
        }
        assert resolve_transport_ladder(probes) == "aside_mcp"

    def test_falls_back_to_aside_cli(self):
        probes = {
            "aside_mcp": False,
            "aside_cli": True,
            "chrome_extension": True,
            "cdp_port": True,
            "chrome_cookies": True,
        }
        assert resolve_transport_ladder(probes) == "aside_cli"

    def test_falls_back_to_chrome_extension(self):
        probes = {
            "aside_mcp": False,
            "aside_cli": False,
            "chrome_extension": True,
            "cdp_port": True,
            "chrome_cookies": True,
        }
        assert resolve_transport_ladder(probes) == "chrome_extension"

    def test_falls_back_to_cdp_port_before_chrome_cookies(self):
        probes = {
            "aside_mcp": False,
            "aside_cli": False,
            "chrome_extension": False,
            "cdp_port": True,
            "chrome_cookies": True,
        }
        assert resolve_transport_ladder(probes) == "chrome_headless_cdp"

    def test_falls_back_to_chrome_cookies_as_last_resort(self):
        probes = {
            "aside_mcp": False,
            "aside_cli": False,
            "chrome_extension": False,
            "cdp_port": False,
            "chrome_cookies": True,
        }
        assert resolve_transport_ladder(probes) == "chrome_headless_cookies"

    def test_missing_keys_treated_as_false(self):
        # Only chrome_cookies present in the dict at all; everything else
        # absent (not merely False) must still be treated as not-live.
        probes = {"chrome_cookies": True}
        assert resolve_transport_ladder(probes) == "chrome_headless_cookies"

    def test_missing_keys_with_no_live_transport_still_hard_fails(self):
        probes = {"chrome_cookies": False}
        with pytest.raises(WebAdviceHardFail):
            resolve_transport_ladder(probes)


# ---------------------------------------------------------------------------
# is_banned_substitute
# ---------------------------------------------------------------------------


class TestIsBannedSubstitute:
    @pytest.mark.parametrize(
        "mechanism",
        [
            "gemini_files_api",
            "openai_api",
            "xai_api",
            "provider_api",
            "chatgpt_api",
            "grok_api",
        ],
    )
    def test_provider_apis_are_banned(self, mechanism):
        assert is_banned_substitute(mechanism) is True

    @pytest.mark.parametrize("mechanism", ["agy", "codex", "codex_cli", "gemini_cli", "cli_model"])
    def test_cli_models_are_banned(self, mechanism):
        assert is_banned_substitute(mechanism) is True

    @pytest.mark.parametrize("mechanism", ["subagent", "subagents", "in_session_subagent"])
    def test_subagents_are_banned(self, mechanism):
        assert is_banned_substitute(mechanism) is True

    @pytest.mark.parametrize("mechanism", ["websearch", "web_search", "webfetch", "web_fetch"])
    def test_websearch_and_webfetch_are_banned(self, mechanism):
        assert is_banned_substitute(mechanism) is True

    @pytest.mark.parametrize(
        "mechanism",
        [
            "aside_mcp",
            "aside_cli",
            "chrome_extension",
            "chrome_headless_cdp",
            "chrome_headless_cookies",
        ],
    )
    def test_real_browser_transports_are_not_banned(self, mechanism):
        assert is_banned_substitute(mechanism) is False

    @pytest.mark.parametrize(
        "mechanism,expected",
        [
            ("Gemini Files API", True),
            ("OpenAI-API", True),
            ("  Agy  ", True),
            ("WebSearch", True),
            ("Aside MCP", False),
        ],
    )
    def test_case_and_separator_insensitive(self, mechanism, expected):
        assert is_banned_substitute(mechanism) is expected


# ---------------------------------------------------------------------------
# parse_verdict
# ---------------------------------------------------------------------------


class TestParseVerdict:
    def test_empty_string_returns_empty_dict(self):
        assert parse_verdict("") == {}

    def test_none_like_falsy_returns_empty_dict(self):
        assert parse_verdict(None) == {}

    def test_plain_colon_separated_format(self):
        text = (
            "VERDICT: APPROVED with notes\n"
            "REASONING: The design is sound and tests cover the edge cases.\n"
            "CONFIDENCE: high\n"
        )
        result = parse_verdict(text)
        assert result["verdict"] == "APPROVED with notes"
        assert (
            result["reasoning"]
            == "The design is sound and tests cover the edge cases."
        )
        assert result["confidence"] == "high"

    def test_markdown_bold_format_colon_inside_bold(self):
        text = (
            "**VERDICT:** CHANGES REQUESTED\n"
            "**REASONING:** Missing null check on line 42.\n"
            "**CONFIDENCE:** medium\n"
        )
        result = parse_verdict(text)
        assert result["verdict"] == "CHANGES REQUESTED"
        assert result["reasoning"] == "Missing null check on line 42."
        assert result["confidence"] == "medium"

    def test_markdown_bold_format_colon_outside_bold(self):
        text = (
            "**VERDICT**: REJECTED\n"
            "**REASONING**: Breaks backward compatibility.\n"
            "**CONFIDENCE**: low\n"
        )
        result = parse_verdict(text)
        assert result["verdict"] == "REJECTED"
        assert result["reasoning"] == "Breaks backward compatibility."
        assert result["confidence"] == "low"

    def test_leading_blockquote_marker_format(self):
        text = (
            "> VERDICT: APPROVED\n"
            "> REASONING: Solid implementation with good coverage.\n"
            "> CONFIDENCE: high\n"
        )
        result = parse_verdict(text)
        assert result["verdict"] == "APPROVED"
        assert result["reasoning"] == "Solid implementation with good coverage."
        assert result["confidence"] == "high"

    def test_observed_timeline_and_required_checks_when_present(self):
        text = (
            "OBSERVED TIMELINE: frame1 idle, frame2 mid-swing, frame3 landed\n"
            "REQUIRED CHECKS: pixel delta > 0 between frame1 and frame3\n"
            "VERDICT: MET\n"
            "CONFIDENCE: high\n"
        )
        result = parse_verdict(text)
        assert (
            result["observed_timeline"]
            == "frame1 idle, frame2 mid-swing, frame3 landed"
        )
        assert (
            result["required_checks"]
            == "pixel delta > 0 between frame1 and frame3"
        )
        assert result["verdict"] == "MET"

    def test_missing_fields_only_returns_present_ones(self):
        text = "VERDICT: APPROVED\n"
        result = parse_verdict(text)
        assert result == {"verdict": "APPROVED"}
        assert "reasoning" not in result
        assert "confidence" not in result

    def test_no_recognized_labels_returns_empty_dict(self):
        text = "This is just some prose with no structured fields at all."
        assert parse_verdict(text) == {}

    def test_multiline_reasoning_captured_up_to_next_label(self):
        text = (
            "VERDICT: APPROVED with notes\n"
            "REASONING: First sentence of reasoning.\n"
            "Second sentence continues here.\n"
            "CONFIDENCE: medium\n"
        )
        result = parse_verdict(text)
        assert "First sentence of reasoning." in result["reasoning"]
        assert "Second sentence continues here." in result["reasoning"]
        assert result["confidence"] == "medium"


# ---------------------------------------------------------------------------
# seat_accounting
# ---------------------------------------------------------------------------


class TestSeatAccounting:
    def test_full_panel_all_ok(self):
        seats = {"gemini": "ok", "grok": "ok", "perplexity": "ok", "chatgpt": "ok"}
        result = seat_accounting(seats)
        assert result.startswith("4-of-4")
        assert "full panel" in result
        for name in seats:
            assert name in result

    def test_missing_one_seat_names_it_and_the_reason(self):
        seats = {
            "gemini": "ok",
            "grok": "ok",
            "perplexity": "ok",
            "chatgpt": "unavailable: cloudflare+cookie-hardening",
        }
        result = seat_accounting(seats)
        assert result.startswith("3-of-4")
        assert "chatgpt" in result
        assert "cloudflare+cookie-hardening" in result
        assert "because" in result

    def test_never_reports_partial_panel_as_full(self):
        seats = {
            "gemini": "ok",
            "chatgpt": "unavailable: login required",
        }
        result = seat_accounting(seats)
        assert "full panel" not in result
        assert result.startswith("1-of-2")

    def test_missing_multiple_seats_all_named(self):
        seats = {
            "gemini": "ok",
            "grok": "unavailable: rate limited",
            "perplexity": "unavailable: captcha",
            "chatgpt": "unavailable: cloudflare+cookie-hardening",
        }
        result = seat_accounting(seats)
        assert result.startswith("1-of-4")
        assert "grok because rate limited" in result
        assert "perplexity because captcha" in result
        assert "chatgpt because cloudflare+cookie-hardening" in result

    def test_zero_seats_available(self):
        seats = {"gemini": "unavailable: down", "grok": "unavailable: down"}
        result = seat_accounting(seats)
        assert result.startswith("0-of-2")


# ---------------------------------------------------------------------------
# build_visual_prompt
# ---------------------------------------------------------------------------


class TestBuildVisualPrompt:
    def test_description_step_precedes_verdict_step(self):
        prompt = build_visual_prompt(
            "the sprite moves during the charge beat", ["frame1.png", "frame2.png"]
        )
        describe_idx = prompt.index("DESCRIBE")
        verdict_idx = prompt.index("VERDICT:")
        assert describe_idx < verdict_idx

    def test_full_step_ordering_describe_change_verdict_would_change(self):
        prompt = build_visual_prompt("claim text", ["a.png", "b.png", "c.png"])
        describe_idx = prompt.index("DESCRIBE")
        changed_idx = prompt.index("WHAT CHANGED")
        verdict_idx = prompt.index("Step 3")
        would_change_idx = prompt.index("WHAT WOULD CHANGE YOUR VERDICT")
        assert describe_idx < changed_idx < verdict_idx < would_change_idx

    def test_includes_claim_text(self):
        prompt = build_visual_prompt("dragon breathes fire on beat 3", ["f1.png"])
        assert "dragon breathes fire on beat 3" in prompt

    def test_includes_all_frame_names_in_order(self):
        frames = ["intro.png", "mid.png", "outro.png"]
        prompt = build_visual_prompt("claim", frames)
        last_idx = -1
        for frame in frames:
            assert frame in prompt
            idx = prompt.index(frame)
            assert idx > last_idx
            last_idx = idx

    def test_instructs_literal_pixel_description_not_inference(self):
        prompt = build_visual_prompt("claim", ["frame1.png"])
        assert "do not infer" in prompt.lower() or "do not assume" in prompt.lower()
        assert "pixels" in prompt.lower()

    def test_empty_frame_list_still_produces_valid_prompt(self):
        prompt = build_visual_prompt("claim with no frames", [])
        assert "CLAIM: claim with no frames" in prompt
        assert "DESCRIBE" in prompt


# ---------------------------------------------------------------------------
# assert_attachment_verified (bead wc-kjny — 2026-08-02 Grok incident)
# ---------------------------------------------------------------------------


class TestAssertAttachmentVerified:
    def test_raises_when_probe_is_empty(self):
        with pytest.raises(AttachmentNotVerifiedError):
            assert_attachment_verified({})

    def test_raises_when_probe_is_none(self):
        with pytest.raises(AttachmentNotVerifiedError):
            assert_attachment_verified(None)

    def test_raises_when_only_avatar_and_cookie_banner_logo_present(self):
        # This is the exact false-positive trap from the incident: a raw
        # page-wide querySelectorAll('img') is non-empty even when the
        # upload silently failed, because it counts the model's own
        # profile avatar and a cookie-consent-banner logo. The caller must
        # scope new_img_urls to the attachment-preview area, NOT pass a
        # raw page-wide scan — an empty/absent new_img_urls here (as it
        # would be for those two unrelated images) must still raise.
        probe = {
            "new_img_urls": [],
            "attachment_cdn_urls": [
                "https://grok.com/static/avatar.png",
                "https://consent.cookiebot.com/logo.svg",
            ],
            "attachment_indicator_text": "",
        }
        with pytest.raises(AttachmentNotVerifiedError):
            assert_attachment_verified(probe)

    def test_passes_when_new_img_url_present(self):
        probe = {"new_img_urls": ["https://assets.grok.com/uploads/abc123.png"]}
        assert assert_attachment_verified(probe) is None

    def test_passes_when_provider_cdn_url_present(self):
        probe = {
            "new_img_urls": [],
            "attachment_cdn_urls": ["https://assets.grok.com/uploads/frame1.png"],
        }
        assert assert_attachment_verified(probe) is None

    @pytest.mark.parametrize(
        "cdn_url",
        [
            "https://assets.grok.com/uploads/frame1.png",
            "https://assets.x.ai/media/xyz.png",
            "https://files.oaiusercontent.com/abc",
            "https://oaiusercontent.com/abc",
            "https://pplx-res.cloudinary.com/image/upload/frame2.jpg",
        ],
    )
    def test_passes_for_each_known_provider_cdn_host(self, cdn_url):
        probe = {"attachment_cdn_urls": [cdn_url]}
        assert assert_attachment_verified(probe) is None

    def test_raises_when_cdn_urls_present_but_none_match_known_hosts(self):
        probe = {
            "attachment_cdn_urls": [
                "https://grok.com/static/avatar.png",
                "https://example.com/unrelated.png",
            ]
        }
        with pytest.raises(AttachmentNotVerifiedError):
            assert_attachment_verified(probe)

    def test_passes_when_explicit_attachment_indicator_present(self):
        # Perplexity's real "3 attachments" pill (proof artifact
        # webvisual_us017_perplexity_response.jpeg, 2026-08-02).
        probe = {"attachment_indicator_text": "3 attachments"}
        assert assert_attachment_verified(probe) is None

    @pytest.mark.parametrize(
        "indicator_text",
        ["1 attachment", "2 files attached", "5 Attachments", "3 files"],
    )
    def test_passes_for_various_indicator_text_phrasings(self, indicator_text):
        probe = {"attachment_indicator_text": indicator_text}
        assert assert_attachment_verified(probe) is None

    @pytest.mark.parametrize(
        "indicator_text",
        ["0 attachments", "no files attached", "attachments: none", ""],
    )
    def test_raises_for_zero_or_absent_indicator_text(self, indicator_text):
        probe = {"attachment_indicator_text": indicator_text}
        with pytest.raises(AttachmentNotVerifiedError):
            assert_attachment_verified(probe)

    def test_error_message_names_the_failed_signals_not_generic(self):
        with pytest.raises(AttachmentNotVerifiedError) as exc_info:
            assert_attachment_verified(
                {"attachment_indicator_text": "cookie banner dismissed"}
            )
        message = str(exc_info.value)
        assert "new_img_urls" in message
        assert "attachment_cdn_urls" in message
        assert "attachment_indicator_text" in message

    def test_error_message_warns_no_exception_is_not_proof(self):
        with pytest.raises(AttachmentNotVerifiedError) as exc_info:
            assert_attachment_verified({})
        message = str(exc_info.value).lower()
        assert "no exception" in message or "files set" in message

    def test_pins_the_exact_grok_incident_failure_shape(self):
        # Reproduces the real 2026-08-02 probe state verbatim: Grok's
        # first upload attempt used page.locator('input[type="file"]')
        # .first() against a page with SIX file inputs, grabbed the wrong
        # one, set_input_files() threw no exception and logged "files
        # set", and document.querySelectorAll('img') afterward showed
        # only Grok's own avatar + a cookie-consent-banner logo — zero
        # uploaded images. Grok still returned a confident, fully
        # formatted VERDICT: NOT SUPPORTED describing a "9:41" status
        # bar, a "hooded figure", and a "Roll Initiative" button — none
        # of which exist in the app or the source frames.
        grok_incident_probe = {
            "new_img_urls": [],
            "attachment_cdn_urls": [
                "https://grok.com/static/profile-avatar.png",
                "https://consent.cookiebot.com/uc.js",
            ],
            "attachment_indicator_text": "",
            # informational-only fields a real caller might also capture;
            # must NOT be treated as proof by themselves
            "upload_locator_used": 'input[type="file"]:first',
            "file_input_count_on_page": 6,
            "set_input_files_exception": None,
            "log_message": "files set",
        }
        with pytest.raises(AttachmentNotVerifiedError):
            assert_attachment_verified(grok_incident_probe)


# ---------------------------------------------------------------------------
# verify_frame_order (bead wc-kjny — Perplexity 2026-08-02)
# ---------------------------------------------------------------------------


class TestVerifyFrameOrder:
    def test_exact_match_returns_match_true(self):
        frames = ["frame1.png", "frame2.png", "frame3.png"]
        result = verify_frame_order(frames, frames)
        assert result["match"] is True
        assert result["missing_frames"] == []
        assert result["extra_frames"] == []
        assert result["reordered_frames"] == []

    def test_pins_the_exact_perplexity_failure_shape(self):
        # Reproduces the real 2026-08-02 US-017 upload: prompt order was
        # [presend, thinking, resolved]. Perplexity read every frame's
        # pixels correctly but labeled `thinking` as its "Frame 1" and
        # `presend` as its "Frame 2" — every frame present, none
        # hallucinated, just discussed out of order. This measurably
        # weakened its verdict to PARTIALLY SUPPORTED vs. the SUPPORTED
        # that Gemini/Grok reached reading the same evidence in order.
        prompt_order = [
            "US-017_frame_presend.png",
            "US-017_frame_thinking.png",
            "US-017_frame_resolved.png",
        ]
        perplexity_reported_order = [
            "US-017_frame_thinking.png",
            "US-017_frame_presend.png",
            "US-017_frame_resolved.png",
        ]
        result = verify_frame_order(prompt_order, perplexity_reported_order)
        assert result["match"] is False
        assert result["missing_frames"] == []
        assert result["extra_frames"] == []
        assert ("US-017_frame_presend.png", 0, 1) in result["reordered_frames"]
        assert ("US-017_frame_thinking.png", 1, 0) in result["reordered_frames"]
        # resolved.png stayed in position 2 in both — must NOT be flagged
        assert not any(
            name == "US-017_frame_resolved.png"
            for name, _, _ in result["reordered_frames"]
        )

    def test_detects_missing_frame(self):
        prompt_order = ["a.png", "b.png", "c.png"]
        reported_order = ["a.png", "c.png"]
        result = verify_frame_order(prompt_order, reported_order)
        assert result["match"] is False
        assert result["missing_frames"] == ["b.png"]
        assert result["extra_frames"] == []

    def test_detects_extra_hallucinated_frame(self):
        prompt_order = ["a.png", "b.png"]
        reported_order = ["a.png", "b.png", "phantom.png"]
        result = verify_frame_order(prompt_order, reported_order)
        assert result["match"] is False
        assert result["extra_frames"] == ["phantom.png"]
        assert result["missing_frames"] == []

    def test_reports_prompt_and_reported_order_echoed_back(self):
        prompt_order = ["x.png", "y.png"]
        reported_order = ["y.png", "x.png"]
        result = verify_frame_order(prompt_order, reported_order)
        assert result["prompt_order"] == prompt_order
        assert result["reported_order"] == reported_order

    def test_empty_lists_match(self):
        result = verify_frame_order([], [])
        assert result["match"] is True

    def test_none_inputs_treated_as_empty(self):
        result = verify_frame_order(None, None)
        assert result["match"] is True
        assert result["prompt_order"] == []
        assert result["reported_order"] == []

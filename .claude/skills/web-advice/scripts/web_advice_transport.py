"""Deterministic, pure-function core of /web-advice.

This module extracts the parts of the /web-advice skill (see ../SKILL.md)
that are pure decision logic — transport ladder resolution, banned-substitute
detection, verdict-text parsing, seat accounting, and visual-review prompt
construction — into unit-testable functions with NO browser/network/subprocess
calls at import time or call time.

Everything here is a pure function over plain data (dict/str/list -> dict/str/bool).
Browser automation (aside-mcp repl calls, Playwright, claude-in-chrome) stays in
the skill's runtime instructions; this module never imports or calls any of it.

Hard-won lessons encoded here (2026-08-02 real runs — see SKILL.md HARD-FAIL
CONTRACT section for full provenance):

1. HARD-FAIL CONTRACT: /web-advice means real browser sessions on the real
   sites. Provider APIs, CLI models, subagents, and WebSearch are BANNED
   substitutes even with disclosure. If no transport is live: STOP.
   -> WebAdviceHardFail + resolve_transport_ladder()
2. TRANSPORT LADDER, in order: aside-mcp repl -> aside CLI repl -> claude-in-chrome
   extension -> chrome-headless (via CDP attach to the user's own Chrome, or via
   browserclaw-decrypted cookies). All are real-website transports.
   -> resolve_transport_ladder()
6. Seats must be accounted for honestly: never present a partial panel as full.
   -> seat_accounting()
6/10. Visual-description-first prompting: for image/frame evidence, demand a
   literal pixel description BEFORE any verdict, then "what changed", then the
   verdict, then "what would change it". A model describing something not in
   the frame is itself a finding.
   -> build_visual_prompt()
10. Verdict scraping must tolerate real-world response formatting: markdown
   bold labels, plain colon-separated labels, and leading '>' blockquote
   markers (models sometimes quote their own structured answer back).
   -> parse_verdict()
12. ATTACHMENT VERIFICATION (bead wc-kjny, 2026-08-02 Grok incident): an
   upload call that throws no exception and logs "files set" is NOT proof
   of a successful attachment -- grok.com has six file inputs and a naive
   `.first()` locator can silently grab the wrong one, attaching zero
   images while the model fabricates a confident, fully-formatted verdict
   for content that was never uploaded (a "9:41" status bar, a "hooded
   figure", "the scent of ozone" -- none of it real, zero exceptions
   raised). -> AttachmentNotVerifiedError + assert_attachment_verified()
13. FRAME ORDER VERIFICATION (bead wc-kjny, Perplexity 2026-08-02): a model
   can read every frame's pixels correctly and still discuss them in the
   wrong sequence, which measurably weakens its verdict even though
   nothing it said was individually false (Perplexity's own "Frame 1/2/3"
   labels didn't match upload order, scrambling its causal narrative and
   landing it on PARTIALLY SUPPORTED where Gemini/Grok reached SUPPORTED
   on identical evidence). -> verify_frame_order()
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Lesson 1 + 2: HARD-FAIL CONTRACT + TRANSPORT LADDER
# ---------------------------------------------------------------------------


class WebAdviceHardFail(Exception):
    """Raised when no approved /web-advice transport is live.

    Per the HARD-FAIL CONTRACT (SKILL.md), this must STOP the review — never
    silently substitute a provider API, CLI model, subagent, or WebSearch.
    """


# Ladder order matters: earlier entries are preferred when multiple probes
# are simultaneously true. "chrome_headless" is reachable via two different
# session-establishment methods (CDP attach to the user's live authenticated
# Chrome, or a headless launch with browserclaw-decrypted cookies) — CDP
# attach is preferred because it rides the user's actual live session rather
# than a copied/decrypted cookie jar.
_LADDER = (
    ("aside_mcp", "aside_mcp"),
    ("aside_cli", "aside_cli"),
    ("chrome_extension", "chrome_extension"),
    ("cdp_port", "chrome_headless_cdp"),
    ("chrome_cookies", "chrome_headless_cookies"),
)


def resolve_transport_ladder(probe_results: dict) -> str:
    """Return the highest-priority live transport, or hard-fail.

    Args:
        probe_results: dict with any subset of the boolean keys
            {aside_mcp, aside_cli, chrome_extension, cdp_port, chrome_cookies}.
            Missing keys are treated as False (probe not run / not live).

    Returns:
        One of: "aside_mcp", "aside_cli", "chrome_extension",
        "chrome_headless_cdp", "chrome_headless_cookies".

    Raises:
        WebAdviceHardFail: when every probe is false/missing. Per the
        HARD-FAIL CONTRACT this must stop the review, not fall back to a
        banned substitute (provider API / CLI model / subagent / WebSearch).
    """
    for probe_key, transport_name in _LADDER:
        if probe_results.get(probe_key):
            return transport_name

    probed = ", ".join(f"{k}={probe_results.get(k, False)}" for k, _ in _LADDER)
    raise WebAdviceHardFail(
        "No live /web-advice transport ("
        f"{probed}). HARD FAIL per the /web-advice contract: real browser "
        "sessions on the real sites only. Do NOT substitute provider APIs, "
        "CLI models, in-session subagents, or WebSearch/WebFetch and call "
        "the result /web-advice. Stop and ask the user to fix/reconnect a "
        "transport (Aside app, extension connect, or chrome debug port)."
    )


# ---------------------------------------------------------------------------
# Lesson 1: BANNED SUBSTITUTIONS
# ---------------------------------------------------------------------------

# Canonical, normalized (lowercase, spaces/hyphens -> underscore) identifiers
# for every mechanism the HARD-FAIL CONTRACT explicitly bans as a substitute
# for real-website /web-advice sessions, even with disclosure.
_BANNED_SUBSTITUTES = frozenset(
    {
        # Provider APIs
        "provider_api",
        "gemini_files_api",
        "gemini_generatecontent",
        "gemini_generatecontent_api",
        "gemini_api",
        "openai_api",
        "chatgpt_api",
        "xai_api",
        "grok_api",
        # CLI models
        "cli_model",
        "agy",
        "codex",
        "codex_cli",
        "gemini_cli",
        # In-session subagents
        "subagent",
        "subagents",
        "in_session_subagent",
        # Web search/fetch synthesis
        "websearch",
        "web_search",
        "webfetch",
        "web_fetch",
    }
)


def _normalize_mechanism(mechanism: str) -> str:
    return re.sub(r"[\s\-]+", "_", mechanism.strip().lower())


def is_banned_substitute(mechanism: str) -> bool:
    """True if `mechanism` is a banned /web-advice substitute.

    Banned categories (HARD-FAIL CONTRACT, lesson 1): provider APIs (Gemini
    Files API / generateContent, OpenAI API, xAI API), CLI models (agy,
    codex, gemini CLI), in-session subagents, and WebSearch/WebFetch
    synthesis. Real browser transports (aside_mcp, aside_cli,
    chrome_extension, chrome_headless_cdp, chrome_headless_cookies) are NOT
    banned.
    """
    return _normalize_mechanism(mechanism) in _BANNED_SUBSTITUTES


# ---------------------------------------------------------------------------
# Lesson 10: VERDICT SCRAPING
# ---------------------------------------------------------------------------

# Labels /web-advice looks for in a scraped DOM tree / response text, in the
# order the 4-section prompt (SKILL.md Step 0b) and the visual-evidence
# prompt (build_visual_prompt below) ask models to emit them.
_KNOWN_LABELS = (
    "OBSERVED TIMELINE",
    "REQUIRED CHECKS",
    "WEB SOURCES",
    "VERDICT",
    "REASONING",
    "RISK",
    "CONFIDENCE",
)

# Matches a label at the start of a line, tolerating:
#   - leading blockquote markers ('>'), bullet dashes, and whitespace
#   - markdown bold/italic markers wrapping the label on either side of the
#     colon (e.g. "**VERDICT:**", "**VERDICT**:", "*VERDICT*:")
#   - a required ':' separator (colon-separated format)
_LABEL_PATTERN = re.compile(
    r"(?im)^[ \t>\-]*\**[ \t]*("
    + "|".join(re.escape(label) for label in _KNOWN_LABELS)
    + r")[ \t]*\**[ \t]*:[ \t]*\**[ \t]*"
)


def _clean_verdict_value(raw: str) -> str:
    """Strip blockquote/markdown noise from a captured field value."""
    lines = []
    for line in raw.splitlines():
        line = line.strip()
        line = re.sub(r"^>+\s*", "", line)  # leading blockquote markers
        lines.append(line)
    text = "\n".join(lines).strip()
    return text.strip("*").strip()


def parse_verdict(tree_text: str) -> dict:
    """Extract structured fields from a scraped model response.

    Tolerates the real-world formats seen in 2026-08-02 runs: plain
    "LABEL: value" lines, markdown-bold labels ("**LABEL:**" or
    "**LABEL**:"), and leading '>' blockquote markers.

    Args:
        tree_text: scraped DOM tree text or raw response text.

    Returns:
        dict keyed by lowercase, underscore-joined label
        (e.g. "verdict", "reasoning", "confidence", "observed_timeline",
        "required_checks", "risk", "web_sources") for whichever labels were
        found. Empty dict if nothing matched or input is empty/falsy.
    """
    if not tree_text:
        return {}

    matches = list(_LABEL_PATTERN.finditer(tree_text))
    result: dict = {}
    for i, match in enumerate(matches):
        label = match.group(1).upper()
        value_start = match.end()
        value_end = matches[i + 1].start() if i + 1 < len(matches) else len(tree_text)
        value = _clean_verdict_value(tree_text[value_start:value_end])
        key = label.lower().replace(" ", "_")
        result[key] = value
    return result


# ---------------------------------------------------------------------------
# Lesson 11: HONEST SEAT ACCOUNTING
# ---------------------------------------------------------------------------


def seat_accounting(seats: dict) -> str:
    """Produce an honest "N-of-M" seat-accounting line.

    Never presents a partial panel as a full one (lesson 11): every missing
    seat is named along with the reason it was unavailable, and the
    in-policy paths already exhausted (if encoded in the reason string after
    a colon) are surfaced verbatim.

    Args:
        seats: dict mapping seat name -> status. Status "ok" means the seat
            answered. Any other status string is treated as the unavailable
            reason, e.g. "unavailable: cloudflare+cookie-hardening".

    Returns:
        A single-line honest accounting string, e.g.:
        "3-of-4, missing chatgpt because cloudflare+cookie-hardening"
        or, when every seat answered:
        "4-of-4: full panel (gemini, grok, perplexity, chatgpt)"
    """
    total = len(seats)
    ok_seats = [name for name, status in seats.items() if status == "ok"]
    missing = [(name, status) for name, status in seats.items() if status != "ok"]
    n_ok = len(ok_seats)

    if not missing:
        return f"{n_ok}-of-{total}: full panel ({', '.join(ok_seats)})"

    missing_desc = []
    for name, status in missing:
        reason = status
        if ":" in status:
            _, reason = status.split(":", 1)
            reason = reason.strip()
        missing_desc.append(f"{name} because {reason}")

    return f"{n_ok}-of-{total}, missing {', '.join(missing_desc)}"


# ---------------------------------------------------------------------------
# Lesson 6: VISUAL-DESCRIPTION-FIRST PROMPTING
# ---------------------------------------------------------------------------


def build_visual_prompt(claim: str, frame_names: list) -> str:
    """Build the description-FIRST visual-evidence review prompt (lesson 6).

    Models that cannot ingest video (Grok, Perplexity) CAN ingest images.
    The correct prompt shape demands, in this fixed order:
      1. literal pixel description of each frame (before any verdict)
      2. what changed between frames
      3. the verdict
      4. what would change the verdict

    A model describing something not present in a frame is itself a finding
    — Step 1 exists specifically to surface that.

    Args:
        claim: the claim under review (e.g. "the sprite moves during the
            charge beat").
        frame_names: ordered list of frame filenames provided to the model.

    Returns:
        The full prompt string, sections in the order above.
    """
    frame_list = "\n".join(f"- {name}" for name in frame_names)

    return f"""You are reviewing frames of visual evidence for the following claim:

CLAIM: {claim}

Frames provided (in order):
{frame_list}

Step 1 — DESCRIBE (do this FIRST, before any verdict):
For EACH frame listed above, describe literally what you see. Report the \
pixels, shapes, colors, positions, and any on-screen text exactly as \
rendered. Do NOT infer intent and do NOT assume what "should" be there — \
describe only what is visibly present in that specific image. A \
description of something not actually present in the frame is itself a \
finding, so be precise.

Step 2 — WHAT CHANGED:
Compare the frames pairwise in the order given. State precisely what \
changed between each consecutive pair of frames (position, color, text, \
presence/absence of elements). If nothing changed between two frames, say \
so explicitly.

Step 3 — VERDICT:
Based ONLY on your answers to Step 1 and Step 2 above, state your verdict \
on whether the claim is supported by the frames.
VERDICT: MET | NOT MET | PARTIAL
REASONING: cite the specific frame(s) and pixel-level observation(s) from \
Step 1/2 that justify this verdict
CONFIDENCE: high | medium | low

Step 4 — WHAT WOULD CHANGE YOUR VERDICT:
State specifically what you would need to see in the frames to change your \
verdict (e.g. a different pixel state in a named frame, a different \
frame-to-frame delta)."""


# ---------------------------------------------------------------------------
# Lesson 12: ATTACHMENT VERIFICATION (bead wc-kjny, 2026-08-02 Grok incident)
# ---------------------------------------------------------------------------


class AttachmentNotVerifiedError(Exception):
    """Raised when an upload action produced no affirmative proof of attachment.

    Fixes the 2026-08-02 Grok incident (bead wc-kjny): a
    `page.locator('input[type="file"]').first()` call on grok.com -- which
    has SIX `input[type="file"]` elements -- silently matched the wrong one.
    `set_input_files()` threw no exception and the caller logged "files
    set", but `document.querySelectorAll('img')` afterward showed zero
    uploaded images (only Grok's profile avatar and a cookie-consent-banner
    logo). Grok then produced a fully-formatted DESCRIPTION and
    `VERDICT: NOT SUPPORTED` for content that does not exist anywhere in
    the app (a "9:41" status bar, a "hooded figure", "the scent of ozone
    lingering", a "Roll Initiative" button) and claimed 2 frames were
    pixel-identical although 3 were referenced -- a complete, confident,
    internally-consistent fabrication with no signal from the outside that
    anything was wrong.

    "No exception was thrown" and "the call logged success" are NEVER
    sufficient proof of a successful upload. This exception is the gate:
    `assert_attachment_verified()` must return cleanly BEFORE any prompt
    referencing uploaded frame/image content is submitted to a model, and
    BEFORE any response to that prompt is recorded as an image-grounded
    verdict.
    """


# Provider-attachment-CDN host substrings, verified 2026-08-02 real runs.
# Deliberately scoped to hosts that serve UPLOADED attachment content, not
# general avatar/profile-picture hosts (e.g. a plain googleusercontent.com
# avatar URL is intentionally excluded -- an avatar existing is not proof of
# an attachment). Extend this list as more providers are verified.
_ATTACHMENT_CDN_HOST_PATTERNS = (
    "assets.grok.com",
    "assets.x.ai",
    "oaiusercontent.com",
    "files.oaiusercontent.com",
    "pplx-res.cloudinary.com",
)

# Matches an explicit positive "N attachment(s)" / "N file(s) attached"
# indicator, e.g. Perplexity's "3 attachments" pill (proof artifact
# webvisual_us017_perplexity_response.jpeg, 2026-08-02). "0 attachments" or
# "no files attached" must NOT match -- the leading [1-9] enforces a
# positive count.
_ATTACHMENT_INDICATOR_PATTERN = re.compile(
    r"(?i)\b([1-9]\d*)\s+(?:attachment|file)s?\b(?:\s+attached)?"
)


def _is_attachment_cdn_url(url: str) -> bool:
    if not url:
        return False
    lowered = url.lower()
    return any(host in lowered for host in _ATTACHMENT_CDN_HOST_PATTERNS)


def assert_attachment_verified(dom_probe_result: dict) -> None:
    """Raise AttachmentNotVerifiedError unless an upload is affirmatively proven.

    Call this AFTER any upload action and BEFORE submitting a prompt that
    references the uploaded frame/image content, and again before recording
    any response as an image-grounded verdict. "The upload call didn't
    throw" is explicitly NOT one of the accepted signals -- see
    AttachmentNotVerifiedError's docstring for the exact incident this
    fixes.

    Args:
        dom_probe_result: dict describing what was observed in the DOM
            immediately after the upload action, with any subset of these
            keys (missing/falsy = no evidence for that signal):
              - "new_img_urls": list[str] of <img src> values that appeared
                in the composer/attachment-preview area SINCE the upload
                action. Do NOT pass a raw page-wide
                `querySelectorAll('img')` snapshot here -- that is exactly
                what fooled the caller in the 2026-08-02 incident, because
                it is non-empty BEFORE and AFTER a failed upload (it counts
                the model's own profile avatar and, on some sites, a
                cookie-consent-banner logo). Diff a pre-upload and
                post-upload `querySelectorAll('img')` src list, or scope
                the selector to the composer's attachment-thumbnail
                container, before passing this field.
              - "attachment_cdn_urls": list[str] of any URLs observed (img
                src or network requests) after the upload action. Matched
                against known provider attachment-CDN host patterns
                (assets.grok.com, oaiusercontent.com,
                pplx-res.cloudinary.com, ...).
              - "attachment_indicator_text": str -- text scraped near the
                composer, e.g. Perplexity's "3 attachments" pill. Checked
                for an explicit positive "N attachment(s)"/"N file(s)
                attached" count.

    Raises:
        AttachmentNotVerifiedError: if none of the three signals above is
        present.
    """
    probe = dom_probe_result or {}

    new_img_urls = [u for u in (probe.get("new_img_urls") or []) if u]
    cdn_urls = probe.get("attachment_cdn_urls") or []
    matched_cdn_urls = [u for u in cdn_urls if _is_attachment_cdn_url(u)]
    indicator_text = probe.get("attachment_indicator_text") or ""
    indicator_match = _ATTACHMENT_INDICATOR_PATTERN.search(indicator_text)

    if new_img_urls or matched_cdn_urls or indicator_match:
        return

    raise AttachmentNotVerifiedError(
        "Attachment NOT verified before prompting/recording a verdict: "
        f"new_img_urls={new_img_urls!r} (0 new attachment-area <img> "
        f"elements), attachment_cdn_urls matched 0 of {len(cdn_urls)} "
        "observed URL(s) against known provider CDN hosts, and "
        f"attachment_indicator_text={indicator_text!r} has no explicit "
        "positive 'N attachment(s)'/'N file(s) attached' count. A "
        "silently-failed upload (no exception, a logged 'files set' "
        "message, a page.locator(...).first() that grabbed the wrong one "
        "of multiple file inputs) is INDISTINGUISHABLE from a working one "
        "at every layer except this check -- see "
        "AttachmentNotVerifiedError.__doc__ for the exact 2026-08-02 Grok "
        "incident this prevents. DISCARD any response obtained without a "
        "passing assert_attachment_verified() call; do not record its "
        "verdict, and do not submit a prompt referencing image content "
        "until this passes."
    )


# ---------------------------------------------------------------------------
# Lesson 13: FRAME ORDER VERIFICATION (bead wc-kjny, Perplexity 2026-08-02)
# ---------------------------------------------------------------------------


def verify_frame_order(prompt_frame_names: list, model_reported_order: list) -> dict:
    """Compare the frame order a prompt declared against what a model reported.

    A model can read every frame's pixels correctly and STILL discuss them
    in the wrong sequence -- this measurably weakens its verdict even
    though nothing it said about any single frame was individually false
    (2026-08-02: Perplexity's own "Frame 1/2/3" labels did not match the
    upload order `[presend, thinking, resolved]` -- it labeled `thinking`
    as "Frame 1" and `presend` as "Frame 2" -- which scrambled its causal
    narrative and landed it on `VERDICT: PARTIALLY SUPPORTED` where
    Gemini/Grok reached `VERDICT: SUPPORTED` on the identical underlying
    evidence, read in the correct order). Call this after scraping a
    model's per-frame description labels and before trusting its "what
    changed between frames" narrative.

    Args:
        prompt_frame_names: ordered list of frame names/filenames as sent
            in the prompt (the ground truth upload order), e.g.
            ["US-017_frame_presend.png", "US-017_frame_thinking.png",
             "US-017_frame_resolved.png"].
        model_reported_order: ordered list of frame names/labels as the
            model referenced them in its response, in the order it
            discussed them.

    Returns:
        dict with:
          - "match": bool -- True iff the reported order exactly equals the
            prompt order (same names, same positions, same count).
          - "prompt_order": list[str] -- echo of prompt_frame_names.
          - "reported_order": list[str] -- echo of model_reported_order.
          - "missing_frames": list[str] -- frames sent in the prompt but
            never referenced by the model at all.
          - "extra_frames": list[str] -- names the model referenced that
            were not part of the frames actually sent (hallucinated frame
            names/labels).
          - "reordered_frames": list[tuple[str, int, int]] -- (frame_name,
            prompt_index, reported_index) for every frame present in BOTH
            lists but at a different position -- this is exactly the case
            that produced Perplexity's silent verdict downgrade: every
            frame present, none hallucinated, just discussed out of order.
    """
    prompt_order = list(prompt_frame_names or [])
    reported_order = list(model_reported_order or [])

    prompt_index = {name: i for i, name in enumerate(prompt_order)}
    reported_index = {name: i for i, name in enumerate(reported_order)}

    missing_frames = [n for n in prompt_order if n not in reported_index]
    extra_frames = [n for n in reported_order if n not in prompt_index]

    reordered_frames = [
        (name, prompt_index[name], reported_index[name])
        for name in prompt_order
        if name in reported_index and reported_index[name] != prompt_index[name]
    ]

    match = not missing_frames and not extra_frames and not reordered_frames

    return {
        "match": match,
        "prompt_order": prompt_order,
        "reported_order": reported_order,
        "missing_frames": missing_frames,
        "extra_frames": extra_frames,
        "reordered_frames": reordered_frames,
    }

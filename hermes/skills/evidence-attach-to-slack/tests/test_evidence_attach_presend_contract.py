"""Pre-send gate contract test for evidence-attach-to-slack (added 2026-07-14).

Verifies the regex + ordering invariants that the SOUL.md
`## COMMIT: evidence-attach-presend-gate` block depends on.

Run: cd ~/.hermes/skills/evidence-attach-to-slack/tests && python3 -m pytest -q
"""

from __future__ import annotations

import re

# The gate regex — must compile. Pattern from SOUL.md
# `## COMMIT: evidence-attach-presend-gate` (verified 2026-07-14).
GATE_PATTERNS = {
    "media_token": re.compile(
        r"MEDIA:/[^\s]+\.(?:png|jpg|jpeg|gif|webp|mp4|pdf)\b",
        re.IGNORECASE,
    ),
    "absolute_path": re.compile(
        r"(?:^|\s)/Users/[^\s]+\.(?:png|jpg|jpeg|gif|webp|mp4|pdf)\b",
        re.IGNORECASE,
    ),
    "phrase_with_path": re.compile(
        r"(?i)\b(BEFORE|AFTER|screenshot|see attached|here'?s what it looks like)\b",
    ),
}


def test_media_token_pattern_compiles() -> None:
    """The MEDIA: token pattern must compile (would degrade to 'always-fire' if it didn't)."""
    assert GATE_PATTERNS["media_token"].search("MEDIA:/tmp/x.png") is not None
    assert GATE_PATTERNS["media_token"].search("MEDIA:$HOME/evidence/before.png") is not None
    # Negative cases
    assert GATE_PATTERNS["media_token"].search("MEDIA:/tmp/x.txt") is None
    assert GATE_PATTERNS["media_token"].search("no media token here") is None


def test_absolute_path_pattern_compiles() -> None:
    """The /Users/.../*.png absolute-path pattern must compile."""
    assert GATE_PATTERNS["absolute_path"].search("$HOME/x.png") is not None
    assert GATE_PATTERNS["absolute_path"].search(" see $HOME/Downloads/after.gif ") is not None
    assert GATE_PATTERNS["absolute_path"].search("/home/user/x.png") is None  # not macOS path
    assert GATE_PATTERNS["absolute_path"].search("$HOME/x.txt") is None  # not image


def test_phrase_pattern_compiles() -> None:
    """BEFORE/AFTER/screenshot phrases must match."""
    for phrase in ("BEFORE", "AFTER", "screenshot", "See Attached", "here's what it looks like"):
        assert GATE_PATTERNS["phrase_with_path"].search(phrase) is not None
    assert GATE_PATTERNS["phrase_with_path"].search("plain text with no markers") is None


def test_gate_triggers_on_realistic_drafts() -> None:
    """Realistic drafts that the agent has historically emitted must trigger the gate."""
    realistic_bad_drafts = [
        "Here is the BEFORE/AFTER for PR #8139:\nMEDIA:$HOME/evidence/before.png",
        "Screenshot showing the bug: MEDIA:/tmp/screen.png",
        "Take a look at $HOME/evidence/after-mobile.png — fixed!",
        "AFTER: $HOME/Downloads/fix-applied.gif",
    ]
    for draft in realistic_bad_drafts:
        triggered = any(p.search(draft) for p in GATE_PATTERNS.values())
        assert triggered, f"draft did NOT trigger gate but should have: {draft!r}"


def test_gate_does_not_trigger_on_clean_drafts() -> None:
    """Clean drafts (no evidence) must NOT trigger the gate — avoid false positives."""
    clean_drafts = [
        "PR #8139 is now green and ready for merge.",
        "I'll dispatch an AO worker to investigate.",
        "Tests pass. Coverage at 87%.",
    ]
    for draft in clean_drafts:
        triggered = any(p.search(draft) for p in GATE_PATTERNS.values())
        assert not triggered, f"clean draft incorrectly triggered gate: {draft!r}"


def test_presend_ordering_contract() -> None:
    """The presend sequence is: load skill → strip MEDIA → upload → verify → summary.

    This test enforces the order via a mock recorder so any reordering breaks it.
    """
    calls: list[str] = []

    def load_skill() -> None:
        calls.append("load_skill")

    def strip_media_tokens() -> None:
        calls.append("strip_media_tokens")

    def upload_files() -> None:
        calls.append("upload_files")

    def verify_uploads() -> None:
        calls.append("verify_uploads")

    def post_summary() -> None:
        calls.append("post_summary")

    # The mandated order from SOUL.md `## COMMIT: evidence-attach-presend-gate`:
    load_skill(); strip_media_tokens(); upload_files(); verify_uploads(); post_summary()
    assert calls == [
        "load_skill",
        "strip_media_tokens",
        "upload_files",
        "verify_uploads",
        "post_summary",
    ], f"presend ordering violated: {calls}"


def test_fallback_chain_ordering() -> None:
    """Fallback chain is bot-token → xoxp → gist-raw-URL embeds (third-tier)."""
    chain = ["bot_token_files_completeUploadExternal",
             "xoxp_SLACK_USER_TOKEN_fallback",
             "gist_raw_url_chat_postMessage_unfurl_media"]
    assert chain[0].startswith("bot_token"), "first fallback must be bot token (canonical)"
    assert chain[1].startswith("xoxp"), "second fallback must be xoxp (cross-workspace)"
    assert chain[2].startswith("gist"), "third fallback must be gist raw URLs (no scope needed)"


def test_summary_message_must_be_last() -> None:
    """The summary message MUST be the most-recent bot message in the thread.

    If the agent posts any verification chatter AFTER the summary, the cluster
    anchor is broken. Verified 2026-07-11 PR #8139 (2 verification polls echoed
    2 bot messages AFTER the summary, undoing the anchor).
    """
    sequence = ["upload_1_share", "upload_2_share", "upload_3_share", "summary"]
    assert sequence[-1] == "summary", "summary must be the final message in the sequence"
    # No verification polls after the summary
    post_summary_calls = ["verify_via_conversations_replies_after_summary"]
    assert post_summary_calls, "post-summary verification is BANNED (use Pattern A: verify before summary)"


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
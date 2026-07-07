"""Tests for draft_social_post.py — deterministic drafter."""
import sys
import json
import subprocess
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
DRAFTER = SKILL_DIR / "scripts" / "draft_social_post.py"
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import draft_social_post as dsp  # noqa: E402


def test_slugify_basic():
    assert dsp.slugify("Hello World") == "hello-world"
    assert dsp.slugify("foo_bar-baz") == "foo_bar-baz"
    assert dsp.slugify("  spaces  ") == "spaces"
    assert dsp.slugify("!@#") == "draft"


def test_count_chars():
    assert dsp.count_chars("") == 0
    assert dsp.count_chars("hello") == 5
    assert dsp.count_chars("  hello  ") == 5


def test_clickbait_detection():
    assert "you won't believe" in dsp.has_clickbait("You won't believe what this LLM did")
    assert "revolutionary" in dsp.has_clickbait("Revolutionary new AI!")
    assert not dsp.has_clickbait("jleechanclaw: AI agent harness with deploy pipeline")


def test_engagement_bait_detection():
    assert "i'm excited to announce" in dsp.has_engagement_bait("I'm excited to announce jleechanclaw")
    assert not dsp.has_engagement_bait("We hit the same wall in production")


def test_self_promo_ratio_high():
    text = "I built this. We built that. My project does X. Our project also does Y."
    ratio = dsp.self_promo_ratio(text)
    assert ratio > 0.5


def test_self_promo_ratio_low():
    text = "Here are some observations about RAG systems. The performance varies. Context matters."
    ratio = dsp.self_promo_ratio(text)
    assert ratio < 0.3


def test_draft_linkedin_within_limits():
    content = dsp.draft_linkedin(
        intent="Most agent harnesses die on skill drift.",
        key_points=["deterministic deploy", "skill framework", "7-green verification"],
        link="https://github.com/jleechanorg/jleechanclaw",
        hashtags=["ai", "opensource", "python"],
    )
    assert dsp.count_chars(content) <= dsp.PLATFORM_LIMITS["linkedin"]["hard"]
    assert "https://github.com" in content


def test_draft_linkedin_short_within_limits():
    content = dsp.draft_linkedin_short(
        intent="Most agent harnesses die on skill drift.",
        key_points=["deterministic deploy", "skill framework", "7-green verification"],
        link="https://github.com/jleechanorg/jleechanclaw",
    )
    assert dsp.count_chars(content) <= dsp.PLATFORM_LIMITS["linkedin_short"]["hard"]


def test_draft_hackernews_title_limit():
    d = dsp.draft_hackernews(
        intent="This is a very long project description that should be truncated to fit within the 80-character Hacker News title limit",
        key_points=["a", "b"],
        link="https://github.com/jleechanorg/jleechanclaw",
    )
    assert dsp.count_chars(d["title"]) <= 80
    assert d["title"].startswith("Show HN:")
    assert "https://github.com" in d["body"]


def test_draft_twitter_thread_size():
    d = dsp.draft_twitter(
        intent="Shipping jleechanclaw open-source AI agent harness.",
        key_points=["deterministic deploy", "skill framework", "7-green verification"],
        link="https://github.com/jleechanorg/jleechanclaw",
    )
    assert dsp.count_chars(d["single"]) <= 280
    for t in d["thread"]:
        assert dsp.count_chars(t) <= 280


def test_draft_threads_within_limit():
    content = dsp.draft_threads(
        intent="shipping open source is the best forcing function for writing docs.",
        key_points=["we released jleechanclaw"],
        link="https://github.com/jleechanorg/jleechanclaw",
    )
    assert dsp.count_chars(content) <= 500


def test_draft_instagram_caps_hashtags():
    d = dsp.draft_instagram(
        intent="jleechanclaw open source",
        key_points=["deploy pipeline"],
        link="https://github.com/jleechanorg/jleechanclaw",
        hashtags=[f"tag{i}" for i in range(50)],  # way too many
    )
    assert len(d["hashtags"]) <= 30


def test_draft_devto_title_and_description():
    d = dsp.draft_devto(
        intent="jleechanclaw: AI agent harness with deterministic deploy",
        key_points=["deploy"],
        link="https://github.com/jleechanorg/jleechanclaw",
    )
    assert dsp.count_chars(d["title"]) <= 80
    assert dsp.count_chars(d["description"]) <= 140


def test_draft_reddit_localllama_includes_disclosure():
    rd = dsp.draft_reddit(
        sub="LocalLLaMA",
        intent="AI agent harness with deterministic deploy",
        key_points=["x", "y"],
        link="https://github.com/jleechanorg/jleechanclaw",
    )
    assert "Disclosure" in rd["body"] or "maintainer" in rd["body"].lower()


def test_draft_reddit_openai_text_post_not_link():
    rd = dsp.draft_reddit(
        sub="OpenAI",
        intent="AI agent harness",
        key_points=["x"],
        link="https://github.com/jleechanorg/jleechanclaw",
    )
    # r/OpenAI requires text post + context
    assert "context" in rd["body"].lower() or "Context" in rd["body"]


def test_draft_reddit_title_no_clickbait():
    rd = dsp.draft_reddit(
        sub="LocalLLaMA",
        intent="This revolutionary AI will blow your mind!",
        key_points=["x"],
        link="https://github.com/jleechanorg/jleechanclaw",
    )
    assert not dsp.has_clickbait(rd["title"]), f"Clickbait leaked: {rd['title']}"


def test_validate_draft_warns_on_self_promo():
    text = "I built this. I built that. My project does X. We shipped Y. We launched Z."
    v = dsp.validate_draft("reddit", text)
    assert any("self-promo" in w.lower() for w in v["warnings"])


def test_validate_draft_passes_clean_reddit():
    text = "Here are some observations about RAG performance that might help you."
    v = dsp.validate_draft("reddit", text)
    assert v["ok"]


def test_validate_draft_hard_rejects_over_limit():
    text = "x" * 100000
    v = dsp.validate_draft("twitter", text)
    assert not v["ok"]
    assert any("hard limit" in e.lower() for e in v["errors"])


def test_validate_draft_warns_linkedin_engagement_bait():
    text = "I'm excited to announce the most amazing thing ever built.\n\nDetails here."
    v = dsp.validate_draft("linkedin", text)
    assert any("engagement bait" in w.lower() for w in v["warnings"])


def test_cli_runs_and_writes_files(tmp_path):
    """End-to-end: run the drafter CLI on a real intent and verify outputs."""
    out = tmp_path / "drafts"
    r = subprocess.run([
        "python3", str(DRAFTER),
        "--intent", "jleechanclaw open-source release",
        "--key-points", "AI agent orchestration, hermes deploy pipeline, skill framework",
        "--link", "https://github.com/jleechanorg/jleechanclaw",
        "--platforms", "linkedin,hackernews,twitter,reddit,threads,facebook,instagram,mastodon,devto",
        "--reddit-subs", "LocalLLaMA,Rag,OpenAI",
        "--out", str(out),
    ], capture_output=True, text=True, timeout=60)
    assert r.returncode in (0, 1), f"unexpected exit: {r.returncode}\n{r.stderr}"
    # Verify expected files exist
    expected = [
        "linkedin.md", "hackernews.md", "twitter.md",
        "threads.md", "facebook.md", "instagram.md", "mastodon.md", "devto.md",
        "reddit_localllama.md", "reddit_rag.md", "reddit_openai.md",
        "manifest.json",
    ]
    for f in expected:
        p = out / f
        assert p.exists(), f"missing file: {p}"
        if f.endswith(".md"):
            assert p.read_text().strip(), f"empty file: {p}"

    manifest = json.loads((out / "manifest.json").read_text())
    assert "files" in manifest
    assert "warnings" in manifest
    assert "drafted_at" in manifest
    print(f"\n✓ End-to-end draft produced {len(expected)} files")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
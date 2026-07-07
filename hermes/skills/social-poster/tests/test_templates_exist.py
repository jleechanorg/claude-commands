"""Tests for templates + references — all 9 platform templates exist and have valid markdown."""
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_DIR / "templates"
REFERENCES_DIR = SKILL_DIR / "references"

REQUIRED_TEMPLATES = [
    "linkedin.md",
    "hackernews.md",
    "twitter.md",
    "reddit.md",
    "threads.md",
    "facebook.md",
    "instagram.md",
    "mastodon.md",
    "devto.md",
]

REQUIRED_REFERENCES = [
    "subreddit-rules.md",
    "platform-character-limits.md",
    "aside-recipes.md",
]


def test_all_required_templates_exist():
    for t in REQUIRED_TEMPLATES:
        p = TEMPLATES_DIR / t
        assert p.exists(), f"missing template: {p}"
        content = p.read_text().strip()
        assert content, f"empty template: {p}"
        assert content.startswith("#"), f"template {t} missing top-level header"


def test_all_required_references_exist():
    for r in REQUIRED_REFERENCES:
        p = REFERENCES_DIR / r
        assert p.exists(), f"missing reference: {p}"
        assert p.read_text().strip(), f"empty reference: {p}"


def test_subreddit_rules_mentions_required_subs():
    content = (REFERENCES_DIR / "subreddit-rules.md").read_text().lower()
    for sub in ("localllama", "rag", "openai"):
        assert sub in content, f"subreddit-rules.md missing {sub}"


def test_subreddit_rules_calls_out_banned():
    content = (REFERENCES_DIR / "subreddit-rules.md").read_text()
    for banned in ("r/AItools", "r/AutoGen", "r/LMStudio"):
        assert banned in content, f"subreddit-rules.md should call out {banned}"


def test_platform_limits_has_all_platforms():
    content = (REFERENCES_DIR / "platform-character-limits.md").read_text()
    for plat in ("LinkedIn", "Hacker News", "Twitter", "Reddit", "Threads", "Facebook", "Instagram", "Mastodon", "Dev.to"):
        assert plat in content, f"platform-character-limits.md missing {plat}"


def test_aside_recipes_has_compose_urls():
    content = (REFERENCES_DIR / "aside-recipes.md").read_text()
    assert "linkedin.com" in content
    assert "news.ycombinator.com/submit" in content
    assert "twitter.com/compose" in content
    assert "reddit.com/r/" in content


def test_templates_have_anti_patterns_section():
    for t in REQUIRED_TEMPLATES:
        content = (TEMPLATES_DIR / t).read_text()
        assert "Anti-patterns" in content or "anti-patterns" in content, \
            f"{t} missing anti-patterns section"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
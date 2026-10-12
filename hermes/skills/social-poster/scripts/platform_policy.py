"""Shared per-request destination selection; X threads are not Meta Threads."""
DEFAULT_PLATFORMS = ("reddit", "twitter")
SUPPORTED_PLATFORMS = frozenset((*DEFAULT_PLATFORMS, "linkedin", "linkedin_short",
    "hackernews", "threads", "facebook", "instagram", "mastodon", "devto"))


def parse_platforms(value=None):
    if value is None:
        return list(DEFAULT_PLATFORMS)
    names = [p.strip().lower() for p in value.split(",") if p.strip()]
    names = ["twitter" if p == "x" else p for p in names]
    if not names or any(p not in SUPPORTED_PLATFORMS and not p.startswith("reddit_") for p in names):
        raise ValueError("Select supported platforms explicitly; empty allowlists are invalid")
    return list(dict.fromkeys(names))


def selected(key, allow):
    key = key.lower()
    return key in allow or (key.startswith("reddit_") and "reddit" in allow)

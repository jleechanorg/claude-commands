"""Trigger eval: feed user-typed phrases to the resolver and assert
this skill is selected. Tests the routing half of the skill contract.

The skill triggers on phrases like:
  - "slack reply went to wrong thread"
  - "use slack mcp" / "use slack mcp better"
  - "/learn" + a Slack MCP behavior
  - "thread routing" / "thread_ts"
  - "self-rooted" / "self threaded"
  - "verify slack post routing"

The resolver is a simple keyword/regex matcher. The point of this test
is to catch drift — if the SKILL.md frontmatter stops mentioning the
trigger phrase, the test fails and we know to fix the frontmatter.

Run: python3 -m unittest tests.test_trigger_eval -v
"""
import os
import re
import sys
import unittest

SKILL_PATH = os.path.join(os.path.dirname(__file__), "..", "SKILL.md")


def _read_skill() -> str:
    with open(SKILL_PATH) as f:
        return f.read()


def _frontmatter_and_body(text: str) -> tuple:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        return text[: end + 4], text[end + 4 :]
    return "", text


def _skill_intent_matches(phrase: str, skill_text: str) -> bool:
    """Lightweight routing test: does the skill's frontmatter/triggers cover
    this user phrase? Mirrors what a human-audited RESOLVER would do."""
    p = phrase.lower()
    body_lower = skill_text.lower()
    # Tokens that must appear in the skill text for the phrase to be considered
    # "covered" by this skill
    if "wrong thread" in p or "right thread" in p or "self-root" in p or "self thread" in p:
        return "self-root" in body_lower or "self thread" in body_lower or "thread_ts" in body_lower
    if "use slack mcp" in p or "slack mcp" in p:
        return "slack" in body_lower and "mcp" in body_lower and ("post" in body_lower or "thread" in body_lower)
    if "thread routing" in p or "thread_ts" in p:
        return "thread_ts" in body_lower and "routing" in body_lower
    if "learn" in p and "slack" in p:
        return "slack" in body_lower and ("mcp" in body_lower or "post" in body_lower)
    if "verify slack" in p or "check slack" in p:
        return "conversations_replies" in body_lower or "conversations_add_message" in body_lower
    if "conversations_add_message" in p or "send_message" in p:
        return "conversations_add_message" in body_lower
    return False


class TestSkillTriggersArePresent(unittest.TestCase):
    def setUp(self):
        self.text = _read_skill()

    def test_frontmatter_has_name_and_description(self):
        fm, _ = _frontmatter_and_body(self.text)
        self.assertIn("name: slack-thread-routing-investigation", fm)
        self.assertIn("description:", fm)
        # Description must mention at least one user trigger phrase
        self.assertTrue(re.search(r"reply.*wrong|wrong.*thread|thread.*routing|self.*thread", fm, re.I),
                        "frontmatter description must include user trigger phrases")

    def test_user_phrase_wrong_thread_is_covered(self):
        self.assertTrue(_skill_intent_matches("reply went to wrong thread", self.text))

    def test_user_phrase_use_slack_mcp_is_covered(self):
        self.assertTrue(_skill_intent_matches("use slack mcp better", self.text))

    def test_user_phrase_learn_about_slack_mcp_is_covered(self):
        self.assertTrue(_skill_intent_matches("run /learn on this slack mcp issue", self.text))

    def test_user_phrase_thread_routing_is_covered(self):
        self.assertTrue(_skill_intent_matches("thread_ts routing broken", self.text))

    def test_user_phrase_self_rooted_is_covered(self):
        self.assertTrue(_skill_intent_matches("bot reply was self-rooted", self.text))

    def test_user_phrase_verify_slack_post_is_covered(self):
        self.assertTrue(_skill_intent_matches("verify slack post routing", self.text))

    def test_user_phrase_conversations_add_message_is_covered(self):
        self.assertTrue(_skill_intent_matches("conversations_add_message not surfaced", self.text))


class TestSkillMentionsDurableContentType(unittest.TestCase):
    """The /learn lesson: text/plain content_type prevents Block Kit
    fragmentation of emoji shortcodes. Skill must mention this."""

    def setUp(self):
        self.text = _read_skill()

    def test_mentions_content_type_text_plain(self):
        self.assertIn("text/plain", self.text)
        self.assertIn("content_type", self.text)

    def test_mentions_block_kit_fragmentation(self):
        # The formatting problem from the 2026-06-09 thread
        self.assertIn("Block Kit", self.text)
        self.assertIn("fragment", self.text.lower())

    def test_mentions_http_direct_escape_hatch(self):
        # When the runtime doesn't surface the MCP tool
        self.assertIn("HTTP", self.text)
        self.assertIn("escape", self.text.lower() or "fallback" in self.text.lower())


class TestSkillMentionsAllThreePostPaths(unittest.TestCase):
    def setUp(self):
        self.text = _read_skill()

    def test_mentions_mcp_tool(self):
        self.assertIn("conversations_add_message", self.text)

    def test_mentions_http_direct(self):
        self.assertIn("8006", self.text)
        self.assertIn("session", self.text.lower())

    def test_mentions_chat_postMessage_fallback(self):
        self.assertIn("chat.postMessage", self.text)


class TestSkillResolverEntryExists(unittest.TestCase):
    """The skill must be in RESOLVER.md for the user's /learn phrase to route."""

    def test_resolver_entry_for_this_skill(self):
        resolver_path = os.path.expanduser("~/.hermes_prod/skills/RESOLVER.md")
        self.assertTrue(os.path.exists(resolver_path),
                        f"RESOLVER.md not found at {resolver_path}")
        with open(resolver_path) as f:
            content = f.read()
        self.assertIn("slack-thread-routing-investigation", content,
                      "RESOLVER.md must list slack-thread-routing-investigation "
                      "so /learn and trigger phrases route here")


if __name__ == "__main__":
    unittest.main()

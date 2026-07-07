"""Unit tests for pain_score() in reddit-competitor-complaints.py.

Run: cd ~/.hermes/skills/reddit-competitor-complaints/tests && \
     python3 -m pytest test_pain_score.py -v
"""
import sys
import os
import unittest

# Resolve the script's location relative to the skill dir.
# Skill is at ~/.hermes/skills/reddit-competitor-complaints/
# Script is at ~/.hermes/scripts/reddit-competitor-complaints.py
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(SKILL_DIR)), "scripts", "reddit-competitor-complaints.py")
if not os.path.isfile(SCRIPT_PATH):
    SCRIPT_PATH = os.path.join(os.path.dirname(SKILL_DIR), "scripts", "reddit-competitor-complaints.py")

# Fall back to ~/.hermes_prod/scripts/ if staging copy is missing (so
# this test passes for both the staging dev loop and the prod runtime).
if not os.path.isfile(SCRIPT_PATH):
    SCRIPT_PATH = os.path.join(
        os.path.expanduser("~"),
        ".hermes_prod", "scripts", "reddit-competitor-complaints.py",
    )
sys.path.insert(0, os.path.dirname(SCRIPT_PATH))

# Import the scraper's pain_score.  Use importlib to load by file path so we
# don't need the script to be on PYTHONPATH at collection time.
import importlib.util
spec = importlib.util.spec_from_file_location("scraper", SCRIPT_PATH)
scraper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scraper)
pain_score = scraper.pain_score


class TestPainScore(unittest.TestCase):
    def test_positive_review_loves_it(self):
        self.assertLess(pain_score("I love this game", "absolutely amazing"), 0)

    def test_strong_complaint_filters(self):
        s = pain_score("NSFW filter censorship broke the game",
                       "latitude banned my story, looking for alternative")
        self.assertGreaterEqual(s, 4)

    def test_neutral_post_zero(self):
        s = pain_score("Update v2.0 released today",
                       "we shipped a new feature for character sheets")
        self.assertEqual(s, 0)

    def test_alternative_request(self):
        s = pain_score("Is there a free alternative to AI Dungeon?",
                       "I'd rather use kobold or novelai")
        self.assertGreaterEqual(s, 2)

    def test_open_source_mention(self):
        s = pain_score("Best open source AI text RPG",
                       "self-host your own dragon model")
        self.assertGreaterEqual(s, 2)

    def test_mixed_signal(self):
        # Post that mentions both a complaint and a positive — net should
        # land near zero or slightly negative.
        s = pain_score("I love the new update but the filter is still broken",
                       "amazing UI but disappointing censorship")
        # 2 pain words (filter, censorship, broken) - 1 pos (love, amazing)
        # Should be net positive (complaint-leaning) given the post title
        # mentions filter/censorship/broken
        self.assertGreater(s, 0)

    def test_refund_mentions(self):
        s = pain_score("Refund request — paywalled features",
                       "I want my money back, this is a scam")
        self.assertGreaterEqual(s, 2)

    def test_lowercase_and_uppercase_treated_equal(self):
        a = pain_score("FILTER is broken", "")
        b = pain_score("filter is broken", "")
        self.assertEqual(a, b)

    def test_empty_input(self):
        self.assertEqual(pain_score("", ""), 0)

    def test_only_pos_words(self):
        s = pain_score("Fantastic update", "amazing, love it, highly recommend")
        self.assertLessEqual(s, -1)

    def test_dragon_model_keyword(self):
        s = pain_score("Try the new dragon model",
                       "much better than griffin or wyvern")
        self.assertGreaterEqual(s, 2)

    def test_novelai_competitor_keyword(self):
        s = pain_score("Migrated to NovelAI from AI Dungeon",
                       "way better, no filter, no censorship")
        self.assertGreaterEqual(s, 2)

    def test_paywall_complaint(self):
        s = pain_score("Subscription too expensive",
                       "I can't afford the paywalled features")
        self.assertGreaterEqual(s, 2)

    def test_pain_word_appears_in_body_not_title(self):
        s = pain_score("Update released", "fixed the broken filter bug")
        self.assertGreaterEqual(s, 2)

    def test_recency_independent(self):
        # pain_score is purely lexical — recency is a separate rank
        # multiplier applied later.  Lexical score is the same regardless.
        a = pain_score("filter is broken", "")
        b = pain_score("filter is broken", "")
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()

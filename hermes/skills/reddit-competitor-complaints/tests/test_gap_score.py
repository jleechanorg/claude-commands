"""Unit tests for gap_score() in reddit-competitor-complaints.py.

Run: cd ~/.hermes/skills/reddit-competitor-complaints/tests && \
     python3 -m pytest test_gap_score.py -v
"""
import sys
import importlib.util
import pytest

# Load the scraper as a module (it's at ~/.hermes/scripts/, not a package)
SCRIPER_PATH = "$HOME/.hermes/scripts/reddit-competitor-complaints.py"
spec = importlib.util.spec_from_file_location("rcc", SCRIPER_PATH)
rcc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rcc)
gap_score = rcc.gap_score


def test_user_wish_phrase_is_strong_gap():
    # "I wish" + "feature" + "would be nice" = 3+3+1+1 = 8
    score = gap_score("I wish there was a feature for custom memory", "It would be nice to have...")
    assert score >= 6, f"expected ≥6, got {score}"


def test_how_do_i_question_is_gap():
    # "how do i" heavy (3) + "feature" light (1) + "custom" light (1) + "scenario" light (1) = 6
    score = gap_score("How do I make a custom scenario", "I'm looking for a feature...")
    assert score >= 4, f"expected ≥4, got {score}"


def test_positive_love_phrase_filters_out():
    # "love" and "amazing" should deduct to make this a negative gap score
    score = gap_score("I love this feature", "It's amazing and addicting")
    assert score < 0, f"expected <0, got {score}"


def test_patch_notes_downweighted():
    plain = gap_score(
        "Custom AI Instruction sets in Scenario Editor",  # NOT a patch-notes title
        "feature feature feature improve improvement custom settings scenario control update"
    )
    patch = gap_score(
        "[Prod] June 6th, 2026 Patch Notes",  # IS a patch-notes title
        "feature feature feature improve improvement custom settings scenario control update"
    )
    # Same body, but patch-notes title should score ~50% lower
    assert patch < plain, f"patch ({patch}) should be < plain ({plain})"
    assert 0.4 <= patch / plain <= 0.6, f"patch should be ~50% of plain, got {patch/plain}"


def test_neutral_needs_minimum_signal():
    # Empty title and body
    assert gap_score("", "") == 0
    # A title with no gap language
    assert gap_score("Question about the new feature", "") <= 1


def test_heavy_phrase_dominates():
    # One heavy phrase (3 pts) should clearly beat one light phrase (1 pt)
    user_wish = gap_score("I wish the AI would remember my character's name", "I want this feature")
    feature_dump = gap_score("Memory feature improvement update", "Custom feature for scenarios")
    # user_wish has: wish (3) + want (3) + remember (1) + character (1) + feature (1) + want (already counted) = 9
    # feature_dump has: memory (1) + feature (1) + improvement (1) + update (1) + custom (1) + feature (already counted) + scenarios (1) = 6
    # Plus 1 "i want" in user_wish's body (3) — that pushes it higher
    assert user_wish > feature_dump, f"user_wish ({user_wish}) should beat feature_dump ({feature_dump})"
    assert user_wish - feature_dump >= 2, f"user_wish should dominate by ≥2, got {user_wish - feature_dump}"


def test_release_notes_also_downweighted():
    plain = gap_score("Custom feature for scenario editing", "feature improve add support")
    release = gap_score("Release notes for v2.7.16", "feature improve add support")
    assert release < plain, f"release ({release}) should be < plain ({plain})"


def test_changelog_marker_downweighted():
    plain = gap_score("Memory improvements", "feature improve")
    cl = gap_score("Changelog for May 26th", "feature improve")
    assert cl < plain, f"changelog ({cl}) should be < plain ({plain})"

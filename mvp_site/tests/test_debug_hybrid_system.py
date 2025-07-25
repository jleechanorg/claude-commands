"""
Test hybrid debug content system for backward compatibility.
"""

import os
import sys

# Add parent directory to path for mvp_site imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))

from debug_hybrid_system import (
    contains_debug_tags,
    get_narrative_for_display,
    process_story_entry_for_display,
    process_story_for_display,
    strip_debug_content,
    strip_state_updates_only,
)


class TestDebugTagDetection:
    """Test detection of legacy debug tags."""

    def test_detects_debug_start_tags(self):
        text = "Story text [DEBUG_START]debug content[DEBUG_END] more story"
        assert contains_debug_tags(text) is True

    def test_detects_state_updates_tags(self):
        text = "Story text [STATE_UPDATES_PROPOSED]state data[END_STATE_UPDATES_PROPOSED] more"
        assert contains_debug_tags(text) is True

    def test_detects_debug_roll_tags(self):
        text = "You attack [DEBUG_ROLL_START]1d20+5 = 18[DEBUG_ROLL_END] and hit!"
        assert contains_debug_tags(text) is True

    def test_no_tags_returns_false(self):
        text = "This is a clean story with no debug content at all."
        assert contains_debug_tags(text) is False

    def test_empty_text_returns_false(self):
        assert contains_debug_tags("") is False
        assert contains_debug_tags(None) is False


class TestDebugContentStripping:
    """Test stripping of debug content."""

    def test_strip_all_debug_content(self):
        text = (
            "You enter the cave. [DEBUG_START]DM notes here[DEBUG_END] "
            "You attack! [DEBUG_ROLL_START]1d20 = 15[DEBUG_ROLL_END] "
            "[STATE_UPDATES_PROPOSED]hp: 45[END_STATE_UPDATES_PROPOSED]"
        )
        result = strip_debug_content(text)
        assert result == "You enter the cave.  You attack!  "
        assert "[DEBUG_START]" not in result
        assert "DM notes" not in result

    def test_strip_only_state_updates(self):
        text = (
            "You enter the cave. [DEBUG_START]DM notes here[DEBUG_END] "
            "[STATE_UPDATES_PROPOSED]hp: 45[END_STATE_UPDATES_PROPOSED]"
        )
        result = strip_state_updates_only(text)
        assert result == "You enter the cave. [DEBUG_START]DM notes here[DEBUG_END] "
        assert "[DEBUG_START]" in result  # Debug content preserved
        assert "[STATE_UPDATES_PROPOSED]" not in result  # State updates removed

    def test_strip_malformed_state_updates(self):
        text = "Story TATE_UPDATES_PROPOSED]bad data[END_STATE_UPDATES_PROPOSED] more"
        result = strip_debug_content(text)
        assert "TATE_UPDATES_PROPOSED" not in result
        assert result == "Story  more"


class TestStoryEntryProcessing:
    """Test processing of individual story entries."""

    def test_process_user_entry_unchanged(self):
        entry = {
            "actor": "user",
            "text": "I attack the [DEBUG_START]goblin[DEBUG_END]!",
            "timestamp": "2024-01-01",
        }
        result = process_story_entry_for_display(entry, debug_mode=False)
        # User entries should not be processed
        assert result["text"] == entry["text"]

    def test_process_ai_entry_old_campaign_no_debug(self):
        entry = {
            "actor": "gemini",
            "text": "You strike! [DEBUG_START]Roll: 18[DEBUG_END] Hit!",
            "timestamp": "2024-01-01",
        }
        result = process_story_entry_for_display(entry, debug_mode=False)
        assert result["text"] == "You strike!  Hit!"

    def test_process_ai_entry_old_campaign_with_debug(self):
        entry = {
            "actor": "gemini",
            "text": "You strike! [DEBUG_START]Roll: 18[DEBUG_END] Hit!",
            "timestamp": "2024-01-01",
        }
        result = process_story_entry_for_display(entry, debug_mode=True)
        assert "[DEBUG_START]Roll: 18[DEBUG_END]" in result["text"]

    def test_process_ai_entry_new_campaign(self):
        # New campaigns have clean text
        entry = {
            "actor": "gemini",
            "text": "You strike the goblin with your sword!",
            "timestamp": "2024-01-01",
        }
        result = process_story_entry_for_display(entry, debug_mode=False)
        assert result["text"] == entry["text"]  # Unchanged


class TestStoryListProcessing:
    """Test processing of full story lists."""

    def test_process_mixed_story(self):
        story = [
            {"actor": "user", "text": "I attack!"},
            {
                "actor": "gemini",
                "text": "Hit! [DEBUG_START]dmg: 8[DEBUG_END] Goblin hurt!",
            },
            {"actor": "user", "text": "I attack again!"},
            {"actor": "gemini", "text": "You miss!"},  # New style, no tags
        ]

        result = process_story_for_display(story, debug_mode=False)

        assert result[0]["text"] == "I attack!"  # User unchanged
        assert result[1]["text"] == "Hit!  Goblin hurt!"  # AI stripped
        assert result[2]["text"] == "I attack again!"  # User unchanged
        assert result[3]["text"] == "You miss!"  # AI new style unchanged


class TestNarrativeDisplay:
    """Test the main narrative display function."""

    def test_old_campaign_no_debug_mode(self):
        text = "Story [DEBUG_START]notes[DEBUG_END] continues"
        result = get_narrative_for_display(text, debug_mode=False)
        assert result == "Story  continues"

    def test_old_campaign_debug_mode(self):
        text = (
            "Story [DEBUG_START]notes[DEBUG_END] "
            "[STATE_UPDATES_PROPOSED]data[END_STATE_UPDATES_PROPOSED]"
        )
        result = get_narrative_for_display(text, debug_mode=True)
        assert "[DEBUG_START]notes[DEBUG_END]" in result
        assert "[STATE_UPDATES_PROPOSED]" not in result

    def test_new_campaign_unchanged(self):
        text = "This is a clean narrative with no debug tags."
        result = get_narrative_for_display(text, debug_mode=False)
        assert result == text
        result = get_narrative_for_display(text, debug_mode=True)
        assert result == text

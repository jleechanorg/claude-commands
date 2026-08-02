#!/usr/bin/env python3
"""Tests for wa-campaign-premise-find skill."""
import os, sys, pytest

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))

from keyword_matrix import KEYWORD_MATRIX, build_search_regex, classify_god_mode

ISEKI_GOD_MODE = (
    "Setting: I wanna play a character who's strong or special like one of those "
    "isekai reborn anime characters but not too OP. Can make me 16 and a level 6"
)
# Then scene 3 player input (from worked example):
ISEKI_PLAYER = (
    "Let's make me a reincarnation of a great demon lord. However make me grey rather "
    "black and white evil morally. Let's assume I killed half the worlds population but "
    "I had a good reason and I was level 25 but a band of heroes finally defeated me but "
    "I only lost because my child's life was in danger during battle."
)

LUNA_GOD_MODE = (
    "Character: Luna | Description: w_user ... Shadowheart (Resurrected) The air inside "
    "the ruined Selûnite temple ... Luna kneels on the cold, uneven flagstones"
)

NOCTURNA_GOD_MODE = (
    "Character: Nocturna | Setting: After the events of bg3. I am a level 5 int based "
    "cleric make me a special class. I am a 16 year old female prodigy and give me an "
    "interesting backstory and extra attack"
)


class TestKeywordMatrix:
    def test_all_tropes_have_patterns(self):
        assert len(KEYWORD_MATRIX) >= 5
        for name, pat in KEYWORD_MATRIX.items():
            assert pat.pattern, f"{name} has empty pattern"

    def test_demon_lord_matches_demon_king(self):
        assert KEYWORD_MATRIX["demon_lord"].search("Once a Demon King who nearly scoured the world")

    def test_reincarnation_matches_isekai_and_reborn(self):
        assert KEYWORD_MATRIX["reincarnation"].search("I am isekai reborn anime character")
        assert KEYWORD_MATRIX["reincarnation"].search("reincarnation of a great demon lord")
        assert KEYWORD_MATRIX["reincarnation"].search("past life memories")

    def test_overpowered_matches_op_and_god_tier(self):
        assert KEYWORD_MATRIX["overpowered"].search("Make me OP")
        assert KEYWORD_MATRIX["overpowered"].search("god-tier campaign")
        assert KEYWORD_MATRIX["overpowered"].search("start at level 25")

    def test_resurrected_matches_brought_back_and_raised(self):
        assert KEYWORD_MATRIX["resurrected"].search("I was resurrected")
        assert KEYWORD_MATRIX["resurrected"].search("raised from the dead")
        assert KEYWORD_MATRIX["resurrected"].search("back from the dead")

    def test_female_pc_matches_make_me_female(self):
        assert KEYWORD_MATRIX["female_pc"].search("make me female and a level 6")
        assert KEYWORD_MATRIX["female_pc"].search("let's make me a 16yo female prodigy")
        assert KEYWORD_MATRIX["female_pc"].search("reincarnated as a succubus")

    def test_daughter_past_matches(self):
        assert KEYWORD_MATRIX["daughter_past"].search("my daughter from a past life")
        assert KEYWORD_MATRIX["daughter_past"].search("child from past life survives")


class TestBuildSearchRegex:
    def test_empty_tropes_returns_empty(self):
        assert build_search_regex([]) == ""

    def test_single_trope(self):
        assert "demon" in build_search_regex(["demon_lord"])

    def test_multiple_tropes_uses_alternation(self):
        regex = build_search_regex(["demon_lord", "reincarnation", "overpowered"])
        # Should be a single string with | separators
        assert regex.count("|") >= 2


class TestClassifyGodMode:
    def test_iseki_matches_reincarnation_and_demon_lord(self):
        combined = ISEKI_GOD_MODE + " " + ISEKI_PLAYER
        result = classify_god_mode(combined)
        assert result["demon_lord"] is True
        assert result["reincarnation"] is True
        assert result["overpowered"] is True
        assert result["daughter_past"] is True

    def test_luna_resurrected_npc_not_pc(self):
        """Luna post bg3 has 'Shadowheart (Resurrected)' as NPC — should still
        match 'resurrected' keyword but is NOT a female-resurrected-PC scenario.
        This test verifies the keyword matching works; the SKILL.md pitfall #3
        documents the disambiguation."""
        result = classify_god_mode(LUNA_GOD_MODE)
        assert result["resurrected"] is True  # Shadowheart NPC
        # And we need the human (or downstream logic) to check that "I" / Luna
        # is NOT explicitly the resurrected one — this is the pitfall, not the regex.

    def test_nocturna_female_pc_op(self):
        result = classify_god_mode(NOCTURNA_GOD_MODE)
        assert result["female_pc"] is True
        assert result["overpowered"] is True  # "special class", "level 5"

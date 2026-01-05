"""Tests for equipment_display module.

Tests the equipment display extraction, categorization, and formatting functions.
"""

import unittest
from unittest.mock import MagicMock

from mvp_site.equipment_display import (
    _build_equipment_summary,
    _categorize_equipment_slot,
    _classify_backpack_item,
    _count_equipment_mentions,
    _filter_equipment_for_summary,
    _get_backpack_importance,
    _limit_backpack_for_display,
    classify_equipment_query,
    ensure_equipment_summary_in_narrative,
    extract_equipment_display,
    is_equipment_query,
)


class TestIsEquipmentQuery(unittest.TestCase):
    """Tests for is_equipment_query function."""

    def test_equipment_keyword(self):
        """Should detect 'equipment' keyword."""
        self.assertTrue(is_equipment_query("show me my equipment"))

    def test_inventory_keyword(self):
        """Should detect 'inventory' keyword."""
        self.assertTrue(is_equipment_query("what's in my inventory"))

    def test_gear_keyword(self):
        """Should detect 'gear' keyword."""
        self.assertTrue(is_equipment_query("check my gear"))

    def test_backpack_keyword(self):
        """Should detect 'backpack' keyword."""
        self.assertTrue(is_equipment_query("what's in my backpack"))

    def test_weapons_keyword(self):
        """Should detect 'weapons' keyword."""
        self.assertTrue(is_equipment_query("list my weapons"))

    def test_what_do_i_have(self):
        """Should detect 'what do i have' phrase."""
        self.assertTrue(is_equipment_query("what do i have?"))

    def test_non_equipment_query(self):
        """Should return False for non-equipment queries."""
        self.assertFalse(is_equipment_query("attack the goblin"))

    def test_case_insensitive(self):
        """Should be case insensitive."""
        self.assertTrue(is_equipment_query("SHOW ME MY EQUIPMENT"))


class TestClassifyEquipmentQuery(unittest.TestCase):
    """Tests for classify_equipment_query function."""

    def test_backpack_query(self):
        """Should classify backpack queries."""
        self.assertEqual(classify_equipment_query("what's in my backpack"), "backpack")

    def test_inventory_query(self):
        """Should classify inventory as backpack."""
        self.assertEqual(classify_equipment_query("show my inventory"), "backpack")

    def test_weapons_query(self):
        """Should classify weapons queries."""
        self.assertEqual(classify_equipment_query("list my weapons"), "weapons")

    def test_equipped_query(self):
        """Should classify equipped queries."""
        self.assertEqual(classify_equipment_query("what am I wearing"), "equipped")

    def test_armor_query(self):
        """Should classify armor as equipped."""
        self.assertEqual(classify_equipment_query("show my armor"), "equipped")

    def test_all_query(self):
        """Should default to 'all' for general equipment queries."""
        self.assertEqual(classify_equipment_query("show my equipment"), "all")


class TestCategorizeEquipmentSlot(unittest.TestCase):
    """Tests for _categorize_equipment_slot function."""

    def test_head_slots(self):
        """Should categorize head slots correctly."""
        for slot in ["head", "helmet", "helm", "crown"]:
            self.assertEqual(_categorize_equipment_slot(slot), "Head")

    def test_armor_slots(self):
        """Should categorize armor slots correctly."""
        for slot in ["armor", "chest", "body", "torso"]:
            self.assertEqual(_categorize_equipment_slot(slot), "Armor")

    def test_weapon_slots(self):
        """Should categorize weapon slots correctly."""
        for slot in ["weapon", "main hand"]:
            self.assertEqual(_categorize_equipment_slot(slot), "Weapons")

    def test_offhand_slots(self):
        """Should categorize off-hand slots separately (shields, focuses)."""
        for slot in ["off hand", "off_hand", "offhand"]:
            self.assertEqual(_categorize_equipment_slot(slot), "Off-Hand")

    def test_backpack_slot(self):
        """Should categorize backpack slot."""
        self.assertEqual(_categorize_equipment_slot("backpack"), "Backpack")

    def test_ring_slots(self):
        """Should categorize ring slots."""
        for slot in ["ring", "ring1", "ring 1"]:
            self.assertEqual(_categorize_equipment_slot(slot), "Rings")

    def test_unknown_slot(self):
        """Should return 'Other' for unknown slots."""
        self.assertEqual(_categorize_equipment_slot("unknown"), "Other")


class TestClassifyBackpackItem(unittest.TestCase):
    """Tests for _classify_backpack_item function."""

    def test_document_items(self):
        """Should classify documents."""
        self.assertEqual(_classify_backpack_item("Ancient Letter", ""), "Documents")
        self.assertEqual(
            _classify_backpack_item("Cipher Key", "decodes messages"), "Documents"
        )

    def test_key_items(self):
        """Should classify keys."""
        self.assertEqual(_classify_backpack_item("Silver Key", ""), "Keys")
        self.assertEqual(_classify_backpack_item("Lockpick Set", ""), "Keys")

    def test_currency_items(self):
        """Should classify currency."""
        self.assertEqual(_classify_backpack_item("Gold Coins", "50 gp"), "Currency")

    def test_potion_items(self):
        """Should classify potions as resources."""
        self.assertEqual(
            _classify_backpack_item("Healing Potion", "2d4+2"), "Resources"
        )

    def test_weapon_items(self):
        """Should classify weapons in backpack."""
        self.assertEqual(_classify_backpack_item("Dagger", "1d4 piercing"), "Weapons")

    def test_mundane_staff_items(self):
        """Plain staff without magical cues should be treated as a weapon."""
        self.assertEqual(
            _classify_backpack_item("Quarterstaff", "1d6 bludgeoning"), "Weapons"
        )

    def test_magical_items(self):
        """Should classify magical items."""
        self.assertEqual(
            _classify_backpack_item("Wand of Magic", "+1 spell DC"), "Magical Items"
        )

    def test_dice_modifiers_do_not_trigger_magic(self):
        """Damage modifiers like 1d6+2 should not be treated as magical bonuses."""
        self.assertEqual(
            _classify_backpack_item("Shortbow", "1d6+2 piercing"), "Weapons"
        )

    def test_misc_items(self):
        """Should default to Miscellaneous."""
        self.assertEqual(_classify_backpack_item("Rope", "50 ft hemp"), "Miscellaneous")


class TestGetBackpackImportance(unittest.TestCase):
    """Tests for _get_backpack_importance function."""

    def test_artifact_highest_priority(self):
        """Artifacts should have highest priority."""
        self.assertEqual(_get_backpack_importance("Ancient Artifact", ""), 100)

    def test_legendary_highest_priority(self):
        """Legendary items should have highest priority."""
        self.assertEqual(_get_backpack_importance("Legendary Sword", ""), 100)

    def test_plus_3_highest_priority(self):
        """Items with +3 should have highest priority."""
        self.assertEqual(_get_backpack_importance("Staff", "+3 to hit"), 100)

    def test_plus_2_high_priority(self):
        """Items with +2 should have high priority."""
        self.assertEqual(_get_backpack_importance("Shield", "+2 AC"), 80)

    def test_potion_medium_priority(self):
        """Potions should have medium priority."""
        self.assertEqual(_get_backpack_importance("Potion of Healing", "2d4+2"), 50)

    def test_dice_notation_not_matched(self):
        """Dice notation like 2d4+2 should NOT match +2 magic item."""
        # Potion gets 50 from "potion" keyword, not 80 from "+2"
        importance = _get_backpack_importance("Potion of Healing", "2d4+2")
        self.assertEqual(importance, 50)

    def test_tools_lower_priority(self):
        """Tools should have lower priority than magic items."""
        self.assertEqual(_get_backpack_importance("Thieves' Tools", ""), 40)

    def test_currency_low_priority(self):
        """Currency should have low priority."""
        self.assertEqual(_get_backpack_importance("Gold Coins", "100 gp"), 20)

    def test_misc_lowest_priority(self):
        """Miscellaneous items should have lowest priority."""
        self.assertEqual(_get_backpack_importance("Rope", "50 ft"), 10)


class TestLimitBackpackForDisplay(unittest.TestCase):
    """Tests for _limit_backpack_for_display function."""

    def test_limits_to_max_items(self):
        """Should limit to specified max items."""
        items = [
            {"slot": "Backpack", "name": "Item 1", "stats": ""},
            {"slot": "Backpack", "name": "Item 2", "stats": ""},
            {"slot": "Backpack", "name": "Item 3", "stats": ""},
            {"slot": "Backpack", "name": "Item 4", "stats": ""},
            {"slot": "Backpack", "name": "Item 5", "stats": ""},
        ]
        result = _limit_backpack_for_display(items, max_items=3)
        self.assertEqual(len(result), 3)

    def test_prioritizes_important_items(self):
        """Should keep most important items."""
        items = [
            {"slot": "Backpack", "name": "Rope", "stats": "50 ft"},  # importance=10
            {
                "slot": "Backpack",
                "name": "Ancient Artifact",
                "stats": "",
            },  # importance=100
            {
                "slot": "Backpack",
                "name": "Gold Coins",
                "stats": "10 gp",
            },  # importance=20
            {"slot": "Backpack", "name": "Potion", "stats": "healing"},  # importance=50
        ]
        result = _limit_backpack_for_display(items, max_items=2)
        names = [item["name"] for item in result]
        self.assertIn("Ancient Artifact", names)
        self.assertIn("Potion", names)
        self.assertNotIn("Rope", names)

    def test_returns_all_if_fewer_than_limit(self):
        """Should return all items if fewer than limit."""
        items = [
            {"slot": "Backpack", "name": "Item 1", "stats": ""},
            {"slot": "Backpack", "name": "Item 2", "stats": ""},
        ]
        result = _limit_backpack_for_display(items, max_items=5)
        self.assertEqual(len(result), 2)


class TestBuildEquipmentSummary(unittest.TestCase):
    """Tests for _build_equipment_summary function."""

    def test_empty_items(self):
        """Should return empty string for no items."""
        self.assertEqual(_build_equipment_summary([], "Test"), "")

    def test_includes_label(self):
        """Should include label in output."""
        items = [{"slot": "Head", "name": "Helm", "stats": ""}]
        result = _build_equipment_summary(items, "Equipment")
        self.assertIn("Equipment", result)

    def test_groups_by_category(self):
        """Should group items by category."""
        items = [
            {"slot": "Head", "name": "Helm", "stats": ""},
            {"slot": "Armor", "name": "Chainmail", "stats": ""},
        ]
        result = _build_equipment_summary(items, "Equipment")
        self.assertIn("Head:", result)
        self.assertIn("Armor:", result)

    def test_includes_stats(self):
        """Should include stats in output."""
        items = [{"slot": "Head", "name": "Helm", "stats": "+2 AC"}]
        result = _build_equipment_summary(items, "Equipment")
        self.assertIn("+2 AC", result)


class TestFilterEquipmentForSummary(unittest.TestCase):
    """Tests for _filter_equipment_for_summary function."""

    def test_filter_backpack(self):
        """Should filter to backpack items only."""
        items = [
            {"slot": "Backpack", "name": "Potion", "stats": ""},
            {"slot": "Head", "name": "Helm", "stats": ""},
        ]
        result = _filter_equipment_for_summary(items, "backpack")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Potion")

    def test_filter_weapons(self):
        """Should filter to weapon items only."""
        items = [
            {"slot": "Weapon", "name": "Sword", "stats": ""},
            {"slot": "Main Hand", "name": "Staff", "stats": ""},
            {"slot": "Head", "name": "Helm", "stats": ""},
        ]
        result = _filter_equipment_for_summary(items, "weapons")
        self.assertEqual(len(result), 2)

    def test_filter_equipped(self):
        """Should filter to equipped items (excluding backpack and weapons)."""
        items = [
            {"slot": "Backpack", "name": "Potion", "stats": ""},
            {"slot": "Head", "name": "Helm", "stats": ""},
            {"slot": "Armor", "name": "Plate", "stats": ""},
        ]
        result = _filter_equipment_for_summary(items, "equipped")
        self.assertEqual(len(result), 2)
        names = [item["name"] for item in result]
        self.assertNotIn("Potion", names)

    def test_filter_all(self):
        """Should return all items for 'all' query."""
        items = [
            {"slot": "Backpack", "name": "Potion", "stats": ""},
            {"slot": "Head", "name": "Helm", "stats": ""},
        ]
        result = _filter_equipment_for_summary(items, "all")
        self.assertEqual(len(result), 2)

    def test_deduplicates_by_name_and_stats(self):
        """Should deduplicate items with same name and stats."""
        items = [
            {"slot": "Backpack", "name": "Potion", "stats": "healing"},
            {"slot": "Backpack", "name": "Potion", "stats": "healing"},
        ]
        result = _filter_equipment_for_summary(items, "all")
        self.assertEqual(len(result), 1)

    def test_preserves_same_name_with_different_stats(self):
        """Should keep items with same name but different stats."""
        items = [
            {"slot": "Backpack", "name": "Ring of Protection", "stats": "+1 AC"},
            {"slot": "Backpack", "name": "Ring of Protection", "stats": "+2 AC"},
        ]
        result = _filter_equipment_for_summary(items, "all")
        self.assertEqual(len(result), 2)

    def test_equipped_filter_excludes_weapons_but_keeps_shields(self):
        """Should exclude weapons but keep defensive off-hand gear like shields."""
        items = [
            {"slot": "Main Hand", "name": "Longsword", "stats": "1d8"},
            {"slot": "Off Hand", "name": "Shield", "stats": "+2 AC"},
            {"slot": "Armor", "name": "Chainmail", "stats": ""},
            {"slot": "Backpack", "name": "Rope", "stats": ""},
        ]
        result = _filter_equipment_for_summary(items, "equipped")
        slots = {item["slot"] for item in result}
        names = {item["name"] for item in result}

        self.assertNotIn("Main Hand", slots)
        self.assertIn("Off Hand", slots)
        self.assertIn("Armor", slots)
        self.assertNotIn("Backpack", slots)
        self.assertIn("Shield", names)


class TestCountEquipmentMentions(unittest.TestCase):
    """Tests for _count_equipment_mentions function."""

    def test_counts_mentions(self):
        """Should count item name mentions in text."""
        narrative = "You hold the Flame Sword and wear the Steel Helm."
        items = [
            {"name": "Flame Sword", "stats": ""},
            {"name": "Steel Helm", "stats": ""},
            {"name": "Magic Ring", "stats": ""},
        ]
        count = _count_equipment_mentions(narrative, items)
        self.assertEqual(count, 2)

    def test_case_insensitive(self):
        """Should be case insensitive."""
        narrative = "You grip the FLAME SWORD tightly."
        items = [{"name": "Flame Sword", "stats": ""}]
        count = _count_equipment_mentions(narrative, items)
        self.assertEqual(count, 1)

    def test_empty_narrative(self):
        """Should return 0 for empty narrative."""
        count = _count_equipment_mentions("", [{"name": "Sword", "stats": ""}])
        self.assertEqual(count, 0)

    def test_empty_items(self):
        """Should return 0 for empty items."""
        count = _count_equipment_mentions("Some text", [])
        self.assertEqual(count, 0)


class TestExtractEquipmentDisplay(unittest.TestCase):
    """Tests for extract_equipment_display function."""

    def test_extracts_equipped_items(self):
        """Should extract equipped items from game state."""
        game_state = MagicMock()
        game_state.item_registry = {}
        game_state.player_character_data = {
            "equipment": {
                "equipped": {
                    "head": "Iron Helm (AC +1)",
                    "armor": "Chainmail",
                },
                "backpack": [],
            }
        }

        result = extract_equipment_display(game_state)
        self.assertEqual(len(result), 2)
        names = [item["name"] for item in result]
        self.assertIn("Iron Helm", names)
        self.assertIn("Chainmail", names)

    def test_extracts_backpack_items(self):
        """Should extract backpack items (limited to 3)."""
        game_state = MagicMock()
        game_state.item_registry = {}
        game_state.player_character_data = {
            "equipment": {
                "equipped": {},
                "backpack": [
                    "Potion of Healing",
                    "Gold Coins",
                    "Rope",
                    "Torch",
                    "Rations",
                ],
            }
        }

        result = extract_equipment_display(game_state)
        # Should be limited to 3 backpack items
        self.assertEqual(len(result), 3)

    def test_uses_item_registry(self):
        """Should resolve item IDs from registry."""
        game_state = MagicMock()
        game_state.item_registry = {
            "helm_001": {"name": "Helm of Telepathy", "stats": "+2 INT"},
        }
        game_state.player_character_data = {
            "equipment": {
                "equipped": {"head": "helm_001"},
                "backpack": [],
            }
        }

        result = extract_equipment_display(game_state)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Helm of Telepathy")
        self.assertEqual(result[0]["stats"], "+2 INT")

    def test_handles_empty_equipment(self):
        """Should handle empty equipment gracefully."""
        game_state = MagicMock()
        game_state.item_registry = {}
        game_state.player_character_data = {"equipment": {}}

        result = extract_equipment_display(game_state)
        self.assertEqual(result, [])

    def test_includes_weapons_inventory(self):
        """Should include distinct weapons from inventory array alongside equipped weapons."""
        game_state = MagicMock()
        game_state.item_registry = {}
        game_state.player_character_data = {
            "equipment": {
                "equipped": {"main_hand": "Longsword"},
                "weapons": ["Longsword", "Dagger", "Shortbow"],
                "backpack": [],
            }
        }

        result = extract_equipment_display(game_state)

        weapon_names = [
            item["name"]
            for item in result
            if item["slot"] in {"Main Hand", "Off Hand", "Weapon"}
        ]
        self.assertEqual(len(weapon_names), 3)
        self.assertCountEqual(weapon_names, ["Longsword", "Dagger", "Shortbow"])

    def test_handles_dict_format_weapons(self):
        """Should preserve name and stats for dict-format weapons in inventory."""
        game_state = MagicMock()
        game_state.item_registry = {}
        game_state.player_character_data = {
            "equipment": {
                "equipped": {"main_hand": "Longsword"},
                "weapons": [
                    {"name": "Longbow", "damage": "1d8", "properties": "piercing"},
                    {"name": "Dagger", "damage": "1d4", "properties": "finesse"},
                ],
                "backpack": [],
            }
        }

        result = extract_equipment_display(game_state)

        longbow = next(
            (
                item
                for item in result
                if item["name"] == "Longbow" and item["slot"] == "Weapon"
            ),
            None,
        )
        dagger = next(
            (
                item
                for item in result
                if item["name"] == "Dagger" and item["slot"] == "Weapon"
            ),
            None,
        )

        self.assertIsNotNone(longbow)
        self.assertEqual(longbow["stats"], "1d8 piercing")
        self.assertIsNotNone(dagger)
        self.assertEqual(dagger["stats"], "1d4 finesse")

    def test_handles_dict_format_backpack_items(self):
        """Should preserve name and stats for dict-format backpack entries."""
        game_state = MagicMock()
        game_state.item_registry = {}
        game_state.player_character_data = {
            "equipment": {
                "equipped": {},
                "weapons": [],
                "backpack": [
                    {"name": "Healing Potion", "stats": "2d4+2"},
                    {"name": "Spellbook", "stats": "contains spells"},
                ],
            }
        }

        result = extract_equipment_display(game_state)

        potion = next(
            (item for item in result if item["name"] == "Healing Potion"), None
        )
        spellbook = next((item for item in result if item["name"] == "Spellbook"), None)

        self.assertIsNotNone(potion)
        self.assertEqual(potion["slot"], "Backpack")
        self.assertEqual(potion["stats"], "2d4+2")
        self.assertIsNotNone(spellbook)
        self.assertEqual(spellbook["slot"], "Backpack")
        self.assertEqual(spellbook["stats"], "contains spells")


class TestEnsureEquipmentSummaryInNarrative(unittest.TestCase):
    """Tests for ensure_equipment_summary_in_narrative function."""

    def test_appends_summary_when_few_mentions(self):
        """Should append summary when narrative has few item mentions."""
        narrative = "You look around the room."
        equipment = [
            {"slot": "Head", "name": "Helm", "stats": ""},
            {"slot": "Armor", "name": "Chainmail", "stats": ""},
        ]
        result = ensure_equipment_summary_in_narrative(
            narrative, equipment, user_input="show equipment", min_item_mentions=2
        )
        self.assertIn("Helm", result)
        self.assertIn("Chainmail", result)

    def test_skips_summary_when_items_mentioned(self):
        """Should skip summary when items are already mentioned."""
        narrative = "You wear your trusty Helm and Chainmail armor."
        equipment = [
            {"slot": "Head", "name": "Helm", "stats": ""},
            {"slot": "Armor", "name": "Chainmail", "stats": ""},
        ]
        result = ensure_equipment_summary_in_narrative(
            narrative, equipment, user_input="show equipment", min_item_mentions=2
        )
        # Should return original narrative without adding summary block
        self.assertEqual(result, narrative)

    def test_empty_equipment(self):
        """Should return narrative unchanged for empty equipment."""
        narrative = "You explore the dungeon."
        result = ensure_equipment_summary_in_narrative(
            narrative, [], user_input="show equipment"
        )
        self.assertEqual(result, narrative)


if __name__ == "__main__":
    unittest.main()

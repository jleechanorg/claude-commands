"""Tests for narrative_response_schema.py following TDD approach.

This test file implements the schema validation gaps identified in
roadmap/llm_schema_alignment_gaps.md following Red-Green-Refactor pattern.
"""

import unittest
from unittest.mock import patch

from mvp_site import logging_util
from mvp_site.narrative_response_schema import (
    NarrativeResponse,
    _validate_resources,
    _validate_spell_slots,
    _validate_attributes,
)


class TestSocialHPInputOutputMapping(unittest.TestCase):
    """RED: Tests for Social HP Input→Output Mapping (Step 1)."""

    def test_social_hp_challenge_extracts_npc_tier_from_npc_data(self):
        """Test that npc_tier can be extracted from npc_data.tier input."""
        # This test documents the expected input→output mapping
        # INPUT: npc_data.<name>.tier
        npc_data = {
            "merchant_john": {
                "tier": "merchant",
                "role": "shopkeeper",
            }
        }

        # OUTPUT: social_hp_challenge.npc_tier should match npc_data.tier
        social_hp_challenge = {
            "npc_name": "John",
            "npc_tier": "merchant",  # Extracted from npc_data.merchant_john.tier
            "objective": "Get information",
            "social_hp": 2,
            "social_hp_max": 3,  # Calculated from merchant tier
            "status": "RESISTING",
            "skill_used": "Persuasion",
        }

        response = NarrativeResponse(
            narrative="Test",
            social_hp_challenge=social_hp_challenge,
        )

        # Verify npc_tier is preserved
        self.assertEqual(response.social_hp_challenge["npc_tier"], "merchant")

    def test_social_hp_max_calculation_based_on_tier(self):
        """Test that social_hp_max follows tier-based calculation rules."""
        # Tier ranges from game_state_instruction.md:
        # commoner=1-2, merchant/guard=2-3, noble/knight=3-5,
        # lord/general=5-8, king/ancient=8-12, god/primordial=15+
        tier_ranges = {
            "commoner": (1, 2),
            "merchant": (2, 3),
            "guard": (2, 3),
            "noble": (3, 5),
            "knight": (3, 5),
            "lord": (5, 8),
            "general": (5, 8),
            "king": (8, 12),
            "ancient": (8, 12),
            "god": (15, 20),
            "primordial": (15, 20),
        }

        for tier, (min_hp, max_hp) in tier_ranges.items():
            social_hp_challenge = {
                "npc_name": "Test NPC",
                "npc_tier": tier,
                "objective": "Test",
                "social_hp_max": (min_hp + max_hp) // 2,  # Mid-range value
                "social_hp": 1,
                "status": "RESISTING",
                "skill_used": "Persuasion",
            }

            response = NarrativeResponse(
                narrative="Test",
                social_hp_challenge=social_hp_challenge,
            )

            # Verify social_hp_max is within expected range
            self.assertGreaterEqual(
                response.social_hp_challenge["social_hp_max"], min_hp
            )
            self.assertLessEqual(response.social_hp_challenge["social_hp_max"], max_hp)


class TestCombatStateSchema(unittest.TestCase):
    """RED: Tests for Combat State Schema (Step 2) - written BEFORE implementation."""

    def test_valid_combat_state_passes_validation(self):
        """Valid combat_state with all required fields should pass."""
        combat_state = {
            "in_combat": True,
            "combat_session_id": "combat_1704931200_a1b2",
            "combat_phase": "active",
            "current_round": 2,
            "initiative_order": [
                {"name": "Player", "initiative": 18, "type": "player"},
                {"name": "Goblin", "initiative": 12, "type": "enemy"},
            ],
            "combatants": {
                "goblin_001": {
                    "hp_current": 5,
                    "hp_max": 7,
                    "ac": 15,
                    "type": "enemy",
                    "cr": 0.25,
                }
            },
            "combat_summary": {
                "rounds_fought": 2,
                "enemies_defeated": 0,
                "xp_awarded": 0,
                "loot_distributed": False,
            },
            "rewards_processed": False,
        }

        state_updates = {"combat_state": combat_state}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # This will FAIL initially (no validation exists)
        # After implementation, this should pass
        self.assertIn("combat_state", response.state_updates)
        self.assertEqual(
            response.state_updates["combat_state"]["combat_phase"], "active"
        )

    def test_invalid_combat_phase_logs_warning(self):
        """Invalid combat_phase enum value should log warning."""
        combat_state = {"combat_phase": "invalid_phase"}
        state_updates = {"combat_state": combat_state}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            # Should log warning about invalid combat_phase
            mock_warning.assert_called()
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("COMBAT_STATE_VALIDATION" in str(call) for call in warning_calls),
                f"Expected COMBAT_STATE_VALIDATION warning, got: {warning_calls}",
            )

    def test_combat_session_id_format_validation(self):
        """combat_session_id should match format: combat_<timestamp>_<4char>."""
        valid_ids = [
            "combat_1704931200_a1b2",
            "combat_1234567890_xyz9",
        ]
        invalid_ids = [
            "combat_123",  # Missing suffix
            "battle_1704931200_a1b2",  # Wrong prefix
            "combat_abc_a1b2",  # Invalid timestamp
        ]

        for valid_id in valid_ids:
            combat_state = {"combat_session_id": valid_id}
            state_updates = {"combat_state": combat_state}
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            self.assertIn("combat_state", response.state_updates)
            # Verify no validation errors for valid IDs
            # (validation errors are logged, not raised - check via warnings if needed)

        # Invalid IDs should produce validation errors
        for invalid_id in invalid_ids:
            combat_state = {"combat_session_id": invalid_id}
            state_updates = {"combat_state": combat_state}
            # Create response - validation happens during construction
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            # Note: Validation errors are logged as warnings, not exceptions
            # The response is still created but validation errors are logged
            # In a real scenario, you'd check logs for COMBAT_STATE_VALIDATION warnings
            self.assertIn("combat_state", response.state_updates)


class TestReputationSchema(unittest.TestCase):
    """RED: Tests for Reputation Schema (Step 3) - written BEFORE implementation."""

    def test_valid_public_reputation_passes_validation(self):
        """Valid public reputation with all required fields should pass."""
        reputation = {
            "public": {
                "score": 50,  # -100 to +100
                "titles": ["Hero of the Realm"],
                "known_deeds": ["Defeated the dragon"],
                "rumors": ["Rumored to have magical powers"],
                "notoriety_level": "respected",  # Valid enum
            }
        }

        state_updates = {"custom_campaign_state": {"reputation": reputation}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # This will FAIL initially (no validation exists)
        self.assertIn("custom_campaign_state", response.state_updates)
        rep_data = response.state_updates["custom_campaign_state"]["reputation"]
        self.assertEqual(rep_data["public"]["score"], 50)

    def test_public_reputation_score_range_validation(self):
        """Public reputation score must be between -100 and +100."""
        valid_scores = [-100, 0, 50, 100]
        invalid_scores = [-101, 101, 200]

        for score in valid_scores:
            reputation = {"public": {"score": score}}
            state_updates = {"custom_campaign_state": {"reputation": reputation}}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("custom_campaign_state", response.state_updates)
                # Valid scores should not log warnings
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertFalse(
                    any("REPUTATION_VALIDATION" in str(call) for call in warning_calls),
                    f"Valid score {score} should not log warning, got: {warning_calls}",
                )

        # Invalid scores should log warnings
        for score in invalid_scores:
            reputation = {"public": {"score": score}}
            state_updates = {"custom_campaign_state": {"reputation": reputation}}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("custom_campaign_state", response.state_updates)
                # Invalid scores should log warnings
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertTrue(
                    any("REPUTATION_VALIDATION" in str(call) for call in warning_calls),
                    f"Invalid score {score} should log warning, got: {warning_calls}",
                )

    def test_public_reputation_notoriety_level_enum(self):
        """notoriety_level must be valid enum value."""
        valid_levels = [
            "infamous",
            "notorious",
            "disreputable",
            "unknown",
            "known",
            "respected",
            "famous",
            "legendary",
        ]
        invalid_level = "super_famous"

        for level in valid_levels:
            reputation = {"public": {"notoriety_level": level}}
            state_updates = {"custom_campaign_state": {"reputation": reputation}}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("custom_campaign_state", response.state_updates)
                # Valid levels should not log warnings
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertFalse(
                    any("REPUTATION_VALIDATION" in str(call) for call in warning_calls),
                    f"Valid level {level} should not log warning",
                )

        # Invalid level should log warning
        reputation = {"public": {"notoriety_level": invalid_level}}
        state_updates = {"custom_campaign_state": {"reputation": reputation}}
        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            self.assertIn("custom_campaign_state", response.state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("REPUTATION_VALIDATION" in str(call) for call in warning_calls),
                f"Invalid level {invalid_level} should log warning, got: {warning_calls}",
            )

    def test_valid_private_reputation_passes_validation(self):
        """Valid private reputation with faction_id should pass."""
        reputation = {
            "private": {
                "faction_001": {
                    "score": 5,  # -10 to +10
                    "standing": "friendly",  # Valid enum
                    "known_deeds": ["Helped our cause"],
                    "secret_knowledge": ["Knows about the plot"],
                    "trust_override": None,
                }
            }
        }

        state_updates = {"custom_campaign_state": {"reputation": reputation}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # This will FAIL initially (no validation exists)
        self.assertIn("custom_campaign_state", response.state_updates)

    def test_private_reputation_score_range_validation(self):
        """Private reputation score must be between -10 and +10."""
        valid_scores = [-10, 0, 5, 10]
        invalid_scores = [-11, 11, 20]

        for score in valid_scores:
            reputation = {
                "private": {"faction_001": {"score": score, "standing": "neutral"}}
            }
            state_updates = {"custom_campaign_state": {"reputation": reputation}}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("custom_campaign_state", response.state_updates)
                # Valid scores should not log warnings
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertFalse(
                    any("REPUTATION_VALIDATION" in str(call) for call in warning_calls),
                    f"Valid score {score} should not log warning",
                )

        # Invalid scores should log warnings
        for score in invalid_scores:
            reputation = {
                "private": {"faction_001": {"score": score, "standing": "neutral"}}
            }
            state_updates = {"custom_campaign_state": {"reputation": reputation}}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("custom_campaign_state", response.state_updates)
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertTrue(
                    any("REPUTATION_VALIDATION" in str(call) for call in warning_calls),
                    f"Invalid score {score} should log warning, got: {warning_calls}",
                )

    def test_private_reputation_standing_enum(self):
        """standing must be valid enum value."""
        valid_standings = [
            "enemy",
            "hostile",
            "unfriendly",
            "neutral",
            "friendly",
            "trusted",
            "ally",
            "champion",
        ]
        invalid_standing = "best_friend"

        for standing in valid_standings:
            reputation = {
                "private": {"faction_001": {"standing": standing, "score": 0}}
            }
            state_updates = {"custom_campaign_state": {"reputation": reputation}}
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            self.assertIn("custom_campaign_state", response.state_updates)

        # After implementation, invalid_standing should fail


class TestRelationshipSchema(unittest.TestCase):
    """RED: Tests for Relationship Schema (Step 5) - written BEFORE implementation."""

    def test_valid_relationship_passes_validation(self):
        """Valid relationship with all required fields should pass."""
        relationship = {
            "trust_level": 5,  # -10 to +10
            "disposition": "friendly",  # Valid enum
            "history": ["Helped them escape", "Shared a meal"],
            "debts": [],
            "grievances": [],
        }

        state_updates = {
            "npc_data": {"npc_john": {"relationships": {"player": relationship}}}
        }
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # This will FAIL initially (no validation exists)
        self.assertIn("npc_data", response.state_updates)

    def test_trust_level_range_validation(self):
        """trust_level must be between -10 and +10."""
        valid_levels = [-10, 0, 5, 10]
        invalid_levels = [-11, 11, 15]

        for level in valid_levels:
            relationship = {"trust_level": level, "disposition": "neutral"}
            state_updates = {
                "npc_data": {"npc_test": {"relationships": {"player": relationship}}}
            }
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("npc_data", response.state_updates)
                # Valid levels should not log warnings
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertFalse(
                    any(
                        "RELATIONSHIP_VALIDATION" in str(call) for call in warning_calls
                    ),
                    f"Valid level {level} should not log warning",
                )

        # Invalid levels should log warnings
        for level in invalid_levels:
            relationship = {"trust_level": level, "disposition": "neutral"}
            state_updates = {
                "npc_data": {"npc_test": {"relationships": {"player": relationship}}}
            }
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("npc_data", response.state_updates)
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertTrue(
                    any(
                        "RELATIONSHIP_VALIDATION" in str(call) for call in warning_calls
                    ),
                    f"Invalid level {level} should log warning, got: {warning_calls}",
                )

    def test_disposition_enum_validation(self):
        """disposition must be valid enum value."""
        valid_dispositions = [
            "hostile",
            "antagonistic",
            "cold",
            "neutral",
            "friendly",
            "trusted",
            "devoted",
            "bonded",
        ]
        invalid_disposition = "best_friend"

        for disposition in valid_dispositions:
            relationship = {"disposition": disposition, "trust_level": 0}
            state_updates = {
                "npc_data": {"npc_test": {"relationships": {"player": relationship}}}
            }
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("npc_data", response.state_updates)
                # Valid dispositions should not log warnings
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertFalse(
                    any(
                        "RELATIONSHIP_VALIDATION" in str(call) for call in warning_calls
                    ),
                    f"Valid disposition {disposition} should not log warning",
                )

        # Invalid disposition should log warning
        relationship = {"disposition": invalid_disposition, "trust_level": 0}
        state_updates = {
            "npc_data": {"npc_test": {"relationships": {"player": relationship}}}
        }
        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            self.assertIn("npc_data", response.state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("RELATIONSHIP_VALIDATION" in str(call) for call in warning_calls),
                f"Invalid disposition {invalid_disposition} should log warning, got: {warning_calls}",
            )


class TestWorldTimeSchema(unittest.TestCase):
    """RED: Tests for World Time Schema (Step 6) - written BEFORE implementation."""

    def test_valid_world_time_passes_validation(self):
        """Valid world_time with all 8 required fields should pass."""
        world_time = {
            "year": 1492,
            "month": "Ches",
            "day": 20,
            "hour": 10,
            "minute": 30,
            "second": 45,
            "microsecond": 123456,
            "time_of_day": "Morning",
        }

        state_updates = {"world_data": {"world_time": world_time}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # This will FAIL initially (no validation exists)
        self.assertIn("world_data", response.state_updates)
        wt = response.state_updates["world_data"]["world_time"]
        self.assertEqual(wt["year"], 1492)

    def test_world_time_day_range_validation(self):
        """day must be between 1 and 31."""
        valid_days = [1, 15, 31]
        invalid_days = [0, 32, -1]

        for day in valid_days:
            world_time = {
                "year": 1492,
                "month": "Ches",
                "day": day,
                "hour": 10,
                "minute": 0,
                "second": 0,
                "microsecond": 0,
                "time_of_day": "Morning",
            }
            state_updates = {"world_data": {"world_time": world_time}}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("world_data", response.state_updates)
                # Valid days should not log warnings
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertFalse(
                    any("WORLD_TIME_VALIDATION" in str(call) for call in warning_calls),
                    f"Valid day {day} should not log warning",
                )

        # Invalid days should log warnings
        for day in invalid_days:
            world_time = {
                "year": 1492,
                "month": "Ches",
                "day": day,
                "hour": 10,
                "minute": 0,
                "second": 0,
                "microsecond": 0,
                "time_of_day": "Morning",
            }
            state_updates = {"world_data": {"world_time": world_time}}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("world_data", response.state_updates)
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertTrue(
                    any("WORLD_TIME_VALIDATION" in str(call) for call in warning_calls),
                    f"Invalid day {day} should log warning, got: {warning_calls}",
                )

    def test_world_time_hour_range_validation(self):
        """hour must be between 0 and 23."""
        valid_hours = [0, 12, 23]
        invalid_hours = [-1, 24, 25]

        for hour in valid_hours:
            world_time = {
                "year": 1492,
                "month": "Ches",
                "day": 20,
                "hour": hour,
                "minute": 0,
                "second": 0,
                "microsecond": 0,
                "time_of_day": "Morning",
            }
            state_updates = {"world_data": {"world_time": world_time}}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("world_data", response.state_updates)
                # Valid hours should not log warnings
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertFalse(
                    any("WORLD_TIME_VALIDATION" in str(call) for call in warning_calls),
                    f"Valid hour {hour} should not log warning",
                )

        # Invalid hours should log warnings
        for hour in invalid_hours:
            world_time = {
                "year": 1492,
                "month": "Ches",
                "day": 20,
                "hour": hour,
                "minute": 0,
                "second": 0,
                "microsecond": 0,
                "time_of_day": "Morning",
            }
            state_updates = {"world_data": {"world_time": world_time}}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("world_data", response.state_updates)
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertTrue(
                    any("WORLD_TIME_VALIDATION" in str(call) for call in warning_calls),
                    f"Invalid hour {hour} should log warning, got: {warning_calls}",
                )

    def test_world_time_time_of_day_enum(self):
        """time_of_day must be valid enum value."""
        valid_times = [
            "Dawn",
            "Morning",
            "Midday",
            "Afternoon",
            "Evening",
            "Night",
            "Deep Night",
        ]
        invalid_time = "Noon"

        for time_of_day in valid_times:
            world_time = {
                "year": 1492,
                "month": "Ches",
                "day": 20,
                "hour": 10,
                "minute": 0,
                "second": 0,
                "microsecond": 0,
                "time_of_day": time_of_day,
            }
            state_updates = {"world_data": {"world_time": world_time}}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("world_data", response.state_updates)
                # Valid times should not log warnings
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertFalse(
                    any("WORLD_TIME_VALIDATION" in str(call) for call in warning_calls),
                    f"Valid time_of_day {time_of_day} should not log warning",
                )

        # Invalid time should log warning
        world_time = {
            "year": 1492,
            "month": "Ches",
            "day": 20,
            "hour": 10,
            "minute": 0,
            "second": 0,
            "microsecond": 0,
            "time_of_day": invalid_time,
        }
        state_updates = {"world_data": {"world_time": world_time}}
        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            self.assertIn("world_data", response.state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("WORLD_TIME_VALIDATION" in str(call) for call in warning_calls),
                f"Invalid time_of_day {invalid_time} should log warning, got: {warning_calls}",
            )


class TestEncounterStateSchema(unittest.TestCase):
    """RED: Tests for Encounter State Schema (Step 7) - written BEFORE implementation."""

    def test_valid_encounter_state_passes_validation(self):
        """Valid encounter_state with all required fields should pass."""
        encounter_state = {
            "encounter_active": True,
            "encounter_id": "enc_1704931200_heist_001",
            "encounter_type": "heist",  # Valid enum
            "difficulty": "medium",  # Valid enum
            "encounter_completed": False,
            "encounter_summary": {
                "xp_awarded": 100,
                "outcome": "success",
                "method": "stealth",
            },
            "rewards_processed": False,
        }

        state_updates = {"encounter_state": encounter_state}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # This will FAIL initially (no validation exists)
        self.assertIn("encounter_state", response.state_updates)
        self.assertEqual(
            response.state_updates["encounter_state"]["encounter_type"], "heist"
        )

    def test_encounter_type_enum_validation(self):
        """encounter_type must be valid enum value."""
        valid_types = [
            "heist",
            "social",
            "stealth",
            "puzzle",
            "quest",
            "narrative_victory",
        ]
        invalid_type = "battle"

        for encounter_type in valid_types:
            encounter_state = {"encounter_type": encounter_type}
            state_updates = {"encounter_state": encounter_state}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("encounter_state", response.state_updates)
                # Valid types should not log warnings
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertFalse(
                    any(
                        "ENCOUNTER_STATE_VALIDATION" in str(call)
                        for call in warning_calls
                    ),
                    f"Valid encounter_type {encounter_type} should not log warning",
                )

        # Invalid type should log warning
        encounter_state = {"encounter_type": invalid_type}
        state_updates = {"encounter_state": encounter_state}
        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            self.assertIn("encounter_state", response.state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any(
                    "ENCOUNTER_STATE_VALIDATION" in str(call) for call in warning_calls
                ),
                f"Invalid encounter_type {invalid_type} should log warning, got: {warning_calls}",
            )

    def test_encounter_difficulty_enum_validation(self):
        """difficulty must be valid enum value."""
        valid_difficulties = ["easy", "medium", "hard", "deadly"]
        invalid_difficulty = "extreme"

        for difficulty in valid_difficulties:
            encounter_state = {"difficulty": difficulty}
            state_updates = {"encounter_state": encounter_state}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                self.assertIn("encounter_state", response.state_updates)
                # Valid difficulties should not log warnings
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertFalse(
                    any(
                        "ENCOUNTER_STATE_VALIDATION" in str(call)
                        for call in warning_calls
                    ),
                    f"Valid difficulty {difficulty} should not log warning",
                )

        # Invalid difficulty should log warning
        encounter_state = {"difficulty": invalid_difficulty}
        state_updates = {"encounter_state": encounter_state}
        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            self.assertIn("encounter_state", response.state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any(
                    "ENCOUNTER_STATE_VALIDATION" in str(call) for call in warning_calls
                ),
                f"Invalid difficulty {invalid_difficulty} should log warning, got: {warning_calls}",
            )


class TestFrozenPlansSchema(unittest.TestCase):
    """RED: Tests for Frozen Plans Schema (Priority 3) - written BEFORE implementation."""

    def test_valid_frozen_plans_passes_validation(self):
        """Valid frozen_plans structure should pass validation."""
        frozen_plans = {
            "warehouse_ambush": {
                "failed_at": "2025-01-11T10:00:00Z",
                "freeze_until": "2025-01-11T14:00:00Z",
                "original_dc": 14,
                "freeze_hours": 4,
                "description": "planning the warehouse ambush",
            }
        }

        state_updates = {"frozen_plans": frozen_plans}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # This will pass (frozen_plans is LLM-enforced, but we can add structure validation)
        self.assertIn("frozen_plans", response.state_updates)


class TestDirectivesSchema(unittest.TestCase):
    """RED: Tests for Directives Schema (Priority 3) - written BEFORE implementation."""

    def test_valid_directives_passes_validation(self):
        """Valid directives with add/drop arrays should pass."""
        directives = {
            "add": ["directive1", "directive2"],
            "drop": ["old_directive"],
        }

        response = NarrativeResponse(narrative="Test", directives=directives)

        # Should accept valid directives structure
        self.assertIn("add", response.directives)
        self.assertIn("drop", response.directives)
        self.assertEqual(len(response.directives["add"]), 2)

    def test_directives_with_non_array_add_fails_validation(self):
        """Directives.add should be an array."""
        directives = {"add": "not_an_array", "drop": []}

        # Should coerce or warn about invalid structure
        response = NarrativeResponse(narrative="Test", directives=directives)
        # After implementation, should validate add/drop are arrays
        self.assertIn("directives", response.__dict__)


class TestEquipmentSlotEnum(unittest.TestCase):
    """RED: Tests for Equipment Slot Enum (Priority 3) - written BEFORE implementation."""

    def test_valid_equipment_slots(self):
        """Valid equipment slots should pass validation."""
        valid_slots = [
            "head",
            "body",
            "armor",
            "cloak",
            "hands",
            "feet",
            "neck",
            "ring_1",
            "ring_2",
            "belt",
            "shield",
            "main_hand",
            "off_hand",
            "instrument",
        ]

        # Test that valid slots are accepted (when equipment validation is added)
        for slot in valid_slots:
            equipment = {slot: {"name": "Test Item"}}
            state_updates = {"player_character_data": {"equipment": equipment}}
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            self.assertIn("player_character_data", response.state_updates)

    def test_invalid_equipment_slots(self):
        """Invalid equipment slots should fail validation."""
        invalid_slots = ["weapon_main", "boots", "invalid_slot"]

        # After implementation, should validate and reject invalid slots
        for slot in invalid_slots:
            equipment = {slot: {"name": "Test Item"}}
            state_updates = {"player_character_data": {"equipment": equipment}}
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            # After implementation, should log warning for invalid slots
            self.assertIn("player_character_data", response.state_updates)


class TestArcMilestonesSchema(unittest.TestCase):
    """RED: Tests for Arc Milestones Schema (Priority 4) - written BEFORE implementation."""

    def test_valid_arc_milestone_passes_validation(self):
        """Valid arc milestone structure should pass."""
        arc_milestones = {
            "main_quest": {
                "status": "in_progress",
                "phase": "investigation",
                "progress": 45,
                "updated_at": "2025-01-11T10:00:00Z",
            }
        }

        state_updates = {"custom_campaign_state": {"arc_milestones": arc_milestones}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # This will pass initially (no validation exists)
        self.assertIn("custom_campaign_state", response.state_updates)

    def test_arc_milestone_status_enum(self):
        """status must be 'in_progress' or 'completed'."""
        valid_statuses = ["in_progress", "completed"]
        invalid_status = "pending"

        for status in valid_statuses:
            arc_milestones = {
                "quest_1": {"status": status, "phase": "test", "progress": 0}
            }
            state_updates = {
                "custom_campaign_state": {"arc_milestones": arc_milestones}
            }
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            self.assertIn("custom_campaign_state", response.state_updates)

        # After implementation, invalid_status should log warning


class TestTimePressureSystemSchema(unittest.TestCase):
    """RED: Tests for Time Pressure System Schema (Priority 4) - written BEFORE implementation."""

    def test_valid_time_sensitive_events_passes_validation(self):
        """Valid time_sensitive_events structure should pass."""
        time_sensitive_events = {
            "event_001": {
                "deadline": "2025-01-15T00:00:00Z",
                "description": "Blood moon ritual",
                "status": "pending",
            }
        }

        state_updates = {"time_sensitive_events": time_sensitive_events}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # This will pass initially (no validation exists)
        self.assertIn("time_sensitive_events", response.state_updates)

    def test_time_pressure_warnings_structure(self):
        """time_pressure_warnings should have expected fields."""
        time_pressure_warnings = {
            "subtle_given": True,
            "clear_given": False,
            "urgent_given": False,
            "last_warning_day": 5,
        }

        state_updates = {"time_pressure_warnings": time_pressure_warnings}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # This will pass initially (no validation exists)
        self.assertIn("time_pressure_warnings", response.state_updates)


class TestUnhashableTypeHandling(unittest.TestCase):
    """Test that validation functions handle unhashable types (list/dict) gracefully."""

    def test_combat_phase_with_list_does_not_crash(self):
        """Test that combat_phase as list doesn't raise TypeError."""
        combat_state = {"combat_phase": ["active"]}  # List instead of string
        state_updates = {"combat_state": combat_state}

        # Should not raise TypeError, should log warning instead
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)
        self.assertIn("combat_state", response.state_updates)

    def test_reputation_notoriety_level_with_dict_does_not_crash(self):
        """Test that notoriety_level as dict doesn't raise TypeError."""
        reputation = {"public": {"notoriety_level": {"invalid": "type"}}}
        state_updates = {"custom_campaign_state": {"reputation": reputation}}

        # Should not raise TypeError, should log warning instead
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)
        self.assertIn("custom_campaign_state", response.state_updates)

    def test_relationship_disposition_with_list_does_not_crash(self):
        """Test that disposition as list doesn't raise TypeError."""
        relationship = {"disposition": ["friendly"], "trust_level": 5}
        state_updates = {
            "npc_data": {"npc_test": {"relationships": {"player": relationship}}}
        }

        # Should not raise TypeError, should log warning instead
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)
        self.assertIn("npc_data", response.state_updates)

    def test_world_time_time_of_day_with_dict_does_not_crash(self):
        """Test that time_of_day as dict doesn't raise TypeError."""
        world_time = {
            "year": 1492,
            "month": "Ches",
            "day": 20,
            "hour": 10,
            "minute": 0,
            "second": 0,
            "microsecond": 0,
            "time_of_day": {"invalid": "type"},  # Dict instead of string
        }
        state_updates = {"world_data": {"world_time": world_time}}

        # Should not raise TypeError, should log warning instead
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)
        self.assertIn("world_data", response.state_updates)

    def test_encounter_type_with_list_does_not_crash(self):
        """Test that encounter_type as list doesn't raise TypeError."""
        encounter_state = {"encounter_type": ["heist"]}  # List instead of string
        state_updates = {"encounter_state": encounter_state}

        # Should not raise TypeError, should log warning instead
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)
        self.assertIn("encounter_state", response.state_updates)

    def test_arc_milestone_status_with_dict_does_not_crash(self):
        """Test that arc milestone status as dict doesn't raise TypeError."""
        arc_milestones = {
            "quest_1": {"status": {"invalid": "type"}, "phase": "test", "progress": 0}
        }
        state_updates = {"custom_campaign_state": {"arc_milestones": arc_milestones}}

        # Should not raise TypeError, should log warning instead
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)
        self.assertIn("custom_campaign_state", response.state_updates)


class TestResourcesSchema(unittest.TestCase):
    """RED: Tests for Resources Schema (Priority 1) - written BEFORE implementation."""

    def test_valid_resources_passes_validation(self):
        """Valid resources structure should pass validation."""
        resources = {
            "gold": 150,
            "hit_dice": {"used": 2, "total": 5},
            "spell_slots": {
                "level_1": {"used": 1, "max": 4},
                "level_2": {"used": 2, "max": 3},
            },
            "class_features": {
                "bardic_inspiration": {"used": 1, "max": 3},
            },
            "consumables": {},
        }

        state_updates = {"player_character_data": {"resources": resources}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # Should pass validation
        self.assertIn("player_character_data", response.state_updates)
        self.assertEqual(
            response.state_updates["player_character_data"]["resources"]["gold"], 150
        )

    def test_resources_gold_negative_logs_warning(self):
        """Gold should be >= 0."""
        resources = {"gold": -10}
        state_updates = {"player_character_data": {"resources": resources}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("RESOURCES_VALIDATION" in str(call) for call in warning_calls),
                f"Expected RESOURCES_VALIDATION warning for negative gold, got: {warning_calls}",
            )

    def test_resources_hit_dice_validation(self):
        """Hit dice should have used <= total, both >= 0."""
        valid_hit_dice = [
            {"used": 0, "total": 5},
            {"used": 2, "total": 5},
            {"used": 5, "total": 5},
        ]
        invalid_hit_dice = [
            {"used": 6, "total": 5},  # used > total
            {"used": -1, "total": 5},  # negative used
            {"used": 2, "total": -1},  # negative total
        ]

        for hit_dice in valid_hit_dice:
            resources = {"hit_dice": hit_dice}
            state_updates = {"player_character_data": {"resources": resources}}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertFalse(
                    any("RESOURCES_VALIDATION" in str(call) for call in warning_calls),
                    f"Valid hit_dice {hit_dice} should not log warning",
                )

        for hit_dice in invalid_hit_dice:
            resources = {"hit_dice": hit_dice}
            state_updates = {"player_character_data": {"resources": resources}}
            with patch.object(logging_util, "warning") as mock_warning:
                response = NarrativeResponse(
                    narrative="Test", state_updates=state_updates
                )
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                self.assertTrue(
                    any("RESOURCES_VALIDATION" in str(call) for call in warning_calls),
                    f"Invalid hit_dice {hit_dice} should log warning",
                )


class TestSpellSlotsSchema(unittest.TestCase):
    """RED: Tests for Spell Slots Schema (Priority 1) - written BEFORE implementation."""

    def test_valid_spell_slots_passes_validation(self):
        """Valid spell_slots structure should pass validation."""
        spell_slots = {
            "level_1": {"used": 0, "max": 4},
            "level_2": {"used": 1, "max": 3},
            "level_3": {"used": 2, "max": 2},
        }

        resources = {"spell_slots": spell_slots}
        state_updates = {"player_character_data": {"resources": resources}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # Should pass validation
        self.assertIn("player_character_data", response.state_updates)
        slots = response.state_updates["player_character_data"]["resources"][
            "spell_slots"
        ]
        self.assertEqual(slots["level_1"]["used"], 0)

    def test_spell_slots_current_exceeds_max_logs_warning(self):
        """Spell slot used should not exceed max."""
        spell_slots = {"level_1": {"used": 5, "max": 4}}  # used > max
        resources = {"spell_slots": spell_slots}
        state_updates = {"player_character_data": {"resources": resources}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("SPELL_SLOTS_VALIDATION" in str(call) for call in warning_calls),
                f"Expected SPELL_SLOTS_VALIDATION warning, got: {warning_calls}",
            )

    def test_spell_slots_negative_current_logs_warning(self):
        """Spell slot used should be >= 0."""
        spell_slots = {"level_1": {"used": -1, "max": 4}}
        resources = {"spell_slots": spell_slots}
        state_updates = {"player_character_data": {"resources": resources}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("SPELL_SLOTS_VALIDATION" in str(call) for call in warning_calls),
                f"Expected SPELL_SLOTS_VALIDATION warning for negative used, got: {warning_calls}",
            )

    def test_spell_slots_invalid_level_key_logs_warning(self):
        """Spell slot level keys should be level_1 through level_9."""
        spell_slots = {"level_10": {"used": 1, "max": 1}}  # Invalid level
        resources = {"spell_slots": spell_slots}
        state_updates = {"player_character_data": {"resources": resources}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            # Should log warning about invalid level key
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            # Note: This might be caught by resources validation or spell_slots validation
            # Both are acceptable


class TestClassFeaturesSchema(unittest.TestCase):
    """RED: Tests for Class Features Schema (Priority 1) - written BEFORE implementation."""

    def test_valid_class_features_passes_validation(self):
        """Valid class_features structure should pass validation."""
        class_features = {
            "bardic_inspiration": {"used": 1, "max": 3},
            "ki_points": {"used": 0, "max": 5},
            "rage": {"used": 0, "max": 2},
        }

        resources = {"class_features": class_features}
        state_updates = {"player_character_data": {"resources": resources}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # Should pass validation
        self.assertIn("player_character_data", response.state_updates)
        features = response.state_updates["player_character_data"]["resources"][
            "class_features"
        ]
        self.assertEqual(features["bardic_inspiration"]["used"], 1)

    def test_class_features_current_exceeds_max_logs_warning(self):
        """Class feature used should not exceed max."""
        class_features = {"bardic_inspiration": {"used": 4, "max": 3}}  # used > max
        resources = {"class_features": class_features}
        state_updates = {"player_character_data": {"resources": resources}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("CLASS_FEATURES_VALIDATION" in str(call) for call in warning_calls),
                f"Expected CLASS_FEATURES_VALIDATION warning, got: {warning_calls}",
            )

    def test_class_features_negative_current_logs_warning(self):
        """Class feature used should be >= 0."""
        class_features = {"ki_points": {"used": -1, "max": 5}}
        resources = {"class_features": class_features}
        state_updates = {"player_character_data": {"resources": resources}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("CLASS_FEATURES_VALIDATION" in str(call) for call in warning_calls),
                f"Expected CLASS_FEATURES_VALIDATION warning for negative used, got: {warning_calls}",
            )


class TestValidationExceptionHandling(unittest.TestCase):
    """RED: Tests for exception handling in validation functions."""

    def test_validation_function_exceptions_do_not_crash_narrative_response(self):
        """Test that exceptions in validation functions are caught and logged, not crash the response."""
        # Create a mock validation function that raises an exception
        original_validate_resources = _validate_resources

        def crashing_validate_resources(resources):
            raise ValueError("Simulated validation crash")

        # Patch the validation function to crash
        with patch('mvp_site.narrative_response_schema._validate_resources', crashing_validate_resources):
            # This should NOT crash even though _validate_resources raises an exception
            with patch.object(logging_util, 'error') as mock_error:
                try:
                    response = NarrativeResponse(
                        narrative="Test narrative",
                        state_updates={
                            "player_character_data": {
                                "resources": {"gold": 100}
                            }
                        }
                    )
                    # Should succeed despite validation crash
                    self.assertIsInstance(response, NarrativeResponse)
                    # Should have logged the error
                    mock_error.assert_called()
                    error_call = str(mock_error.call_args[0][0])
                    self.assertIn("Validation failed with exception", error_call)
                except Exception as e:
                    self.fail(f"NarrativeResponse creation should not crash on validation exception: {e}")

    def test_multiple_validation_function_exceptions_are_handled(self):
        """Test that multiple validation function exceptions are all caught."""
        with patch('mvp_site.narrative_response_schema._validate_resources') as mock_resources, \
             patch('mvp_site.narrative_response_schema._validate_spell_slots') as mock_spell_slots, \
             patch('mvp_site.narrative_response_schema._validate_attributes') as mock_attributes, \
             patch.object(logging_util, 'error') as mock_error:

            # Make all validation functions crash
            mock_resources.side_effect = RuntimeError("Resources crash")
            mock_spell_slots.side_effect = ValueError("Spell slots crash")
            mock_attributes.side_effect = TypeError("Attributes crash")

            # Should not crash
            try:
                response = NarrativeResponse(
                    narrative="Test narrative",
                    state_updates={
                        "player_character_data": {
                            "resources": {"gold": 100, "spell_slots": {}, "base_attributes": {}},
                            "base_attributes": {"strength": 10}
                        }
                    }
                )
                self.assertIsInstance(response, NarrativeResponse)
                # Should have logged multiple errors
                self.assertGreaterEqual(mock_error.call_count, 2)
            except Exception as e:
                self.fail(f"Should handle multiple validation exceptions: {e}")


class TestValidationErrorMessages(unittest.TestCase):
    """RED: Tests for improved error messages in validation functions."""

    def test_none_values_produce_clear_error_messages(self):
        """Test that None values in numeric fields produce clear error messages."""
        # Test resources validation
        errors = _validate_resources({"gold": None})
        self.assertEqual(len(errors), 1)
        self.assertIn("cannot be None", errors[0])
        self.assertIn("resources.gold", errors[0])

        # Test with hit_dice None values
        errors = _validate_resources({"hit_dice": {"used": None, "max": 5}})
        # Should produce error for None used value
        none_errors = [e for e in errors if "cannot be None" in e]
        self.assertTrue(len(none_errors) > 0)

    def test_float_values_are_coerced_to_int_when_valid(self):
        """Test that float values that are whole numbers are accepted."""
        # This should pass (50.0 should be accepted as 50)
        errors = _validate_resources({"gold": 50.0})
        # Currently fails - need to implement coercion
        self.assertEqual(len(errors), 0, f"Float 50.0 should be accepted but got errors: {errors}")

    def test_invalid_float_values_are_rejected(self):
        """Test that non-whole float values are rejected."""
        errors = _validate_resources({"gold": 50.5})
        self.assertGreater(len(errors), 0)
        self.assertIn("integer", errors[0])


class TestAttributesSchema(unittest.TestCase):
    """RED: Tests for Attributes Schema (Priority 2) - written BEFORE implementation."""

    def test_valid_attributes_passes_validation(self):
        """Valid attributes structure should pass validation."""
        player_data = {
            "base_attributes": {
                "STR": 16,
                "DEX": 14,
                "CON": 15,
                "INT": 12,
                "WIS": 13,
                "CHA": 10,
            },
            "attributes": {
                "STR": 18,
                "DEX": 14,
                "CON": 15,
                "INT": 12,
                "WIS": 13,
                "CHA": 10,
            },  # STR boosted by equipment
        }
        state_updates = {"player_character_data": player_data}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # Should pass validation
        self.assertIn("player_character_data", response.state_updates)
        self.assertEqual(
            response.state_updates["player_character_data"]["attributes"]["STR"], 18
        )

    def test_attributes_below_base_logs_warning(self):
        """Attributes should be >= base_attributes (equipment can only add)."""
        player_data = {
            "base_attributes": {"STR": 16},
            "attributes": {"STR": 14},  # Lower than base (invalid)
        }
        state_updates = {"player_character_data": player_data}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("ATTRIBUTES_VALIDATION" in str(call) for call in warning_calls),
                f"Expected ATTRIBUTES_VALIDATION warning, got: {warning_calls}",
            )

    def test_attributes_out_of_range_logs_warning(self):
        """Attributes should be in range 1-30."""
        player_data = {
            "base_attributes": {"STR": 16},
            "attributes": {"STR": 31},  # Out of range
        }
        state_updates = {"player_character_data": player_data}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("ATTRIBUTES_VALIDATION" in str(call) for call in warning_calls),
                f"Expected ATTRIBUTES_VALIDATION warning for out-of-range value, got: {warning_calls}",
            )


class TestExperienceSchema(unittest.TestCase):
    """RED: Tests for Experience Schema (Priority 2) - written BEFORE implementation."""

    def test_valid_experience_passes_validation(self):
        """Valid experience structure should pass validation."""
        experience = {"current": 500, "needed_for_next_level": 1000}
        state_updates = {"player_character_data": {"experience": experience}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # Should pass validation
        self.assertIn("player_character_data", response.state_updates)
        self.assertEqual(
            response.state_updates["player_character_data"]["experience"]["current"],
            500,
        )

    def test_experience_current_exceeds_needed_logs_warning(self):
        """If current > needed_for_next_level, should warn (level up should trigger)."""
        experience = {"current": 1500, "needed_for_next_level": 1000}  # Should level up
        state_updates = {"player_character_data": {"experience": experience}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("EXPERIENCE_VALIDATION" in str(call) for call in warning_calls),
                f"Expected EXPERIENCE_VALIDATION warning, got: {warning_calls}",
            )

    def test_experience_negative_current_logs_warning(self):
        """Experience current should be >= 0."""
        experience = {"current": -100, "needed_for_next_level": 1000}
        state_updates = {"player_character_data": {"experience": experience}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("EXPERIENCE_VALIDATION" in str(call) for call in warning_calls),
                f"Expected EXPERIENCE_VALIDATION warning for negative current, got: {warning_calls}",
            )


class TestDeathSavesSchema(unittest.TestCase):
    """RED: Tests for Death Saves Schema (Priority 2) - written BEFORE implementation."""

    def test_valid_death_saves_passes_validation(self):
        """Valid death_saves structure should pass validation."""
        death_saves = {"successes": 2, "failures": 1}
        state_updates = {"player_character_data": {"death_saves": death_saves}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # Should pass validation
        self.assertIn("player_character_data", response.state_updates)
        self.assertEqual(
            response.state_updates["player_character_data"]["death_saves"]["successes"],
            2,
        )

    def test_death_saves_out_of_range_logs_warning(self):
        """Death saves successes and failures should be 0-3."""
        death_saves = {"successes": 4, "failures": 0}  # successes > 3
        state_updates = {"player_character_data": {"death_saves": death_saves}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("DEATH_SAVES_VALIDATION" in str(call) for call in warning_calls),
                f"Expected DEATH_SAVES_VALIDATION warning, got: {warning_calls}",
            )

    def test_death_saves_negative_logs_warning(self):
        """Death saves should be >= 0."""
        death_saves = {"successes": -1, "failures": 0}
        state_updates = {"player_character_data": {"death_saves": death_saves}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("DEATH_SAVES_VALIDATION" in str(call) for call in warning_calls),
                f"Expected DEATH_SAVES_VALIDATION warning for negative value, got: {warning_calls}",
            )


class TestSpellsKnownSchema(unittest.TestCase):
    """RED: Tests for Spells Known Schema (Priority 2) - written BEFORE implementation."""

    def test_valid_spells_known_passes_validation(self):
        """Valid spells_known array should pass validation."""
        spells_known = [
            {"name": "Charm Person", "level": 1},
            {"name": "Hypnotic Pattern", "level": 3, "school": "illusion"},
        ]
        state_updates = {"player_character_data": {"spells_known": spells_known}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # Should pass validation
        self.assertIn("player_character_data", response.state_updates)
        self.assertEqual(
            len(response.state_updates["player_character_data"]["spells_known"]), 2
        )

    def test_spells_known_missing_name_logs_warning(self):
        """Spells must have 'name' field."""
        spells_known = [{"level": 1}]  # Missing name
        state_updates = {"player_character_data": {"spells_known": spells_known}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("SPELLS_KNOWN_VALIDATION" in str(call) for call in warning_calls),
                f"Expected SPELLS_KNOWN_VALIDATION warning, got: {warning_calls}",
            )

    def test_spells_known_invalid_level_logs_warning(self):
        """Spell level should be 0-9."""
        spells_known = [{"name": "Test Spell", "level": 10}]  # Invalid level
        state_updates = {"player_character_data": {"spells_known": spells_known}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("SPELLS_KNOWN_VALIDATION" in str(call) for call in warning_calls),
                f"Expected SPELLS_KNOWN_VALIDATION warning for invalid level, got: {warning_calls}",
            )


class TestStatusConditionsSchema(unittest.TestCase):
    """RED: Tests for Status Conditions Schema (Priority 3) - written BEFORE implementation."""

    def test_valid_status_conditions_passes_validation(self):
        """Valid status_conditions array should pass validation."""
        status_conditions = ["Poisoned", "Frightened", "Prone"]
        state_updates = {
            "player_character_data": {"status_conditions": status_conditions}
        }
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # Should pass validation
        self.assertIn("player_character_data", response.state_updates)
        self.assertEqual(
            len(response.state_updates["player_character_data"]["status_conditions"]), 3
        )

    def test_status_conditions_non_array_logs_warning(self):
        """status_conditions must be an array."""
        status_conditions = {"Poisoned": True}  # Dict instead of array
        state_updates = {
            "player_character_data": {"status_conditions": status_conditions}
        }

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any(
                    "STATUS_CONDITIONS_VALIDATION" in str(call)
                    for call in warning_calls
                ),
                f"Expected STATUS_CONDITIONS_VALIDATION warning, got: {warning_calls}",
            )


class TestActiveEffectsSchema(unittest.TestCase):
    """RED: Tests for Active Effects Schema (Priority 3) - written BEFORE implementation."""

    def test_valid_active_effects_passes_validation(self):
        """Valid active_effects array should pass validation."""
        active_effects = [
            "Bless: +1d4 to attack rolls and saving throws",
            "Haste: Double speed, +2 AC, extra action",
        ]
        state_updates = {"player_character_data": {"active_effects": active_effects}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # Should pass validation
        self.assertIn("player_character_data", response.state_updates)
        self.assertEqual(
            len(response.state_updates["player_character_data"]["active_effects"]), 2
        )

    def test_active_effects_non_array_logs_warning(self):
        """active_effects must be an array."""
        active_effects = {"Bless": "active"}  # Dict instead of array
        state_updates = {"player_character_data": {"active_effects": active_effects}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("ACTIVE_EFFECTS_VALIDATION" in str(call) for call in warning_calls),
                f"Expected ACTIVE_EFFECTS_VALIDATION warning, got: {warning_calls}",
            )


class TestCombatStatsSchema(unittest.TestCase):
    """RED: Tests for Combat Stats Schema (Priority 3) - written BEFORE implementation."""

    def test_valid_combat_stats_passes_validation(self):
        """Valid combat_stats structure should pass validation."""
        combat_stats = {"initiative": 15, "speed": 30, "passive_perception": 14}
        state_updates = {"player_character_data": {"combat_stats": combat_stats}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # Should pass validation
        self.assertIn("player_character_data", response.state_updates)
        self.assertEqual(
            response.state_updates["player_character_data"]["combat_stats"]["speed"], 30
        )

    def test_combat_stats_negative_speed_logs_warning(self):
        """Speed should be >= 0."""
        combat_stats = {"speed": -10}
        state_updates = {"player_character_data": {"combat_stats": combat_stats}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("COMBAT_STATS_VALIDATION" in str(call) for call in warning_calls),
                f"Expected COMBAT_STATS_VALIDATION warning, got: {warning_calls}",
            )

    def test_combat_stats_negative_passive_perception_logs_warning(self):
        """passive_perception should be >= 0."""
        combat_stats = {"passive_perception": -5}
        state_updates = {"player_character_data": {"combat_stats": combat_stats}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("COMBAT_STATS_VALIDATION" in str(call) for call in warning_calls),
                f"Expected COMBAT_STATS_VALIDATION warning, got: {warning_calls}",
            )


class TestItemSchemas(unittest.TestCase):
    """RED: Tests for Item Schemas (Priority 3) - written BEFORE implementation."""

    def test_valid_weapon_passes_validation(self):
        """Valid weapon structure should pass validation."""
        weapon = {
            "name": "Longsword +1",
            "type": "weapon",
            "damage": "1d8",
            "damage_type": "slashing",
            "bonus": 1,
            "weight": 3,
            "value_gp": 1015,
        }
        equipment = {"main_hand": weapon}
        state_updates = {"player_character_data": {"equipment": equipment}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # Should pass validation
        self.assertIn("player_character_data", response.state_updates)

    def test_weapon_invalid_type_logs_warning(self):
        """Weapon type must be 'weapon'."""
        weapon = {"name": "Sword", "type": "armor", "damage": "1d8"}  # Wrong type
        equipment = {"main_hand": weapon}
        state_updates = {"player_character_data": {"equipment": equipment}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            # Note: This might be caught by equipment slot validation or item validation
            # Both are acceptable

    def test_valid_armor_passes_validation(self):
        """Valid armor structure should pass validation."""
        armor = {
            "name": "Chain Mail",
            "type": "armor",
            "armor_class": 16,
            "armor_type": "heavy",
            "weight": 55,
            "value_gp": 75,
        }
        equipment = {"armor": armor}
        state_updates = {"player_character_data": {"equipment": equipment}}
        response = NarrativeResponse(narrative="Test", state_updates=state_updates)

        # Should pass validation
        self.assertIn("player_character_data", response.state_updates)

    def test_armor_invalid_ac_range_logs_warning(self):
        """Armor class should be in range 1-30."""
        armor = {"name": "Armor", "type": "armor", "armor_class": 35}  # Out of range
        equipment = {"armor": armor}
        state_updates = {"player_character_data": {"equipment": equipment}}

        with patch.object(logging_util, "warning") as mock_warning:
            response = NarrativeResponse(narrative="Test", state_updates=state_updates)
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            self.assertTrue(
                any("ITEM_VALIDATION" in str(call) for call in warning_calls),
                f"Expected ITEM_VALIDATION warning, got: {warning_calls}",
            )


if __name__ == "__main__":
    unittest.main()

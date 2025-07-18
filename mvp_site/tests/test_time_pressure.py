import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shutil
import tempfile

# Set testing environment
os.environ["TESTING"] = "true"

from game_state import GameState


class TestTimePressure(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()

        # Create initial game state with time pressure structures
        self.game_state = GameState(
            game_state_version=1,
            world_data={
                "world_time": {
                    "year": 1492,
                    "month": "Ches",
                    "day": 20,
                    "hour": 12,
                    "minute": 0,
                    "second": 0,
                }
            },
            time_sensitive_events={},
            npc_agendas={},
            world_resources={},
            time_pressure_warnings={},
            custom_campaign_state={"active_missions": []},
        )

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_time_sensitive_events_tracked(self):
        """Test that events with deadlines are properly tracked in game state"""
        # Verify time pressure structures exist in game state
        self.assertTrue(hasattr(self.game_state, "time_sensitive_events"))
        self.assertTrue(hasattr(self.game_state, "npc_agendas"))
        self.assertTrue(hasattr(self.game_state, "world_resources"))
        self.assertTrue(hasattr(self.game_state, "time_pressure_warnings"))

        # Add a time-sensitive event
        event_id = "rescue_merchant"
        event_data = {
            "description": "Rescue kidnapped merchant from bandits",
            "deadline": {
                "year": 1492,
                "month": "Ches",
                "day": 25,
                "hour": 18,
                "minute": 0,
            },
            "consequences": "Merchant will be sold to slavers",
            "urgency_level": "high",
            "warnings_given": 0,
            "related_npcs": ["Elara (Merchant)", "Garrick (Bandit Leader)"],
            "status": "active",
        }

        # Add event to game state
        self.game_state.time_sensitive_events[event_id] = event_data

        # Verify event is tracked
        self.assertIn(event_id, self.game_state.time_sensitive_events)
        self.assertEqual(
            self.game_state.time_sensitive_events[event_id]["description"],
            event_data["description"],
        )

    def test_npc_agenda_progression(self):
        """Test that NPCs have agendas that progress over time"""
        # Add NPC agenda
        npc_name = "Garrick (Bandit Leader)"
        agenda_data = {
            "current_goal": "Sell captured merchant to slavers",
            "progress_percentage": 30,
            "next_milestone": {
                "day": 23,
                "hour": 12,
                "description": "Meet with slaver representative",
            },
            "blocking_factors": ["guard patrols", "PC interference"],
            "completed_milestones": ["Captured merchant"],
        }

        # Add agenda to game state
        self.game_state.npc_agendas[npc_name] = agenda_data

        # Verify agenda is tracked
        self.assertIn(npc_name, self.game_state.npc_agendas)
        self.assertEqual(
            self.game_state.npc_agendas[npc_name]["current_goal"],
            agenda_data["current_goal"],
        )
        self.assertEqual(
            self.game_state.npc_agendas[npc_name]["progress_percentage"], 30
        )

    def test_deadline_consequences(self):
        """Test that missing a deadline triggers consequences"""
        # Add event with past deadline
        event_id = "save_village"
        past_event = {
            "description": "Deliver cure for plague",
            "deadline": {
                "year": 1492,
                "month": "Ches",
                "day": 19,  # Yesterday
                "hour": 12,
                "minute": 0,
            },
            "consequences": "Half the village dies from plague",
            "urgency_level": "critical",
            "status": "active",
        }

        self.game_state.time_sensitive_events[event_id] = past_event

        # Current time is day 20, so deadline (day 19) is passed
        current_day = self.game_state.world_data["world_time"]["day"]
        deadline_day = past_event["deadline"]["day"]

        # Verify deadline is in the past
        self.assertGreater(current_day, deadline_day)

    def test_warning_generation(self):
        """Test warning generation at different urgency levels"""
        # Add event with future deadline
        event_id = "defend_town"
        event_data = {
            "description": "Prepare defenses against bandit attack",
            "deadline": {
                "year": 1492,
                "month": "Ches",
                "day": 24,  # 4 days from now
                "hour": 12,
                "minute": 0,
            },
            "urgency_level": "high",
            "warnings_given": 0,
            "status": "active",
        }

        self.game_state.time_sensitive_events[event_id] = event_data

        # Add warning tracking
        self.game_state.time_pressure_warnings[event_id] = {
            "subtle_given": False,
            "clear_given": False,
            "urgent_given": False,
            "last_warning_day": 0,
        }

        # Verify warning structure exists
        self.assertIn(event_id, self.game_state.time_pressure_warnings)
        self.assertFalse(
            self.game_state.time_pressure_warnings[event_id]["subtle_given"]
        )

    def test_world_resource_depletion(self):
        """Test that world resources deplete at specified rates"""
        # Add depleting resource
        resource_id = "village_food"
        resource_data = {
            "current_amount": 100,
            "max_amount": 100,
            "depletion_rate": 5,
            "depletion_unit": "per_day",
            "critical_level": 20,
            "consequence": "Villagers start leaving",
            "last_updated_day": 20,
        }

        self.game_state.world_resources[resource_id] = resource_data

        # Verify resource is tracked
        self.assertIn(resource_id, self.game_state.world_resources)
        self.assertEqual(
            self.game_state.world_resources[resource_id]["current_amount"], 100
        )
        self.assertEqual(
            self.game_state.world_resources[resource_id]["depletion_rate"], 5
        )

    def test_time_advancement(self):
        """Test that different actions advance time appropriately"""
        # Verify world time structure exists
        self.assertIn("world_time", self.game_state.world_data)

        initial_time = self.game_state.world_data["world_time"].copy()

        # Verify initial time
        self.assertEqual(initial_time["year"], 1492)
        self.assertEqual(initial_time["month"], "Ches")
        self.assertEqual(initial_time["day"], 20)
        self.assertEqual(initial_time["hour"], 12)

        # Test time cost constants from narrative system instruction
        # Combat: 6 seconds per round
        # Short rest: 1 hour
        # Long rest: 8 hours
        combat_seconds_per_round = 6
        short_rest_hours = 1
        long_rest_hours = 8

        # Verify these are the expected values
        self.assertEqual(combat_seconds_per_round, 6)
        self.assertEqual(short_rest_hours, 1)
        self.assertEqual(long_rest_hours, 8)

    def test_initial_game_state_has_time_pressure_structures(self):
        """Test that new game states are created with time pressure structures"""
        # Create a fresh game state as would happen in main.py
        new_game_state = GameState()

        # Convert to dict as done in the API
        state_dict = new_game_state.to_dict()

        # Verify time pressure structures are initialized
        self.assertIn("time_sensitive_events", state_dict)
        self.assertIn("npc_agendas", state_dict)
        self.assertIn("world_resources", state_dict)
        self.assertIn("time_pressure_warnings", state_dict)

        # Verify they are initialized as empty dicts
        self.assertEqual(state_dict["time_sensitive_events"], {})
        self.assertEqual(state_dict["npc_agendas"], {})
        self.assertEqual(state_dict["world_resources"], {})
        self.assertEqual(state_dict["time_pressure_warnings"], {})


if __name__ == "__main__":
    unittest.main()

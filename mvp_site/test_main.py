import unittest
from main import deep_merge

class TestDeepMerge(unittest.TestCase):

    def test_three_layer_nesting(self):
        """
        Tests deep merging with three levels of nested dictionaries.
        It should update existing values, preserve unique values, and add new keys.
        """
        destination = {
            "level1_a": {
                "level2_a": {
                    "level3_a": "original_a",
                    "level3_b": "original_b"
                },
                "level2_b": "original_2b"
            },
            "level1_b": "original_1b"
        }

        source = {
            "level1_a": {
                "level2_a": {
                    "level3_b": "updated_b",
                    "level3_c": "new_c"
                },
                "level2_c": "new_2c"
            },
            "level1_c": "new_1c"
        }

        expected = {
            "level1_a": {
                "level2_a": {
                    "level3_a": "original_a",
                    "level3_b": "updated_b",
                    "level3_c": "new_c"
                },
                "level2_b": "original_2b",
                "level2_c": "new_2c"
            },
            "level1_b": "original_1b",
            "level1_c": "new_1c"
        }

        result = deep_merge(source, destination)
        self.assertEqual(result, expected)

    def test_multiple_sequential_deep_merges(self):
        """
        Tests the effect of applying two sequential deep merges on an object.
        """
        # 1. Initial object
        game_state = {
            "player": {"hp": 100, "location": "start"},
            "world": {
                "time": "day",
                "npcs": {
                    "guard": {"state": "idle"}
                }
            }
        }

        # 2. First merge: Add a new NPC and update player HP
        update1 = {
            "player": {"hp": 90},
            "world": {
                "npcs": {
                    "merchant": {"state": "selling"}
                }
            }
        }

        # Apply first merge
        game_state = deep_merge(update1, game_state)

        expected_after_1 = {
            "player": {"hp": 90, "location": "start"},
            "world": {
                "time": "day",
                "npcs": {
                    "guard": {"state": "idle"},
                    "merchant": {"state": "selling"}
                }
            }
        }
        self.assertEqual(game_state, expected_after_1)

        # 3. Second merge: Update existing NPCs and add a world event
        update2 = {
            "world": {
                "event": "rain",
                "npcs": {
                    "guard": {"state": "patrolling"},
                    "merchant": {"state": "packing_up"}
                }
            }
        }
        
        # Apply second merge
        game_state = deep_merge(update2, game_state)

        expected_after_2 = {
            "player": {"hp": 90, "location": "start"},
            "world": {
                "time": "day",
                "event": "rain",
                "npcs": {
                    "guard": {"state": "patrolling"},
                    "merchant": {"state": "packing_up"}
                }
            }
        }
        self.assertEqual(game_state, expected_after_2)

if __name__ == '__main__':
    unittest.main() 
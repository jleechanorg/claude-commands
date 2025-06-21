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

if __name__ == '__main__':
    unittest.main() 
"""
Test both Pydantic and Simple validation approaches for comparison.
"""

import unittest
import os
import sys
import time
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestValidationComparison(unittest.TestCase):
    """Compare Pydantic vs Simple validation performance and functionality"""
    
    def setUp(self):
        """Setup test data"""
        self.sample_game_state = {
            'player_character_data': {
                'name': 'Sariel',
                'hp': 25,
                'hp_max': 30,
                'level': 3
            },
            'npc_data': {
                'Cassian': {'present': True, 'hp': 20, 'hp_max': 20},
                'Lady Cressida': {'present': True, 'location': 'Chambers'}
            },
            'location': 'Throne Room'
        }
    
    def test_simple_validation_performance(self):
        """Test Simple validation performance"""
        # Set environment to use Simple validation
        original_env = os.environ.get('USE_PYDANTIC', 'false')
        os.environ['USE_PYDANTIC'] = 'false'
        
        try:
            # Force reimport to pick up new environment
            if 'entity_tracking' in sys.modules:
                del sys.modules['entity_tracking']
            
            import entity_tracking
            
            # Performance test
            start_time = time.time()
            iterations = 100
            
            for i in range(iterations):
                manifest = entity_tracking.create_from_game_state(
                    self.sample_game_state, session_number=1, turn_number=i+1
                )
                self.assertIsNotNone(manifest)
            
            duration = time.time() - start_time
            rate = iterations / duration
            
            print(f"Simple validation: {iterations} iterations in {duration:.3f}s ({rate:.0f} ops/sec)")
            
            # Test functionality
            manifest = entity_tracking.create_from_game_state(
                self.sample_game_state, session_number=1, turn_number=1
            )
            
            self.assertEqual(entity_tracking.VALIDATION_TYPE, "Simple")
            self.assertEqual(len(manifest.player_characters), 1)
            self.assertEqual(manifest.player_characters[0].display_name, "Sariel")
            self.assertGreater(len(manifest.npcs), 0)
            
        finally:
            os.environ['USE_PYDANTIC'] = original_env
    
    def test_pydantic_validation_performance(self):
        """Test Pydantic validation performance (if available)"""
        # Set environment to use Pydantic validation
        original_env = os.environ.get('USE_PYDANTIC', 'false')
        os.environ['USE_PYDANTIC'] = 'true'
        
        try:
            # Force reimport to pick up new environment
            if 'entity_tracking' in sys.modules:
                del sys.modules['entity_tracking']
            
            import entity_tracking
            
            if "Pydantic unavailable" in entity_tracking.VALIDATION_TYPE:
                self.skipTest("Pydantic not available in this environment")
            
            # Performance test
            start_time = time.time()
            iterations = 100
            
            for i in range(iterations):
                manifest = entity_tracking.create_from_game_state(
                    self.sample_game_state, session_number=1, turn_number=i+1
                )
                self.assertIsNotNone(manifest)
            
            duration = time.time() - start_time
            rate = iterations / duration
            
            print(f"Pydantic validation: {iterations} iterations in {duration:.3f}s ({rate:.0f} ops/sec)")
            
            # Test functionality
            manifest = entity_tracking.create_from_game_state(
                self.sample_game_state, session_number=1, turn_number=1
            )
            
            self.assertEqual(entity_tracking.VALIDATION_TYPE, "Pydantic")
            self.assertEqual(len(manifest.player_characters), 1)
            self.assertEqual(manifest.player_characters[0].display_name, "Sariel")
            self.assertGreater(len(manifest.npcs), 0)
            
        finally:
            os.environ['USE_PYDANTIC'] = original_env
    
    def test_validation_switching(self):
        """Test that validation approach can be switched via environment variable"""
        # Test Simple validation
        os.environ['USE_PYDANTIC'] = 'false'
        if 'entity_tracking' in sys.modules:
            del sys.modules['entity_tracking']
        
        import entity_tracking
        info = entity_tracking.get_validation_info()
        
        self.assertEqual(info['use_pydantic'], 'False')
        self.assertIn("Simple", info['validation_type'])
        
        # Test Pydantic validation (if available)
        os.environ['USE_PYDANTIC'] = 'true'
        if 'entity_tracking' in sys.modules:
            del sys.modules['entity_tracking']
        
        import entity_tracking
        info = entity_tracking.get_validation_info()
        
        self.assertEqual(info['use_pydantic'], 'True')
        # Will be either "Pydantic" or "Simple (Pydantic unavailable)"
        self.assertTrue(
            info['validation_type'] == "Pydantic" or 
            "unavailable" in info['validation_type']
        )
    
    def test_manifest_structure_consistency(self):
        """Test that both validation approaches produce consistent manifest structure"""
        results = {}
        
        for use_pydantic in ['false', 'true']:
            os.environ['USE_PYDANTIC'] = use_pydantic
            if 'entity_tracking' in sys.modules:
                del sys.modules['entity_tracking']
            
            import entity_tracking
            
            if use_pydantic == 'true' and "unavailable" in entity_tracking.VALIDATION_TYPE:
                continue  # Skip if Pydantic not available
            
            manifest = entity_tracking.create_from_game_state(
                self.sample_game_state, session_number=1, turn_number=1
            )
            
            results[entity_tracking.VALIDATION_TYPE] = {
                'pc_count': len(manifest.player_characters),
                'npc_count': len(manifest.npcs),
                'has_expected_entities': hasattr(manifest, 'get_expected_entities'),
                'validation_type': entity_tracking.VALIDATION_TYPE
            }
        
        print(f"Validation comparison results: {results}")
        
        # If we have both results, compare them
        if len(results) == 2:
            simple_result = results.get("Simple")
            pydantic_result = results.get("Pydantic")
            
            if simple_result and pydantic_result:
                self.assertEqual(simple_result['pc_count'], pydantic_result['pc_count'])
                self.assertEqual(simple_result['npc_count'], pydantic_result['npc_count'])
                self.assertEqual(simple_result['has_expected_entities'], pydantic_result['has_expected_entities'])
    
    def test_error_handling_comparison(self):
        """Test error handling differences between validation approaches"""
        invalid_game_state = {
            'player_character_data': {
                'name': 'Sariel',
                'hp': -5,  # Invalid negative HP
                'hp_max': 30
            }
        }
        
        for use_pydantic in ['false', 'true']:
            os.environ['USE_PYDANTIC'] = use_pydantic
            if 'entity_tracking' in sys.modules:
                del sys.modules['entity_tracking']
            
            import entity_tracking
            
            if use_pydantic == 'true' and "unavailable" in entity_tracking.VALIDATION_TYPE:
                continue
            
            try:
                manifest = entity_tracking.create_from_game_state(
                    invalid_game_state, session_number=1, turn_number=1
                )
                print(f"{entity_tracking.VALIDATION_TYPE}: Handled invalid data gracefully")
            except Exception as e:
                print(f"{entity_tracking.VALIDATION_TYPE}: Raised {type(e).__name__}: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
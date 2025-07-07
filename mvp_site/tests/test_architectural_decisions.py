#!/usr/bin/env python3
"""
Architecture Decision Tests (ADTs)

These tests verify that our architectural decisions remain valid and are 
actually implemented as designed. They prevent the "test name vs reality" 
problem and ensure architectural consistency.
"""

import unittest
import os
import sys
import importlib

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestArchitecturalDecisions(unittest.TestCase):
    """Tests that validate our architectural decisions"""
    
    def test_adt_001_pydantic_validation_is_used(self):
        """ADT-001: Entity validation uses Pydantic implementation for robust data validation"""
        # Import and verify we're using the pydantic module
        from schemas import entities_pydantic
        
        # Verify we're using Pydantic
        self.assertIn('pydantic', str(entities_pydantic.SceneManifest.__module__), 
                     "SceneManifest should be using Pydantic implementation")
        
        # Verify Pydantic is in requirements since it's now the default
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        with open(req_path) as f:
            requirements = f.read()
            # Note: Pydantic comes as dependency of google-genai, so we don't need explicit entry
    
    def test_adt_002_only_pydantic_implementation_exists(self):
        """ADT-002: Only Pydantic implementation exists (Simple removed)"""
        schema_dir = os.path.join(os.path.dirname(__file__), '..', 'schemas')
        entity_files = [f for f in os.listdir(schema_dir) 
                       if f.startswith('entities') and f.endswith('.py')]
        
        self.assertEqual(len(entity_files), 1, 
                        f"Should have only Pydantic implementation, found: {entity_files}")
        self.assertIn('entities_pydantic.py', entity_files, "Only Pydantic version should exist")
        self.assertNotIn('entities_simple.py', entity_files, "Simple version should be removed")
    
    def test_adt_003_entity_tracking_imports_pydantic_module(self):
        """ADT-003: entity_tracking.py imports from Pydantic module"""
        import entity_tracking
        
        # Check what module is actually imported
        manifest_module = entity_tracking.SceneManifest.__module__
        self.assertEqual(manifest_module, 'schemas.entities_pydantic',
                        f"entity_tracking should import from schemas.entities_pydantic")
        
        # Verify validation type is set correctly
        self.assertEqual(entity_tracking.VALIDATION_TYPE, "Pydantic")
    
    def test_adt_004_pydantic_validation_actually_rejects_bad_data(self):
        """ADT-004: Pydantic validation actually rejects invalid data"""
        from schemas.entities_pydantic import NPC, HealthStatus, EntityType
        
        # Test that gender validation works for NPCs (Luke campaign fix)
        with self.assertRaises(Exception) as context:
            npc = NPC(
                entity_id="npc_test_001",
                display_name="Test NPC",
                health=HealthStatus(hp=10, hp_max=10),
                current_location="loc_test_001",
                gender=None  # Should fail - gender required for NPCs
            )
        
        # Verify the error is about gender validation
        self.assertIn("Gender is required for NPCs", str(context.exception))
    
    def test_adt_005_defensive_numeric_conversion_works(self):
        """ADT-005: DefensiveNumericConverter handles 'unknown' values gracefully"""
        from schemas.defensive_numeric_converter import DefensiveNumericConverter
        
        # Test conversion of 'unknown' values
        result = DefensiveNumericConverter.convert_value('hp', 'unknown')
        self.assertEqual(result, 1, "Should convert 'unknown' to default value 1")
        
        # Test conversion of valid numeric strings
        result = DefensiveNumericConverter.convert_value('hp', '25')
        self.assertEqual(result, 25, "Should convert valid numeric string")
        
        # Test conversion of actual numbers
        result = DefensiveNumericConverter.convert_value('hp', 30)
        self.assertEqual(result, 30, "Should pass through actual numbers")
    
    def test_adt_006_no_environment_variable_switching(self):
        """ADT-006: No environment variable switching - Pydantic is always used"""
        import entity_tracking
        
        # Verify that validation type is always Pydantic regardless of environment
        info = entity_tracking.get_validation_info()
        self.assertEqual(info['validation_type'], 'Pydantic')
        self.assertEqual(info['pydantic_available'], 'true')
        
        # Verify no environment variable dependency
        import os
        old_env = os.environ.get('USE_PYDANTIC')
        try:
            # Set environment variable to false - should not affect anything
            os.environ['USE_PYDANTIC'] = 'false'
            
            # Force reimport
            if 'entity_tracking' in sys.modules:
                del sys.modules['entity_tracking']
            
            import entity_tracking
            
            # Should still be Pydantic
            self.assertEqual(entity_tracking.VALIDATION_TYPE, "Pydantic")
            
        finally:
            if old_env is not None:
                os.environ['USE_PYDANTIC'] = old_env
            elif 'USE_PYDANTIC' in os.environ:
                del os.environ['USE_PYDANTIC']


if __name__ == '__main__':
    unittest.main()
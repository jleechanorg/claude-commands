#!/usr/bin/env python3
"""
Architecture Decision Tests (ADTs)

These tests verify that our architectural decisions remain valid and are 
actually implemented as designed. They prevent the "test name vs reality" 
problem that led to the Pydantic validation failure.
"""

import unittest
import os
import sys
import importlib

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestArchitecturalDecisions(unittest.TestCase):
    """Tests that validate our architectural decisions"""
    
    def test_adt_001_simple_validation_is_used(self):
        """ADT-001: Entity validation uses Simple implementation (until Pydantic properly tested)"""
        # Import and verify we're using the simple module
        from schemas import entities_simple
        
        # Verify we're NOT accidentally using Pydantic
        self.assertNotIn('pydantic', str(entities_simple.SceneManifest.__module__), 
                     "SceneManifest should be using Simple implementation")
        
        # Verify Pydantic is NOT in requirements (until properly tested)
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        with open(req_path) as f:
            requirements = f.read()
            self.assertNotIn('pydantic', requirements, 
                         "Pydantic should not be in requirements.txt until properly tested")
    
    def test_adt_002_both_entity_implementations_exist_temporarily(self):
        """ADT-002: Both implementations exist until proper testing complete"""
        # During transition, we have both files
        schema_dir = os.path.join(os.path.dirname(__file__), '..', 'schemas')
        entity_files = [f for f in os.listdir(schema_dir) 
                       if f.startswith('entities') and f.endswith('.py')]
        
        self.assertEqual(len(entity_files), 2, 
                        f"Should have both implementations during testing phase, found: {entity_files}")
        self.assertIn('entities_pydantic.py', entity_files, "Pydantic version for testing")
        self.assertIn('entities_simple.py', entity_files, "Simple version in use")
    
    def test_adt_003_entity_tracking_imports_simple_module(self):
        """ADT-003: entity_tracking.py imports from Simple module (current implementation)"""
        import entity_tracking
        
        # Check what module is actually imported
        manifest_module = entity_tracking.SceneManifest.__module__
        self.assertEqual(manifest_module, 'schemas.entities_simple',
                        f"entity_tracking should import from schemas.entities_simple until Pydantic is tested")
    
    def test_adt_004_simple_validation_actually_rejects_bad_data(self):
        """ADT-004: Simple validation actually rejects malformed data"""
        from schemas.entities_simple import SceneManifest, Location
        
        # Test that bad scene_id format is rejected
        with self.assertRaises(ValueError) as context:
            location = Location(
                entity_id="bad_format",  # Should be loc_XXX_XXX
                display_name="Test Location"
            )
        
        # Verify the error mentions the format
        self.assertIn('Invalid location ID format', str(context.exception))
    
    def test_adt_005_test_verification_example(self):
        """ADT-005: Example of proper test verification"""
        # This shows how every test should verify what it's testing
        
        # Log what we're actually testing
        import schemas.entities_simple as test_module
        
        verification = {
            "module_name": test_module.__name__,
            "module_file": test_module.__file__,
            "has_pydantic": 'pydantic' in test_module.__file__,
            "scene_manifest_bases": str(test_module.SceneManifest.__bases__),
            "has_validation": hasattr(test_module.SceneManifest, '__pydantic_model__')
        }
        
        print(f"\nTEST VERIFICATION: {self._testMethodName}")
        for key, value in verification.items():
            print(f"  {key}: {value}")
        
        # Should be false for Simple implementation
        self.assertFalse(verification['has_pydantic'])
        self.assertFalse(verification['has_validation'])


class TestDependencyManagement(unittest.TestCase):
    """Tests that verify dependencies match imports"""
    
    def test_all_imported_packages_in_requirements(self):
        """All packages imported in code should be in requirements.txt"""
        # This is a simplified example - a real version would scan all .py files
        
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        with open(req_path) as f:
            requirements = f.read().lower()
        
        # Key packages we know are used
        critical_packages = [
            # ('pydantic', 'schemas/entities_pydantic.py uses Pydantic'),  # Not yet - pending testing
            ('firebase-admin', 'firestore_service.py uses Firebase'),
            ('google-genai', 'gemini_service.py uses Gemini SDK'),
        ]
        
        for package, reason in critical_packages:
            self.assertIn(package.lower(), requirements,
                         f"{package} must be in requirements.txt - {reason}")


if __name__ == '__main__':
    # Run with verbose output to show test verification
    unittest.main(verbosity=2)
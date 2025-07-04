#!/usr/bin/env python3
"""
Integration tests for world_loader.py using the actual implementation.
"""

import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the actual world_loader
import world_loader


class TestWorldLoaderIntegration(unittest.TestCase):
    """Integration tests for world_loader with actual implementation."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Save original WORLD_DIR value
        self.original_world_dir = world_loader.WORLD_DIR
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
        
        # Restore original WORLD_DIR
        world_loader.WORLD_DIR = self.original_world_dir
        if world_loader.WORLD_DIR.startswith(".."):
            world_loader.CELESTIAL_WARS_BOOK_PATH = os.path.join(world_loader.WORLD_DIR, "celestial_wars_alexiel_book.md")
            world_loader.WORLD_ASSIAH_PATH = os.path.join(world_loader.WORLD_DIR, "world_assiah.md")
    
    def test_actual_development_path_detection(self):
        """Test actual world_loader behavior in development scenario."""
        # Check what WORLD_DIR is actually set to
        if os.path.exists(os.path.join(os.path.dirname(world_loader.__file__), "world")):
            # Local world exists (might be from deploy script copy)
            self.assertEqual(world_loader.WORLD_DIR, "world")
            self.assertIn("world/", world_loader.CELESTIAL_WARS_BOOK_PATH)
        else:
            # In pure development, WORLD_DIR should be ../world
            self.assertEqual(world_loader.WORLD_DIR, "../world")
            self.assertIn("../world", world_loader.CELESTIAL_WARS_BOOK_PATH)
    
    @patch('os.path.exists')
    def test_production_path_detection_simulation(self, mock_exists):
        """Simulate production environment where world/ exists locally."""
        # Mock that world directory exists in current directory
        def exists_side_effect(path):
            if path.endswith("world") and not ".." in path:
                return True
            return False
        
        mock_exists.side_effect = exists_side_effect
        
        # Reload the module to trigger path detection with mock
        import importlib
        importlib.reload(world_loader)
        
        # In production simulation, WORLD_DIR should be "world"
        self.assertEqual(world_loader.WORLD_DIR, "world")
    
    def test_path_construction_with_real_logic(self):
        """Test the actual path construction logic in world_loader."""
        # Create test directories
        app_dir = os.path.join(self.test_dir, "app")
        os.makedirs(app_dir)
        
        # Test development scenario (../world)
        parent_world = os.path.join(self.test_dir, "world")
        os.makedirs(parent_world)
        
        # Create test files
        with open(os.path.join(parent_world, "celestial_wars_alexiel_book.md"), "w") as f:
            f.write("Test book content")
        with open(os.path.join(parent_world, "world_assiah.md"), "w") as f:
            f.write("Test world content")
        
        # Change to app directory
        os.chdir(app_dir)
        
        # Mock the module's __file__ to be in app_dir
        with patch.object(world_loader, '__file__', os.path.join(app_dir, 'world_loader.py')):
            # Test with WORLD_DIR = "../world"
            world_loader.WORLD_DIR = "../world"
            world_loader.CELESTIAL_WARS_BOOK_PATH = os.path.join(world_loader.WORLD_DIR, "celestial_wars_alexiel_book.md")
            world_loader.WORLD_ASSIAH_PATH = os.path.join(world_loader.WORLD_DIR, "world_assiah.md")
            
            # Should load successfully
            result = world_loader.load_world_content_for_system_instruction()
            self.assertIn("Test book content", result)
            self.assertIn("Test world content", result)
    
    def test_production_scenario_with_copied_files(self):
        """Test production scenario where files are copied to local world/."""
        # Create app directory with local world
        app_dir = os.path.join(self.test_dir, "app")
        local_world = os.path.join(app_dir, "world")
        os.makedirs(local_world)
        
        # Create test files in local world
        with open(os.path.join(local_world, "celestial_wars_alexiel_book.md"), "w") as f:
            f.write("Production book content")
        with open(os.path.join(local_world, "world_assiah.md"), "w") as f:
            f.write("Production world content")
        
        # Change to app directory
        os.chdir(app_dir)
        
        # Mock the module's __file__ to be in app_dir
        with patch.object(world_loader, '__file__', os.path.join(app_dir, 'world_loader.py')):
            # Test with WORLD_DIR = "world"
            world_loader.WORLD_DIR = "world"
            world_loader.CELESTIAL_WARS_BOOK_PATH = os.path.join(world_loader.WORLD_DIR, "celestial_wars_alexiel_book.md")
            world_loader.WORLD_ASSIAH_PATH = os.path.join(world_loader.WORLD_DIR, "world_assiah.md")
            
            # Should load successfully from local directory
            result = world_loader.load_world_content_for_system_instruction()
            self.assertIn("Production book content", result)
            self.assertIn("Production world content", result)
    
    def test_error_path_in_logs(self):
        """Test that error messages include the actual path attempted."""
        # Change to a directory with no world files
        os.chdir(self.test_dir)
        
        with patch.object(world_loader, '__file__', os.path.join(self.test_dir, 'world_loader.py')):
            # Force WORLD_DIR to a non-existent path
            world_loader.WORLD_DIR = "../nonexistent"
            world_loader.CELESTIAL_WARS_BOOK_PATH = os.path.join(world_loader.WORLD_DIR, "celestial_wars_alexiel_book.md")
            world_loader.WORLD_ASSIAH_PATH = os.path.join(world_loader.WORLD_DIR, "world_assiah.md")
            
            # Should raise FileNotFoundError with path info
            with self.assertRaises(FileNotFoundError) as context:
                world_loader.load_world_content_for_system_instruction()
            
            # Error should mention the path
            error_msg = str(context.exception)
            self.assertTrue("nonexistent" in error_msg or "No such file" in error_msg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
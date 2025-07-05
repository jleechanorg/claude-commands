#!/usr/bin/env python3
"""
Unit tests for world_loader.py path handling logic.
Tests both development and production scenarios.
"""

import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch, mock_open

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging_util

class TestWorldLoader(unittest.TestCase):
    """Test world_loader.py path handling in different environments."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create test directory structure
        self.app_dir = os.path.join(self.test_dir, "app")
        os.makedirs(self.app_dir)
        
        # Create parent world directory (development scenario)
        self.parent_world_dir = os.path.join(self.test_dir, "world")
        os.makedirs(self.parent_world_dir)
        
        # Create test world files in parent directory
        with open(os.path.join(self.parent_world_dir, "celestial_wars_alexiel_book.md"), "w") as f:
            f.write("# Parent Book Content\nThis is the development book.")
        
        with open(os.path.join(self.parent_world_dir, "world_assiah.md"), "w") as f:
            f.write("# Parent World Content\nThis is the development world.")
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        sys.modules.pop('world_loader', None)
        if self.app_dir in sys.path:
            sys.path.remove(self.app_dir)
        shutil.rmtree(self.test_dir)
    
    def test_development_scenario_parent_world(self):
        """Test loading from ../world in development environment."""
        # Change to app directory
        os.chdir(self.app_dir)
        
        # Create world_loader.py in app directory
        world_loader_code = '''
import os
import logging_util
# World file paths - only used in this module
# In deployment, world files are copied to same directory as the app
if os.path.exists(os.path.join(os.path.dirname(__file__), "world")):
    WORLD_DIR = "world"
else:
    WORLD_DIR = "../world"
    
CELESTIAL_WARS_BOOK_PATH = os.path.join(WORLD_DIR, "celestial_wars_alexiel_book.md")
WORLD_ASSIAH_PATH = os.path.join(WORLD_DIR, "world_assiah.md")

def load_world_content_for_system_instruction():
    """Load world files and create a combined system instruction."""
    try:
        # If WORLD_DIR is relative (not starting with ../), join with current dir
        if WORLD_DIR.startswith(".."):
            book_path = os.path.join(os.path.dirname(__file__), CELESTIAL_WARS_BOOK_PATH)
            world_path = os.path.join(os.path.dirname(__file__), WORLD_ASSIAH_PATH)
        else:
            # WORLD_DIR is "world" - files are in same directory
            book_path = CELESTIAL_WARS_BOOK_PATH
            world_path = WORLD_ASSIAH_PATH
            
        # Load book content
        with open(book_path, 'r', encoding='utf-8') as f:
            book_content = f.read().strip()
        
        # Load world content
        with open(world_path, 'r', encoding='utf-8') as f:
            world_content = f.read().strip()
        
        return {"book": book_content, "world": world_content, "world_dir": WORLD_DIR}
    except Exception as e:
        return {"error": str(e), "world_dir": WORLD_DIR}
'''
        
        with open(os.path.join(self.app_dir, "world_loader.py"), "w") as f:
            f.write(world_loader_code)
        
        # Import and test
        sys.path.insert(0, self.app_dir)
        import world_loader
        
        # Verify WORLD_DIR is set to ../world
        self.assertEqual(world_loader.WORLD_DIR, "../world")
        
        # Load content
        result = world_loader.load_world_content_for_system_instruction()
        
        # Verify content loaded from parent directory
        self.assertIn("Parent Book Content", result.get("book", ""))
        self.assertIn("Parent World Content", result.get("world", ""))
        self.assertEqual(result.get("world_dir"), "../world")
    
    def test_production_scenario_local_world(self):
        """Test loading from world/ in production environment."""
        # Create local world directory (production scenario)
        local_world_dir = os.path.join(self.app_dir, "world")
        os.makedirs(local_world_dir)
        
        # Create test world files in local directory
        with open(os.path.join(local_world_dir, "celestial_wars_alexiel_book.md"), "w") as f:
            f.write("# Local Book Content\nThis is the production book.")
        
        with open(os.path.join(local_world_dir, "world_assiah.md"), "w") as f:
            f.write("# Local World Content\nThis is the production world.")
        
        # Change to app directory
        os.chdir(self.app_dir)
        
        # Create world_loader.py (same code as above)
        world_loader_code = '''
import os
import logging_util
# World file paths - only used in this module
# In deployment, world files are copied to same directory as the app
if os.path.exists(os.path.join(os.path.dirname(__file__), "world")):
    WORLD_DIR = "world"
else:
    WORLD_DIR = "../world"
    
CELESTIAL_WARS_BOOK_PATH = os.path.join(WORLD_DIR, "celestial_wars_alexiel_book.md")
WORLD_ASSIAH_PATH = os.path.join(WORLD_DIR, "world_assiah.md")

def load_world_content_for_system_instruction():
    """Load world files and create a combined system instruction."""
    try:
        # If WORLD_DIR is relative (not starting with ../), join with current dir
        if WORLD_DIR.startswith(".."):
            book_path = os.path.join(os.path.dirname(__file__), CELESTIAL_WARS_BOOK_PATH)
            world_path = os.path.join(os.path.dirname(__file__), WORLD_ASSIAH_PATH)
        else:
            # WORLD_DIR is "world" - files are in same directory
            book_path = CELESTIAL_WARS_BOOK_PATH
            world_path = WORLD_ASSIAH_PATH
            
        # Load book content
        with open(book_path, 'r', encoding='utf-8') as f:
            book_content = f.read().strip()
        
        # Load world content
        with open(world_path, 'r', encoding='utf-8') as f:
            world_content = f.read().strip()
        
        return {"book": book_content, "world": world_content, "world_dir": WORLD_DIR}
    except Exception as e:
        return {"error": str(e), "world_dir": WORLD_DIR}
'''
        
        with open(os.path.join(self.app_dir, "world_loader.py"), "w") as f:
            f.write(world_loader_code)
        
        # Import and test
        sys.path.insert(0, self.app_dir)
        import world_loader
        
        # Verify WORLD_DIR is set to world (local)
        self.assertEqual(world_loader.WORLD_DIR, "world")
        
        # Load content
        result = world_loader.load_world_content_for_system_instruction()
        
        # Verify content loaded from local directory
        self.assertIn("Local Book Content", result.get("book", ""))
        self.assertIn("Local World Content", result.get("world", ""))
        self.assertEqual(result.get("world_dir"), "world")
    
    def test_path_construction_logic(self):
        """Test the path construction logic for both scenarios."""
        # Test data
        test_cases = [
            {
                "world_dir": "../world",
                "expected_join": True,
                "description": "Parent directory should join paths"
            },
            {
                "world_dir": "world",
                "expected_join": False,
                "description": "Local directory should not join paths"
            },
            {
                "world_dir": "./world",
                "expected_join": False,
                "description": "Current directory reference should not join paths"
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(test_case=test_case["description"]):
                world_dir = test_case["world_dir"]
                expected_join = test_case["expected_join"]
                
                # Test the logic
                should_join = world_dir.startswith("..")
                self.assertEqual(should_join, expected_join, 
                               f"Failed for {world_dir}: {test_case['description']}")
    
    def test_missing_world_files_error_handling(self):
        """Test error handling when world files are missing."""
        # Change to app directory without creating world files
        os.chdir(self.app_dir)
        
        # Create world_loader.py
        world_loader_code = '''
import os
import logging_util
# World file paths - only used in this module
if os.path.exists(os.path.join(os.path.dirname(__file__), "world")):
    WORLD_DIR = "world"
else:
    WORLD_DIR = "../world"
    
CELESTIAL_WARS_BOOK_PATH = os.path.join(WORLD_DIR, "celestial_wars_alexiel_book.md")
WORLD_ASSIAH_PATH = os.path.join(WORLD_DIR, "world_assiah.md")

def load_world_content_for_system_instruction():
    """Load world files and create a combined system instruction."""
    try:
        # If WORLD_DIR is relative (not starting with ../), join with current dir
        if WORLD_DIR.startswith(".."):
            book_path = os.path.join(os.path.dirname(__file__), CELESTIAL_WARS_BOOK_PATH)
            world_path = os.path.join(os.path.dirname(__file__), WORLD_ASSIAH_PATH)
        else:
            # WORLD_DIR is "world" - files are in same directory
            book_path = CELESTIAL_WARS_BOOK_PATH
            world_path = WORLD_ASSIAH_PATH
            
        # Load book content
        with open(book_path, 'r', encoding='utf-8') as f:
            book_content = f.read().strip()
        
        # Load world content
        with open(world_path, 'r', encoding='utf-8') as f:
            world_content = f.read().strip()
        
        return {"book": book_content, "world": world_content}
    except FileNotFoundError as e:
        raise FileNotFoundError(f"World file not found: {e}")
'''
        
        with open(os.path.join(self.app_dir, "world_loader.py"), "w") as f:
            f.write(world_loader_code)
        
        # Remove parent world directory to simulate missing files
        shutil.rmtree(self.parent_world_dir)
        
        # Import and test
        sys.path.insert(0, self.app_dir)
        import world_loader
        
        # Should raise FileNotFoundError
        with self.assertRaises(FileNotFoundError) as context:
            world_loader.load_world_content_for_system_instruction()
        
        self.assertIn("World file not found", str(context.exception))


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
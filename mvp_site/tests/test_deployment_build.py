#!/usr/bin/env python3
"""
Test to verify world files are accessible in deployment context.
This simulates the Docker build environment to catch deployment issues early.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add mvp_site directory to path for imports
# Handle both running from project root and from mvp_site directory
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.basename(current_dir) == 'mvp_site':
    # Already in mvp_site directory
    sys.path.insert(0, current_dir)
else:
    # Running from project root
    sys.path.insert(0, os.path.join(current_dir, 'mvp_site'))

import world_loader


class TestDeploymentBuild(unittest.TestCase):
    """Test deployment build context and file accessibility."""

    def setUp(self):
        """Create a temporary directory structure mimicking deployment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # Create mvp_site directory structure
        self.mvp_site_dir = os.path.join(self.test_dir, "mvp_site")
        os.makedirs(self.mvp_site_dir)

        # Create a minimal logging_util.py for the test
        logging_util_content = """
import logging

def info(message, *args, **kwargs):
    logging.info(message, *args, **kwargs)

def error(message, *args, **kwargs):
    logging.error(message, *args, **kwargs)

def warning(message, *args, **kwargs):
    logging.warning(message, *args, **kwargs)
"""

        with open(os.path.join(self.mvp_site_dir, "logging_util.py"), "w") as f:
            f.write(logging_util_content)

        # Create a minimal world_loader.py that mimics the real one
        world_loader_content = '''
import os
WORLD_DIR = "../world"
CELESTIAL_WARS_BOOK_PATH = os.path.join(WORLD_DIR, "celestial_wars_alexiel_book.md")
WORLD_ASSIAH_PATH = os.path.join(WORLD_DIR, "world_assiah.md")

def load_world_content_for_system_instruction():
    """Load world files and create a combined system instruction."""
    try:
        # Load book content
        book_path = os.path.join(os.path.dirname(__file__), CELESTIAL_WARS_BOOK_PATH)
        with open(book_path, 'r', encoding='utf-8') as f:
            book_content = f.read().strip()
        
        # Load world content
        world_path = os.path.join(os.path.dirname(__file__), WORLD_ASSIAH_PATH)
        with open(world_path, 'r', encoding='utf-8') as f:
            world_content = f.read().strip()
        
        return f"Book: {len(book_content)} chars, World: {len(world_content)} chars"
    except FileNotFoundError as e:
        raise FileNotFoundError(f"World file not found: {e}")
'''

        with open(os.path.join(self.mvp_site_dir, "world_loader.py"), "w") as f:
            f.write(world_loader_content)

    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_world_files_not_accessible_without_copy(self):
        """Test that world files are NOT accessible without copying (reproduces the bug)."""
        # Change to mvp_site directory (simulating Docker build context)
        os.chdir(self.mvp_site_dir)

        # Import should work
        sys.path.insert(0, self.mvp_site_dir)
        try:


            # But loading should fail
            with self.assertRaises(FileNotFoundError) as context:
                world_loader.load_world_content_for_system_instruction()

            self.assertIn("World file not found", str(context.exception))
        finally:
            sys.path.remove(self.mvp_site_dir)

    def test_world_files_accessible_after_copy(self):
        """Test that world files ARE accessible after copying (verifies the fix)."""
        # Create world directory at project root
        world_dir = os.path.join(self.test_dir, "world")
        os.makedirs(world_dir)

        # Create test world files
        with open(os.path.join(world_dir, "celestial_wars_alexiel_book.md"), "w") as f:
            f.write("# Test Celestial Wars Book\nThis is test content.")

        with open(os.path.join(world_dir, "world_assiah.md"), "w") as f:
            f.write("# Test World of Assiah\nThis is test world content.")

        # Simulate the deploy.sh copy operation
        dest_world_dir = os.path.join(self.mvp_site_dir, "world")
        shutil.copytree(world_dir, dest_world_dir)

        # Change to mvp_site directory (simulating Docker build context)
        os.chdir(self.mvp_site_dir)

        # Import and test
        sys.path.insert(0, self.mvp_site_dir)
        try:


            # Loading should now work
            result = world_loader.load_world_content_for_system_instruction()

            # Verify content was loaded
            self.assertIn("Book:", result)
            self.assertIn("World:", result)
            self.assertIn("chars", result)

            # Verify world files exist in the copied location
            self.assertTrue(os.path.exists("world/celestial_wars_alexiel_book.md"))
            self.assertTrue(os.path.exists("world/world_assiah.md"))

        finally:
            sys.path.remove(self.mvp_site_dir)

    def test_deploy_script_simulation(self):
        """Simulate the deploy.sh script behavior."""
        # Create world directory at project root
        world_dir = os.path.join(self.test_dir, "world")
        os.makedirs(world_dir)

        # Create test world files
        Path(world_dir, "celestial_wars_alexiel_book.md").touch()
        Path(world_dir, "world_assiah.md").touch()

        # Change to project root
        os.chdir(self.test_dir)

        # Simulate deploy.sh logic
        TARGET_DIR = "mvp_site"

        # This is the key line from deploy.sh
        if TARGET_DIR == "mvp_site" and os.path.isdir("world"):
            shutil.copytree("world", os.path.join(TARGET_DIR, "world"))

        # Verify the copy worked
        self.assertTrue(os.path.exists("mvp_site/world/celestial_wars_alexiel_book.md"))
        self.assertTrue(os.path.exists("mvp_site/world/world_assiah.md"))


if __name__ == "__main__":
    unittest.main()

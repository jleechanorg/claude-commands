#!/usr/bin/env python3
"""
Test to verify world files are accessible in deployment context.
This simulates the Docker build environment to catch deployment issues early.
"""

import importlib
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

# Add mvp_site directory to path for imports
# Handle both running from project root and from mvp_site directory
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.basename(current_dir) == "mvp_site":
    # Already in mvp_site directory
    sys.path.insert(0, current_dir)
else:
    # Running from project root
    sys.path.insert(0, os.path.join(current_dir))


class TestDeploymentBuild(unittest.TestCase):
    """Test deployment build context and file accessibility."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # Create mvp_site directory structure in test_dir
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

        # Create a dummy world_loader.py in the test mvp_site directory
        # This world_loader will look for world files relative to itself
        world_loader_content = """
import os
import logging_util

def load_world_content_for_system_instruction():
    # Use path relative to this file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    world_dir = os.path.join(base_dir, "world")
    
    world_file = os.path.join(world_dir, "world_assiah.md")
    logging_util.info(f"Looking for world content at: {world_file}")
    
    if not os.path.exists(world_file):
        raise FileNotFoundError(f"World file not found: {world_file}")
        
    with open(world_file, "r") as f:
        return f.read()
"""
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

        # Import should work - use direct import since we're in mvp_site directory
        sys.path.insert(0, self.mvp_site_dir)
        # Ensure world_loader is not in sys.modules to force a fresh import from self.mvp_site_dir
        if "world_loader" in sys.modules:
            del sys.modules["world_loader"]
        try:
            world_loader = importlib.import_module("world_loader")

            # But loading should fail
            with pytest.raises(FileNotFoundError) as context:
                world_loader.load_world_content_for_system_instruction()

            assert "World file not found" in str(context.value)
        finally:
            if self.mvp_site_dir in sys.path:
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

        # Import and test - use direct import since we're in mvp_site directory
        sys.path.insert(0, self.mvp_site_dir)
        # Ensure world_loader is not in sys.modules to force a fresh import from self.mvp_site_dir
        if "world_loader" in sys.modules:
            del sys.modules["world_loader"]
        try:
            world_loader = importlib.import_module("world_loader")

            # Loading should now work
            result = world_loader.load_world_content_for_system_instruction()

            # Verify content was loaded successfully
            assert result is not None
            assert len(result) > 0
            # Check for actual world content markers instead of mock format
            assert any(
                marker in result
                for marker in ["World", "WORLD", "Campaign", "CAMPAIGN"]
            )

            # Verify world files exist in the copied location
            assert os.path.exists("world/celestial_wars_alexiel_book.md")
            assert os.path.exists("world/world_assiah.md")

        finally:
            if self.mvp_site_dir in sys.path:
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
        target_dir = "mvp_site"

        # This is the key line from deploy.sh
        if target_dir == "mvp_site" and os.path.isdir("world"):
            shutil.copytree("world", os.path.join(target_dir, "world"))

        # Verify the copy worked
        assert os.path.exists("mvp_site/world/celestial_wars_alexiel_book.md")
        assert os.path.exists("mvp_site/world/world_assiah.md")


if __name__ == "__main__":
    unittest.main()

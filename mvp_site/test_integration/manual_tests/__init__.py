"""
Manual tests package initialization.

This module sets up the Python path to allow imports from the mvp_site package
without using sys.path.insert() in individual test files.
"""

import os
import sys

# Get the mvp_site directory (two levels up from this file)
MVP_SITE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Add to Python path if not already there
if MVP_SITE_DIR not in sys.path:
    sys.path.insert(0, MVP_SITE_DIR)

# Also add the project root (parent of mvp_site) for any project-level imports
PROJECT_ROOT = os.path.dirname(MVP_SITE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

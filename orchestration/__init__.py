"""
Orchestration System Package

Multi-agent orchestration and task dispatch system for WorldArchitect.AI
"""

import os
import sys

# Ensure current directory is in path for module imports
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

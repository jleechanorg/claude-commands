#!/usr/bin/env python3
"""
Standalone Flask app starter for run_ui_tests.sh
This resolves import path issues when running in subshells.
"""

import os
import sys

# Add current directory to Python path (we're already in mvp_site)
sys.path.insert(0, os.path.dirname(__file__))

# Import and run Flask app
from main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8088))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)

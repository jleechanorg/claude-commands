#!/usr/bin/env python3
"""
/orch - Orchestration Command (alias for /orchestrate)

Simple wrapper that delegates to orchestrate.py
"""

import sys
import os
import subprocess

# Get the path to orchestrate.py
script_dir = os.path.dirname(os.path.abspath(__file__))
orchestrate_path = os.path.join(script_dir, 'orchestrate.py')

# Execute orchestrate.py with all arguments
if __name__ == "__main__":
    try:
        # Pass all command line arguments to orchestrate.py
        result = subprocess.run([sys.executable, orchestrate_path] + sys.argv[1:], 
                              capture_output=False, text=True)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error running orchestrate: {e}")
        sys.exit(1)
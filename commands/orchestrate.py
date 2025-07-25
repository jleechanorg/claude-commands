#!/usr/bin/env python3
"""
/orchestrate - Unified Orchestration System
Redirects to the mature orchestration/ directory system enhanced with LLM intelligence

This ensures we use the single, unified orchestration system instead of parallel implementations.
"""

import os
import subprocess
import sys

def main():
    """Redirect to unified orchestration system."""
    if len(sys.argv) < 2:
        print("Usage: /orchestrate [task description]")
        print("Example: /orchestrate Find security vulnerabilities and create coverage report")
        return 1
    
    # Find orchestration directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    orchestration_dir = os.path.join(project_root, "orchestration")
    unified_script = os.path.join(orchestration_dir, "orchestrate_unified.py")
    
    if not os.path.exists(unified_script):
        print(f"❌ Unified orchestration script not found: {unified_script}")
        return 1
    
    # Redirect to unified system
    task_args = sys.argv[1:]
    
    try:
        result = subprocess.run([
            sys.executable, unified_script
        ] + task_args, cwd=project_root)
        return result.returncode
    except Exception as e:
        print(f"❌ Failed to launch unified orchestration: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
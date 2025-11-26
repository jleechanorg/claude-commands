"""
Pytest configuration for jleechanorg_pr_automation tests.
Sets up proper Python path for package imports.
"""
import sys
from pathlib import Path

# Add project root to sys.path so package imports work without editable install
package_dir = Path(__file__).parent.parent
project_root = package_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

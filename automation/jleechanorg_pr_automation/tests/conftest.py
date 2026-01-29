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


def _get_inflight_count(data: dict, pr_key: str) -> int:
    value = data.get(pr_key, 0)
    if isinstance(value, dict):
        return int(value.get("count", 0))
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

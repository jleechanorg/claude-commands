import pytest
from pathlib import Path
from typing import Optional

import jleechanorg_pr_automation
from jleechanorg_pr_automation import _version_from_pyproject

def test_package_version_matches_pyproject():
    """
    Keep package version declarations consistent.

    Cursor/Copilot bots frequently flag mismatches between:
    - automation/pyproject.toml [project].version
    - automation/jleechanorg_pr_automation/__init__.py __version__
    """
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if not pyproject_path.exists():
        pytest.skip(f"pyproject not found at {pyproject_path}")

    pyproject_version = _version_from_pyproject(pyproject_path)
    if pyproject_version is None:
        pytest.fail(f"Unable to parse [project].version from {pyproject_path}")
    assert jleechanorg_pr_automation.__version__ == pyproject_version

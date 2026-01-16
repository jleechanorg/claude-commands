import pytest
import re
from pathlib import Path
from typing import Optional

import jleechanorg_pr_automation

_PROJECT_SECTION_RE = re.compile(r"^\s*\[project\]\s*$")
_SECTION_RE = re.compile(r"^\s*\[[^\]]+\]\s*$")
_VERSION_RE = re.compile(r'^\s*version\s*=\s*"([^"]+)"\s*$')


def _version_from_pyproject(pyproject_path: Path) -> Optional[str]:
    if not pyproject_path.exists():
        return None

    in_project_section = False
    for line in pyproject_path.read_text(encoding="utf-8").splitlines():
        if _PROJECT_SECTION_RE.match(line):
            in_project_section = True
            continue
        if in_project_section and _SECTION_RE.match(line):
            in_project_section = False
            continue
        if not in_project_section:
            continue

        match = _VERSION_RE.match(line)
        if match:
            version = match.group(1).strip()
            return version or None

    return None


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

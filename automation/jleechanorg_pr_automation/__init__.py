"""
jleechanorg-pr-automation: GitHub PR automation system with safety limits and actionable counting.

This package provides comprehensive PR monitoring and automation capabilities with built-in
safety features, intelligent filtering, and cross-process synchronization.
"""

import re
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as dist_version
from pathlib import Path
from typing import Any

from .automation_safety_manager import AutomationSafetyManager


# Lazy import to avoid RuntimeWarning when running as script
# Use __getattr__ for Python 3.7+ lazy module imports
def __getattr__(name: str) -> Any:
    """Lazy import of JleechanorgPRMonitor to avoid frozen module warning."""
    if name == "JleechanorgPRMonitor":
        from .jleechanorg_pr_monitor import JleechanorgPRMonitor
        return JleechanorgPRMonitor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

from .utils import (
    SafeJSONManager,
    get_automation_limits,
    get_email_config,
    json_manager,
    setup_logging,
    validate_email_config,
)

_PROJECT_SECTION_RE = re.compile(r"^\s*\[project\]\s*$")
_SECTION_RE = re.compile(r"^\s*\[[^\]]+\]\s*$")
_VERSION_RE = re.compile(r'^\s*version\s*=\s*"([^"]+)"\s*$')


def _version_from_pyproject(pyproject_path: Path) -> str | None:
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


def _resolve_version() -> str:
    # Prefer the source-tree pyproject.toml when present (avoids mismatches with any
    # separately-installed distribution on the machine).
    try:
        # __file__ = automation/jleechanorg_pr_automation/__init__.py
        # parents[0] = automation/jleechanorg_pr_automation
        # parents[1] = automation
        pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
        version = _version_from_pyproject(pyproject_path)
        if version is not None:
            return version
    except Exception:
        pass

    try:
        return dist_version("jleechanorg-pr-automation")
    except PackageNotFoundError:
        return "0.2.39"
    except Exception:
        return "0.2.39"


__version__ = _resolve_version()
__author__ = "jleechan"
__email__ = "jlee@jleechan.org"

__all__ = [
    "AutomationSafetyManager",
    "JleechanorgPRMonitor",
    "SafeJSONManager",
    "get_automation_limits",
    "get_email_config",
    "json_manager",
    "setup_logging",
    "validate_email_config",
]

"""Tests to keep the orchestration package layout lean and centralized."""

from pathlib import Path

import orchestration


def test_no_nested_orchestration_package():
    """Ensure we don't ship a duplicate nested orchestration package."""
    package_root = Path(orchestration.__file__).parent
    nested_package = package_root / "orchestration"
    assert not nested_package.exists(), "Nested orchestration package should be removed to avoid duplicate code paths"

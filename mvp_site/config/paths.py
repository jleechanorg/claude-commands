"""
Centralized Path Configuration for WorldArchitect.AI

This module provides a single source of truth for all file and directory paths
used throughout the application and tests. This eliminates hardcoded path
calculations and ensures consistency across environments.

Usage:
    from config.paths import PATHS

    # Get frontend app.js path
    app_js_path = PATHS.frontend_dir / "app.js"

    # Get test data directory
    test_data = PATHS.test_data_dir
"""

from pathlib import Path


class PathConfig:
    """Centralized path configuration for the application."""

    def __init__(self):
        """Initialize paths based on this file's location."""
        # Get mvp_site directory (parent of config directory)
        self.base_dir = Path(__file__).parent.parent.resolve()

        # Validate we're in the right location
        if not (self.base_dir / "main.py").exists():
            raise RuntimeError(
                f"Invalid base directory: {self.base_dir}. Expected mvp_site with main.py"
            )

    @property
    def base_dir(self) -> Path:
        """Root mvp_site directory."""
        return self._base_dir

    @base_dir.setter
    def base_dir(self, value: Path):
        self._base_dir = value

    @property
    def frontend_dir(self) -> Path:
        """Frontend assets directory (frontend_v1/)."""
        return self.base_dir / "frontend_v1"

    @property
    def frontend_js_dir(self) -> Path:
        """Frontend JavaScript directory."""
        return self.frontend_dir / "js"

    @property
    def frontend_css_dir(self) -> Path:
        """Frontend CSS directory."""
        return self.frontend_dir / "css"

    @property
    def frontend_styles_dir(self) -> Path:
        """Frontend styles directory."""
        return self.frontend_dir / "styles"

    @property
    def tests_dir(self) -> Path:
        """Tests directory."""
        return self.base_dir / "tests"

    @property
    def test_data_dir(self) -> Path:
        """Test data directory."""
        return self.tests_dir / "data"

    @property
    def static_dir(self) -> Path:
        """Legacy static directory (should redirect to frontend_v1)."""
        return self.base_dir / "static"

    # Common file paths
    @property
    def app_js(self) -> Path:
        """Main application JavaScript file."""
        return self.frontend_dir / "app.js"

    @property
    def api_js(self) -> Path:
        """API JavaScript file."""
        return self.frontend_dir / "api.js"

    @property
    def auth_js(self) -> Path:
        """Authentication JavaScript file."""
        return self.frontend_dir / "auth.js"

    @property
    def index_html(self) -> Path:
        """Main index.html file."""
        return self.frontend_dir / "index.html"

    @property
    def main_css(self) -> Path:
        """Main CSS file."""
        return self.frontend_dir / "style.css"

    def validate_paths(self) -> dict:
        """Validate that key paths exist and return status."""
        paths_to_check = {
            "base_dir": self.base_dir,
            "frontend_dir": self.frontend_dir,
            "app_js": self.app_js,
            "api_js": self.api_js,
            "index_html": self.index_html,
            "tests_dir": self.tests_dir,
        }

        results = {}
        for name, path in paths_to_check.items():
            results[name] = {
                "path": str(path),
                "exists": path.exists(),
                "is_file": path.is_file() if path.exists() else None,
                "is_dir": path.is_dir() if path.exists() else None,
            }

        return results

    def get_relative_path(self, absolute_path: Path) -> Path:
        """Convert absolute path to relative path from base_dir."""
        try:
            return absolute_path.relative_to(self.base_dir)
        except ValueError:
            return absolute_path


# Global instance - import this in other modules
PATHS = PathConfig()


# Convenience functions for common operations
def get_test_file_path(test_module_file: str) -> Path:
    """
    Get the base directory path from a test module's __file__.

    Args:
        test_module_file: The __file__ variable from a test module

    Returns:
        Path to mvp_site directory
    """
    test_file_path = Path(test_module_file).resolve()

    # Navigate from test file to mvp_site directory
    # Handle different test directory structures
    current = test_file_path.parent
    while current != current.parent:  # Stop at filesystem root
        if (current / "main.py").exists():
            return current
        current = current.parent

    # Fallback to configured base directory
    return PATHS.base_dir


def validate_installation() -> bool:
    """Validate that all critical paths exist."""
    validation = PATHS.validate_paths()
    critical_paths = ["base_dir", "frontend_dir", "app_js", "index_html"]

    for path_name in critical_paths:
        if not validation[path_name]["exists"]:
            print(
                f"❌ Missing critical path: {path_name} -> {validation[path_name]['path']}"
            )
            return False

    print("✅ All critical paths validated")
    return True


if __name__ == "__main__":
    print("🔍 WorldArchitect.AI Path Configuration")
    print("=" * 50)

    validation = PATHS.validate_paths()
    for name, info in validation.items():
        status = "✅" if info["exists"] else "❌"
        print(f"{status} {name}: {info['path']}")

    print("\n" + "=" * 50)
    overall_status = validate_installation()
    if overall_status:
        print("🎉 Path configuration is healthy!")
    else:
        print("⚠️ Path configuration has issues!")

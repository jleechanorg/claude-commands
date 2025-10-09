# Python Modules: config

> Auto-generated overview of module docstrings and public APIs. Enhance descriptions as needed.
> Updated: 2025-10-08

## `config/__init__.py`

**Role:** No module docstring; review code to confirm responsibilities.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:** None exported (primarily internal helpers).

---

## `config/paths.py`

**Role:** Centralized Path Configuration for WorldArchitect.AI This module provides a single source of truth for all file and directory paths used throughout the application and tests. This eliminates hardcoded path calculations and ensures consistency across environments. Usage: from config.paths import PATHS # Get frontend app.js path app_js_path = PATHS.frontend_dir / "app.js" # Get test data directory test_data = PATHS.test_data_dir

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class PathConfig` – Centralized path configuration for the application. (Status: Keep).
  - `base_dir` – Root mvp_site directory. (Status: Keep).
  - `base_dir` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `frontend_dir` – Frontend assets directory (frontend_v1/). (Status: Keep).
  - `frontend_js_dir` – Frontend JavaScript directory. (Status: Keep).
  - `frontend_css_dir` – Frontend CSS directory. (Status: Keep).
  - `frontend_styles_dir` – Frontend styles directory. (Status: Keep).
  - `tests_dir` – Tests directory. (Status: Keep).
  - `test_data_dir` – Test data directory. (Status: Keep).
  - `static_dir` – Legacy static directory (should redirect to frontend_v1). (Status: Keep).
  - `app_js` – Main application JavaScript file. (Status: Keep).
  - `api_js` – API JavaScript file. (Status: Keep).
  - `auth_js` – Authentication JavaScript file. (Status: Keep).
  - `index_html` – Main index.html file. (Status: Keep).
  - `main_css` – Main CSS file. (Status: Keep).
  - `validate_paths` – Validate that key paths exist and return status. (Status: Keep).
  - `get_relative_path` – Convert absolute path to relative path from base_dir. (Status: Keep).
- `get_test_file_path` – Get the base directory path from a test module's __file__. Args: test_module_file: The __file__ variable from a test module Returns: Path to mvp_site directory (Status: Keep).
- `validate_installation` – Validate that all critical paths exist. (Status: Keep).

---


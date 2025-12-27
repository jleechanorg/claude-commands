"""
Global pytest configuration for mvp_site tests.

Ensures test runs use mock services and dev-mode-safe settings, preventing
real network calls (e.g., Gemini/Firebase) and clock-skew validation errors.
"""

import os
import importlib
import sys

# Force mock/test modes for all tests
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("USE_MOCKS", "true")
os.environ.setdefault("MOCK_SERVICES_MODE", "true")
os.environ.setdefault("WORLDAI_DEV_MODE", "true")

# Provide a dummy API key to satisfy libraries that check for presence
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-api-key")

# Ensure the real Flask module is loaded (some tests monkeypatch sys.modules)
sys.modules["flask"] = importlib.import_module("flask")

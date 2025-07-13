import os

# Shared configuration for browser-based tests
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8088")
SCREENSHOT_DIR = os.environ.get("TEST_SCREENSHOT_DIR", "/tmp/worldarchitectai/browser") 
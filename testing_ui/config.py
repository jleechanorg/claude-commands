import os

# Shared configuration for browser-based tests
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8088")
SCREENSHOT_DIR = os.environ.get("TEST_SCREENSHOT_DIR", "/tmp/worldarchitectai/browser")

# Dual Mode Configuration
# /testui = fake APIs (USE_MOCK_* = true)
# /testuif = real APIs (USE_MOCK_* = false)
def get_test_mode():
    """
    Determine if we're running with real or fake APIs.

    Returns:
        str: 'real' if using real APIs, 'fake' if using mocks
    """
    use_mock_firebase = os.environ.get("USE_MOCK_FIREBASE", "true").lower() == "true"
    use_mock_gemini = os.environ.get("USE_MOCK_GEMINI", "true").lower() == "true"

    if not use_mock_firebase and not use_mock_gemini:
        return "real"
    elif use_mock_firebase and use_mock_gemini:
        return "fake"
    else:
        return "mixed"

def is_real_api_mode():
    """Check if we're using real APIs (costs money)."""
    return get_test_mode() == "real"

def is_fake_api_mode():
    """Check if we're using fake/mock APIs."""
    return get_test_mode() == "fake"

def get_api_timeouts():
    """Get appropriate timeouts based on API mode."""
    if is_real_api_mode():
        return {
            "campaign_creation": 90000,  # 90 seconds for real Gemini
            "ai_response": 60000,        # 60 seconds for real AI chat
            "page_load": 15000           # 15 seconds for real Firebase
        }
    else:
        return {
            "campaign_creation": 10000,  # 10 seconds for mocks
            "ai_response": 5000,         # 5 seconds for mock responses
            "page_load": 5000            # 5 seconds for mock data
        }

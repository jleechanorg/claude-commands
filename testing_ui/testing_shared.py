#!/usr/bin/env python3
"""
Shared testing utilities for both browser and HTTP tests.
Provides common test data, configuration, and validation logic.
"""

import os
import subprocess
import time
import urllib.request

import requests

# Module-level constants
PROBLEMATIC_PHRASES = [
    "ser arion",
    "dragon knight",
    "celestial imperium",
    "empress sariel",
]

# Test data constants
CAMPAIGN_TEST_DATA = {
    "custom_campaign": {
        "title": "Test Custom Campaign",
        "campaign_type": "custom",
        "character_name": "Sir TestCharacter the Bold",
        "setting": "A mystical test realm",
        "description": "A custom campaign for testing",
        "custom_options": ["defaultWorld"],
        "selected_prompts": ["narrative", "mechanics"],
    },
    "dragon_knight_campaign": {
        "title": "Test Dragon Knight Campaign",
        "campaign_type": "dragon-knight",
        "character_name": "",  # Empty to test auto-generation
        "setting": "World of Assiah",
        "description": "",
        "custom_options": ["defaultWorld"],
        "selected_prompts": ["narrative", "mechanics"],
    },
    "empty_character_campaign": {
        "title": "Test Empty Character Campaign",
        "campaign_type": "custom",
        "character_name": "",  # Empty character name
        "setting": "A mystical test realm",
        "description": "",
        "custom_options": ["defaultWorld"],
        "selected_prompts": ["narrative", "mechanics"],
    },
    # Bug capture test data
    "bug_demo_campaign": {
        "title": "Bug Demo - Custom Campaign",
        "campaign_type": "custom",
        "character_name": "",
        "setting": "World of Assiah",
        "description": "",
        "custom_options": ["defaultWorld"],
        "selected_prompts": ["narrative", "mechanics"],
    },
    # Red/Green test data
    "red_test_campaign": {
        "title": "Red Test - Bug Demo",
        "campaign_type": "custom",
        "character_name": "",
        "setting": "",
        "description": "",
        "custom_options": [],
        "selected_prompts": ["narrative"],
    },
    "green_test_campaign": {
        "title": "Green Test - Character Fixed",
        "campaign_type": "custom",
        "character_name": "Sir Custom Knight",
        "setting": "Custom Realm",
        "description": "A properly filled custom campaign",
        "custom_options": ["defaultWorld"],
        "selected_prompts": ["narrative", "mechanics"],
    },
}

# Common test configuration
TEST_CONFIG = {
    "browser_base_url": "http://localhost:6006",
    "http_base_url": "http://localhost:8086",
    "structured_fields_port": "6006",
    "wizard_bug_port": "8088",
    "timeout_ms": 15000,
    "retry_count": 10,
    "wait_between_retries": 1000,
    "screenshot_dir": "/tmp/worldarchitectai/browser",
    "server_start_timeout": 30,
}


def generate_test_user_id(test_type="generic"):
    """Generate a unique test user ID with timestamp"""
    return f"test-{test_type}-{int(time.time())}"


def get_test_headers(user_id, test_mode="http"):
    """Get appropriate headers for test requests"""
    if test_mode == "http":
        return {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": user_id,
            "Content-Type": "application/json",
        }
    # Browser test might need different headers in future
    return {}


def get_test_url(test_mode="http", user_id=None, test_type="standard"):
    """Get appropriate base URL for test mode and test type"""
    if test_mode == "browser":
        # Different tests use different ports/URLs
        if test_type == "structured_fields":
            base_url = f"http://localhost:{TEST_CONFIG['structured_fields_port']}"
        elif test_type in ["wizard_bug", "red_green"]:
            base_url = f"http://localhost:{TEST_CONFIG['wizard_bug_port']}"
        else:
            base_url = TEST_CONFIG["browser_base_url"]

        if user_id:
            return f"{base_url}?test_mode=true&test_user_id={user_id}"
        return base_url
    return os.getenv("TEST_SERVER_URL", TEST_CONFIG["http_base_url"])


# Validation functions that both test types can use
def validate_campaign_created_successfully(response_data, test_mode="http"):
    """Common validation for successful campaign creation"""
    if test_mode == "http":
        # HTTP API returns simple confirmation
        assert response_data.get("success") == True, (
            f"Campaign creation not successful: {response_data}"
        )
        assert response_data.get("campaign_id") is not None, (
            f"No campaign ID returned: {response_data}"
        )
        return response_data.get("campaign_id")
    # Browser test would validate different elements
    # This can be extended when refactoring browser tests
    return None


def validate_character_name_display(
    character_text, expected_character, test_mode="http"
):
    """Common validation for character name display"""
    if expected_character:
        assert expected_character in character_text, (
            f"Expected character '{expected_character}' not found in: {character_text}"
        )

    # Common validations for both test types
    assert "dragon knight" not in character_text.lower(), (
        f"Found 'dragon knight' in character text: {character_text}"
    )


def validate_no_hardcoded_text(text_content, test_mode="http"):
    """Validate that hardcoded text issues are not present"""
    combined_text = text_content.lower()

    # Check for problematic hardcoded references
    assert "ser arion dragon knight campaign" not in combined_text, (
        f"Found hardcoded dragon knight text: {text_content}"
    )

    # Can add more common validations here
    return True


def validate_story_content_exists(story_data, minimum_length=50):
    """Validate that story content exists and has minimum content"""
    if isinstance(story_data, list) and len(story_data) > 0:
        first_entry = story_data[0]
        narrative_text = (
            first_entry.get("narrative_text", "")
            if isinstance(first_entry, dict)
            else ""
        )
        return len(narrative_text) >= minimum_length
    return False


# Test scenarios that both test types can use
TEST_SCENARIOS = {
    "custom_character_display": {
        "description": "Test that custom character names display correctly",
        "campaign_data": CAMPAIGN_TEST_DATA["custom_campaign"],
        "expected_character": "Sir TestCharacter the Bold",
        "validations": ["character_display", "no_hardcoded_text"],
    },
    "empty_character_handling": {
        "description": "Test that empty character input is handled properly",
        "campaign_data": CAMPAIGN_TEST_DATA["empty_character_campaign"],
        "expected_character": None,  # Should be auto-generated
        "validations": ["auto_generated_character", "no_dragon_knight_default"],
    },
    "story_content_loading": {
        "description": "Test that campaign loads with story content",
        "campaign_data": CAMPAIGN_TEST_DATA["dragon_knight_campaign"],
        "expected_character": None,
        "validations": ["story_content_exists", "campaign_retrievable"],
    },
    "structured_fields_test": {
        "description": "Test complete campaign creation workflow with structured fields",
        "campaign_data": CAMPAIGN_TEST_DATA["custom_campaign"],
        "expected_character": "Sir TestCharacter the Bold",
        "validations": ["structured_response", "campaign_created", "no_hardcoded_text"],
    },
    "bug_capture_test": {
        "description": "Test that captures wizard bugs for demonstration",
        "campaign_data": CAMPAIGN_TEST_DATA["bug_demo_campaign"],
        "expected_character": None,
        "validations": ["no_dragon_knight_in_custom", "screenshot_capture"],
    },
    "red_green_comparison": {
        "description": "Red/Green test comparing broken vs fixed behavior",
        "red_data": CAMPAIGN_TEST_DATA["red_test_campaign"],
        "green_data": CAMPAIGN_TEST_DATA["green_test_campaign"],
        "validations": ["red_shows_bug", "green_shows_fix"],
    },
    "api_response_capture": {
        "description": "Capture real API responses for mock data updates",
        "campaign_data": CAMPAIGN_TEST_DATA["custom_campaign"],
        "expected_character": "Sir TestCharacter the Bold",
        "validations": ["api_response_captured", "real_api_used"],
    },
}


# Server management utilities
def setup_test_environment(use_real_api=False, port="6006"):
    """Set up environment variables for testing"""
    os.environ["TESTING"] = "true"
    os.environ["PORT"] = port

    if use_real_api:
        os.environ.pop("USE_MOCK_FIREBASE", None)
        os.environ.pop("USE_MOCK_GEMINI", None)
        print("⚠️  USING REAL APIs - This will cost money!")
    else:
        os.environ["USE_MOCK_FIREBASE"] = "true"
        os.environ["USE_MOCK_GEMINI"] = "true"
        print("✓ Using mock APIs")


def start_test_server(port="6006") -> subprocess.Popen | None:
    """Start the test server and wait for it to be ready"""
    print(f"🚀 Starting test server on port {port}...")

    # Try vpython first, fallback to python
    try:
        server_process = subprocess.Popen(
            ["vpython", "mvp_site/main.py", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd(),
        )
    except FileNotFoundError:
        # Fallback to direct python with venv
        server_process = subprocess.Popen(
            ["python", "mvp_site/main.py", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd(),
            env={
                **os.environ,
                "PATH": os.path.join(os.getcwd(), "venv", "bin")
                + os.pathsep
                + os.environ.get("PATH", ""),
            },
        )

    print("⏳ Waiting for server to start...")
    for i in range(TEST_CONFIG["server_start_timeout"]):
        try:
            with urllib.request.urlopen(f"http://localhost:{port}") as resp:
                if resp.status == 200:
                    print("✅ Server is ready")
                    return server_process
        except:
            pass
        time.sleep(1)

    print("❌ Server failed to start")
    server_process.terminate()
    return None


# Screenshot and validation utilities
def ensure_screenshot_dir(test_name="generic"):
    """Ensure screenshot directory exists for test"""
    screenshot_dir = os.path.join(TEST_CONFIG["screenshot_dir"], test_name)
    os.makedirs(screenshot_dir, exist_ok=True)
    return screenshot_dir


def validate_no_dragon_knight_in_custom(page_content, test_mode="http"):
    """Validate that Dragon Knight defaults don't appear in custom campaigns"""
    content_lower = page_content.lower()

    # Check for Dragon Knight references that shouldn't be in custom campaigns
    for phrase in PROBLEMATIC_PHRASES:
        assert phrase not in content_lower, (
            f"Found Dragon Knight default '{phrase}' in custom campaign: {page_content[:200]}..."
        )

    return True


def validate_api_response_structure(response_data, expected_fields=None):
    """Validate that API response has expected structure"""
    if expected_fields is None:
        expected_fields = ["success", "campaign_id"]

    for field in expected_fields:
        assert field in response_data, (
            f"Missing required field '{field}' in response: {response_data}"
        )

    return True


def validate_browser_element_text(element_text, expected_content, should_contain=True):
    """Validate browser element text content"""
    if should_contain:
        assert expected_content in element_text, (
            f"Expected '{expected_content}' in element text: {element_text}"
        )
    else:
        assert expected_content not in element_text, (
            f"Should not contain '{expected_content}' in element text: {element_text}"
        )

    return True


# HTTP request helpers shared between tests
def make_authenticated_request(session, method, url, data=None, user_id=None):
    """Make an authenticated HTTP request with proper headers"""
    headers = get_test_headers(user_id or generate_test_user_id(), "http")

    if method.upper() == "GET":
        return session.get(url, headers=headers)
    if method.upper() == "POST":
        return session.post(url, json=data, headers=headers)
    raise ValueError(f"Unsupported HTTP method: {method}")


def setup_http_test_session(base_url, user_id=None):
    """Setup HTTP test session with authentication"""
    session = requests.Session()
    test_user_id = user_id or generate_test_user_id("http")

    # Navigate to homepage with test mode to establish session
    response = session.get(f"{base_url}?test_mode=true&test_user_id={test_user_id}")

    if response.status_code != 200:
        raise Exception(f"Failed to setup test session: {response.status_code}")

    # Update headers for session
    headers = get_test_headers(test_user_id, "http")
    session.headers.update(headers)

    return session, test_user_id

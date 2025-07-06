# Playwright Configuration for WorldArchitect.AI
# This configuration file provides basic setup for Playwright testing

import os
from pathlib import Path

# Test configuration
PLAYWRIGHT_CONFIG = {
    "base_url": "http://localhost:5000",
    "timeout": 30000,  # 30 seconds
    "browser_timeout": 60000,  # 60 seconds
    "trace": True,  # Enable trace for debugging
    "screenshot": "only-on-failure",
    "video": "retain-on-failure",
    "headless": True,  # Run in headless mode by default
    "slow_mo": 0,  # No slow motion by default
    "viewport": {"width": 1280, "height": 720},
    "browsers": ["chromium", "firefox", "webkit"]
}

# Test directories
TEST_DIR = Path(__file__).parent
OUTPUT_DIR = TEST_DIR / "test-results"
TRACE_DIR = OUTPUT_DIR / "traces"
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
VIDEO_DIR = OUTPUT_DIR / "videos"

# Create directories if they don't exist
for dir_path in [OUTPUT_DIR, TRACE_DIR, SCREENSHOT_DIR, VIDEO_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Flask app configuration for testing
FLASK_CONFIG = {
    "TESTING": True,
    "PORT": 5000,
    "DEBUG": False,
    "WTF_CSRF_ENABLED": False  # Disable CSRF for testing
}

# Test data
TEST_USER_EMAIL = "test@example.com"
TEST_CAMPAIGN_DATA = {
    "name": "Test Campaign",
    "description": "A test campaign for Playwright testing",
    "world": "Test World"
}

# Critical user flows to test
CRITICAL_FLOWS = [
    "homepage_load",
    "user_authentication",
    "campaign_creation",
    "character_creation",
    "game_session_start",
    "narrative_interaction",
    "state_updates",
    "campaign_export"
]

# Page selectors (to be updated based on actual DOM)
SELECTORS = {
    "auth": {
        "login_button": "[data-testid='login-button']",
        "email_input": "[data-testid='email-input']",
        "user_email_display": "#user-email"
    },
    "campaign": {
        "create_button": "[data-testid='create-campaign']",
        "campaign_title": "[data-testid='campaign-title']",
        "campaign_list": "[data-testid='campaign-list']",
        "delete_button": "[data-testid='delete-campaign']"
    },
    "character": {
        "create_button": "[data-testid='create-character']",
        "character_name": "[data-testid='character-name']",
        "character_class": "[data-testid='character-class']",
        "submit_button": "[data-testid='submit-character']"
    },
    "game": {
        "chat_input": "[data-testid='chat-input']",
        "send_button": "[data-testid='send-message']",
        "narrative_display": "[data-testid='narrative-display']",
        "character_sheet": "[data-testid='character-sheet']"
    }
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "page_load_time": 3000,  # 3 seconds
    "api_response_time": 2000,  # 2 seconds
    "navigation_time": 1000,  # 1 second
    "ai_response_time": 10000  # 10 seconds for AI responses
}

# Browser configurations for cross-browser testing
BROWSER_CONFIGS = {
    "chromium": {
        "args": [
            "--no-sandbox",
            "--disable-web-security",
            "--disable-dev-shm-usage",
            "--disable-gpu"
        ]
    },
    "firefox": {
        "args": [
            "--no-sandbox"
        ]
    },
    "webkit": {
        "args": []
    }
}
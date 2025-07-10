#!/usr/bin/env python3
"""
Common test data and mock server utilities for UI tests.
Provides reusable test data, mock responses, and server utilities.
"""
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Dict, Any, Optional, Callable

# Common test campaign data
DEFAULT_TEST_CAMPAIGNS = [
    {
        "id": "test-campaign-1",
        "title": "Test Campaign 1",
        "narrative_text": "Welcome to the test campaign.",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": "test-campaign-2", 
        "title": "Dragon Knight Adventure",
        "narrative_text": "You are Ser Arion, a Dragon Knight.",
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z"
    }
]

# Common test interaction response
DEFAULT_INTERACTION_RESPONSE = {
    "success": True,
    "response": {
        "narrative_text": "The dragon roars in response to your action.",
        "session_header": "Session 1, Turn 1",
        "planning_block": {
            "thinking": "The player is trying to interact with the dragon.",
            "context": "This is a dangerous situation."
        },
        "dice_rolls": [
            {"type": "Persuasion", "result": 15, "modifier": 3, "total": 18}
        ],
        "resource_updates": {
            "hp": {"current": 45, "max": 50},
            "spell_slots": {"level_1": 3, "level_2": 2}
        }
    }
}

# Test user configurations
TEST_USERS = {
    "default": {
        "id": "test-user-123",
        "name": "Test User"
    },
    "browser": {
        "id": "browser-test-user",
        "name": "Browser Test User"
    },
    "api": {
        "id": "api-test-user",
        "name": "API Test User"
    }
}

class MockAPIHandler(BaseHTTPRequestHandler):
    """
    Mock API handler for testing UI against fake backend.
    Can be customized with different responses.
    """
    
    # Class variables to store custom responses
    custom_responses = {}
    request_log = []
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass
    
    def do_GET(self):
        """Handle GET requests."""
        self.request_log.append({
            "method": "GET",
            "path": self.path,
            "headers": dict(self.headers)
        })
        
        if self.path == "/api/campaigns":
            self.send_json_response({"campaigns": DEFAULT_TEST_CAMPAIGNS})
        elif self.path.startswith("/api/campaigns/") and not "/interaction" in self.path:
            campaign_id = self.path.split("/")[-1]
            campaign = next((c for c in DEFAULT_TEST_CAMPAIGNS if c["id"] == campaign_id), None)
            if campaign:
                self.send_json_response(campaign)
            else:
                self.send_error(404, "Campaign not found")
        else:
            # Check custom responses
            if self.path in self.custom_responses:
                response = self.custom_responses[self.path]
                self.send_json_response(response)
            else:
                self.send_error(404, "Not found")
    
    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            json_data = json.loads(post_data) if post_data else {}
        except:
            json_data = {}
        
        self.request_log.append({
            "method": "POST",
            "path": self.path,
            "headers": dict(self.headers),
            "body": json_data
        })
        
        if self.path == "/api/campaigns":
            # Mock campaign creation
            response = {
                "success": True,
                "campaign_id": "test-campaign-new",
                "title": json_data.get("title", "New Campaign")
            }
            self.send_json_response(response, status=201)
        elif "/interaction" in self.path:
            # Mock interaction response
            response = DEFAULT_INTERACTION_RESPONSE.copy()
            # Can customize based on input
            if json_data.get("user_input", "").lower() == "attack":
                response["response"]["narrative_text"] = "You swing your sword at the enemy!"
            self.send_json_response(response)
        else:
            # Check custom responses
            if self.path in self.custom_responses:
                response = self.custom_responses[self.path]
                self.send_json_response(response)
            else:
                self.send_error(404, "Not found")
    
    def send_json_response(self, data: Dict[str, Any], status: int = 200):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

class MockAPIServer:
    """
    Context manager for running a mock API server during tests.
    
    Example:
        with MockAPIServer(port=8086) as server:
            server.set_response("/api/custom", {"custom": "data"})
            # Run your test
            # Access server.requests to see what was called
    """
    
    def __init__(self, port: int = 8086):
        self.port = port
        self.server = None
        self.thread = None
        MockAPIHandler.custom_responses = {}
        MockAPIHandler.request_log = []
    
    def set_response(self, path: str, response: Dict[str, Any]):
        """Set a custom response for a specific path."""
        MockAPIHandler.custom_responses[path] = response
    
    @property
    def requests(self):
        """Get the list of requests made to the server."""
        return MockAPIHandler.request_log
    
    def clear_requests(self):
        """Clear the request log."""
        MockAPIHandler.request_log = []
    
    def __enter__(self):
        """Start the mock server."""
        self.server = HTTPServer(('localhost', self.port), MockAPIHandler)
        self.thread = Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(0.5)  # Give server time to start
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the mock server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=2)

def generate_test_campaign(
    title: str = "Test Campaign",
    character: str = "Test Character",
    setting: str = "Test Setting",
    campaign_type: str = "custom"
) -> Dict[str, Any]:
    """
    Generate test campaign data with common structure.
    """
    return {
        "title": title,
        "character": character,
        "setting": setting,
        "campaignType": campaign_type,
        "selected_prompts": ["narrative", "mechanics"],
        "custom_options": ["companions"] if campaign_type == "custom" else ["defaultWorld"]
    }

def generate_mock_structured_response(
    narrative_text: str = "Default narrative response",
    session_num: int = 1,
    turn_num: int = 1,
    include_dice: bool = True,
    include_planning: bool = True
) -> Dict[str, Any]:
    """
    Generate a mock structured response with all expected fields.
    """
    response = {
        "narrative_text": narrative_text,
        "session_header": f"Session {session_num}, Turn {turn_num}"
    }
    
    if include_planning:
        response["planning_block"] = {
            "thinking": "AI is considering the situation.",
            "context": "Current game context.",
            "plan": "Next steps in the adventure."
        }
    
    if include_dice:
        response["dice_rolls"] = [
            {
                "type": "Investigation",
                "result": 12,
                "modifier": 4,
                "total": 16,
                "success": True
            }
        ]
    
    return response

# Convenience functions for common test scenarios
def get_test_user_headers(user_type: str = "default") -> Dict[str, str]:
    """Get test authentication headers for a specific user type."""
    user = TEST_USERS.get(user_type, TEST_USERS["default"])
    return {
        "X-Test-Mode": "true",
        "X-Test-User-Id": user["id"]
    }

def create_test_campaign(page, campaign_name: str = "All Fields Test Campaign", 
                        character: str = "Test Character",
                        setting: str = "Test Setting") -> bool:
    """
    Create a test campaign with structured fields enabled.
    
    Args:
        page: Playwright page instance
        campaign_name: Name for the test campaign
        character: Character name/description
        setting: Setting/world description
        
    Returns:
        True if campaign created successfully, False otherwise
    """
    try:
        # Wait for and click new campaign button
        new_campaign_selectors = [
            "text='Start New Campaign'",
            "text='New Campaign'",
            "text='Create Campaign'",
            "#new-campaign-btn",
            "button:has-text('New Campaign')"
        ]
        
        clicked = False
        for selector in new_campaign_selectors:
            try:
                page.wait_for_selector(selector, timeout=3000)
                page.click(selector)
                clicked = True
                break
            except:
                continue
        
        if not clicked:
            print("❌ Could not find New Campaign button")
            return False
        
        # Wait for campaign form
        page.wait_for_selector("#campaign-title, #wizard-campaign-title", timeout=10000)
        
        # Check if it's the wizard or regular form
        if page.is_visible("#wizard-campaign-title"):
            # Wizard form
            page.fill("#wizard-campaign-title", campaign_name)
            
            # Check for character/setting fields in wizard
            if page.is_visible("#wizard-character-input"):
                page.fill("#wizard-character-input", character)
            if page.is_visible("#wizard-setting-input"):
                page.fill("#wizard-setting-input", setting)
            
            # Navigate through wizard steps
            for _ in range(3):
                if page.is_visible("button:has-text('Next')"):
                    page.click("button:has-text('Next')")
                    page.wait_for_timeout(500)
            
            # Click launch button
            if page.is_visible("#launch-campaign"):
                page.click("#launch-campaign")
            elif page.is_visible("button:has-text('Begin Adventure')"):
                page.click("button:has-text('Begin Adventure')")
        else:
            # Regular form
            page.fill("#campaign-title", campaign_name)
            
            # Fill character and setting if they exist
            if page.is_visible("#character-input"):
                page.fill("#character-input", character)
            if page.is_visible("#setting-input"):
                page.fill("#setting-input", setting)
            
            # Submit form
            submit_selectors = [
                "button[type='submit']",
                "button:has-text('Create Campaign')",
                "button:has-text('Begin Adventure')"
            ]
            
            for selector in submit_selectors:
                if page.is_visible(selector):
                    page.click(selector)
                    break
        
        # Wait for campaign creation
        page.wait_for_selector("#game-view", timeout=30000)
        
        return True
        
    except Exception as e:
        print(f"❌ Campaign creation failed: {e}")
        return False
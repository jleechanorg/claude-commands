#!/usr/bin/env python3
"""
Shared helper library for browser test screenshot management and standardization.
Enforces consistent screenshot naming, directory structure, and test patterns.
"""

import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.sync_api import Page, Browser

# Standard screenshot directory structure
SCREENSHOT_BASE_DIR = "/tmp/worldarchitectai/browser"
STRUCTURED_FIELDS_DIR = f"{SCREENSHOT_BASE_DIR}/structured_fields"
INTEGRATION_DIR = f"{SCREENSHOT_BASE_DIR}/integration"
UNIT_DIR = f"{SCREENSHOT_BASE_DIR}/unit"

class BrowserTestHelper:
    """Shared helper for browser test screenshot management."""
    
    def __init__(self, test_name: str, page: Page):
        self.test_name = test_name
        self.page = page
        self.screenshot_counter = 0
        self.screenshot_dir = self._setup_screenshot_directory()
        
    def _setup_screenshot_directory(self) -> str:
        """Create and return the screenshot directory for this test."""
        # Determine directory based on test name
        if 'structured_fields' in self.test_name.lower():
            base_dir = STRUCTURED_FIELDS_DIR
        elif 'integration' in self.test_name.lower():
            base_dir = INTEGRATION_DIR
        else:
            base_dir = UNIT_DIR
            
        # Create directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        return base_dir
    
    def take_screenshot(self, description: str, element_selector: Optional[str] = None) -> str:
        """
        Take a screenshot with standardized naming and location.
        
        Args:
            description: Description of what the screenshot shows
            element_selector: Optional CSS selector to screenshot specific element
            
        Returns:
            Path to the screenshot file
        """
        # Generate filename with counter and description
        filename = f"{self.screenshot_counter:02d}_{description.lower().replace(' ', '_')}.png"
        filepath = os.path.join(self.screenshot_dir, filename)
        
        try:
            if element_selector:
                # Screenshot specific element
                element = self.page.locator(element_selector)
                element.screenshot(path=filepath)
            else:
                # Screenshot entire page
                self.page.screenshot(path=filepath, full_page=True)
                
            print(f"📸 Screenshot saved: {filepath}")
            self.screenshot_counter += 1
            return filepath
            
        except Exception as e:
            print(f"❌ Screenshot failed for {description}: {e}")
            return ""
    
    def wait_for_element(self, selector: str, timeout: float = 30.0) -> bool:
        """Wait for element to be visible with timeout."""
        try:
            self.page.wait_for_selector(selector, timeout=timeout * 1000)
            return True
        except Exception as e:
            print(f"⏰ Element not found: {selector} - {e}")
            return False
    
    def wait_for_content(self, content: str, timeout: float = 30.0) -> bool:
        """Wait for specific content to appear on page."""
        try:
            self.page.wait_for_function(
                f"document.body.innerText.includes('{content}')",
                timeout=timeout * 1000
            )
            return True
        except Exception as e:
            print(f"⏰ Content not found: {content} - {e}")
            return False
    
    def navigate_to_test_game(self, campaign_name: str = "All Fields Test Campaign") -> bool:
        """
        Navigate to a test game using standard test mode parameters.
        
        Args:
            campaign_name: Name of campaign to navigate to
            
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            # Navigate to dashboard with test mode
            self.page.goto("http://localhost:6006?test_mode=true&test_user_id=test-user-123")
            
            # Wait for dashboard to load
            if not self.wait_for_element("[data-testid='campaign-list']", timeout=10):
                if not self.wait_for_element(".campaign-card", timeout=10):
                    print("❌ Dashboard not loaded - no campaign list found")
                    return False
            
            # Click on the specified campaign
            campaign_selector = f"text='{campaign_name}'"
            if not self.wait_for_element(campaign_selector, timeout=5):
                print(f"❌ Campaign '{campaign_name}' not found")
                return False
                
            self.page.click(campaign_selector)
            
            # Wait for game view to load
            if not self.wait_for_element("#game-view", timeout=10):
                print("❌ Game view not loaded")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def capture_structured_fields_sequence(self, action_text: str = "I attack the goblin") -> Dict[str, str]:
        """
        Capture a complete sequence of structured fields screenshots.
        
        Args:
            action_text: Text to send to trigger AI response
            
        Returns:
            Dictionary mapping field names to screenshot paths
        """
        screenshots = {}
        
        # Take initial screenshot
        screenshots['full_page'] = self.take_screenshot("full_page")
        
        # Enter action and submit
        action_input = self.page.locator("#player-action")
        action_input.fill(action_text)
        self.page.click("#send-action")
        
        # Wait for response
        if not self.wait_for_content("Response time:", timeout=30):
            print("❌ No AI response received")
            return screenshots
        
        # Take screenshot of full response
        screenshots['full_ai_response'] = self.take_screenshot("full_ai_response")
        
        # Capture individual field screenshots
        field_selectors = {
            'session_header': '.session-header',
            'narrative': '#story-content p:last-child',
            'dice_rolls': '.dice-rolls',
            'resources': '.resources',
            'planning_block': '.planning-block',
            'debug_info': '.debug-info',
            'god_mode_response': '.god-mode-response',
            'entities_mentioned': '.entities-mentioned', 
            'location_confirmed': '.location-confirmed'
        }
        
        for field_name, selector in field_selectors.items():
            if self.page.locator(selector).count() > 0:
                screenshots[field_name] = self.take_screenshot(field_name, selector)
            else:
                print(f"⚠️ Field not found: {field_name}")
        
        # Take final full page screenshot
        screenshots['full_page_final'] = self.take_screenshot("full_page_final")
        
        return screenshots
    
    def get_screenshot_summary(self) -> Dict[str, Any]:
        """Get summary of all screenshots taken during test."""
        return {
            'test_name': self.test_name,
            'screenshot_dir': self.screenshot_dir,
            'total_screenshots': self.screenshot_counter,
            'directory_listing': os.listdir(self.screenshot_dir)
        }

def create_test_campaign(page: Page, campaign_name: str = "All Fields Test Campaign") -> bool:
    """
    Create a test campaign with structured fields enabled.
    
    Args:
        page: Playwright page instance
        campaign_name: Name for the test campaign
        
    Returns:
        True if campaign created successfully, False otherwise
    """
    try:
        # Navigate to new campaign page
        page.goto("http://localhost:6006?test_mode=true&test_user_id=test-user-123")
        
        # Wait for dashboard and click new campaign
        page.wait_for_selector("text='Start New Campaign'", timeout=10000)
        page.click("text='Start New Campaign'")
        
        # Fill campaign details
        page.wait_for_selector("#campaign-title", timeout=10000)
        page.fill("#campaign-title", campaign_name)
        
        # Use test prompt for structured fields
        test_prompt = """Test campaign to demonstrate all structured fields including:
- Session headers with timestamps
- Narrative content with scene information
- Dice rolls with calculations
- Resource tracking
- Planning blocks with options
- Debug information with DM notes
- State rationale explanations
- God mode responses when needed
- Entity mentions and location confirmation"""
        
        page.fill("#campaign-prompt", test_prompt)
        
        # Create campaign
        page.click("text='Create Campaign'")
        
        # Wait for campaign creation
        page.wait_for_selector("#game-view", timeout=30000)
        
        return True
        
    except Exception as e:
        print(f"❌ Campaign creation failed: {e}")
        return False

def cleanup_old_screenshots(days_old: int = 7):
    """Clean up screenshot directories older than specified days."""
    import time
    
    current_time = time.time()
    cutoff_time = current_time - (days_old * 24 * 60 * 60)
    
    for root, dirs, files in os.walk(SCREENSHOT_BASE_DIR):
        for file in files:
            if file.endswith('.png'):
                filepath = os.path.join(root, file)
                if os.path.getctime(filepath) < cutoff_time:
                    os.remove(filepath)
                    print(f"🗑️ Removed old screenshot: {filepath}")
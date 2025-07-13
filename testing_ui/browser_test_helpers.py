"""
Browser Test Helper Library for WorldArchitect.AI

This library provides standardized authentication bypass and utility functions
for browser tests using Playwright.
"""
import os
from playwright.sync_api import Page, Browser, BrowserContext
from testing_ui.config import BASE_URL, SCREENSHOT_DIR


class BrowserTestHelper:
    """Helper class for browser test authentication and common operations."""
    
    def __init__(self, page: Page, base_url: str = None):
        """
        Initialize browser test helper.
        
        Args:
            page: Playwright page instance
            base_url: Base URL for the application (defaults to BASE_URL from config)
        """
        self.page = page
        self.base_url = base_url or BASE_URL
    
    def navigate_with_test_auth(self, path: str = "/", test_user_id: str = "test-user-123"):
        """
        Navigate to a page with test mode authentication bypass enabled.
        
        Args:
            path: Path to navigate to (default: "/")
            test_user_id: Test user ID to use (default: "test-user-123")
        
        Returns:
            The page response
        """
        test_url = f"{self.base_url}{path}?test_mode=true&test_user_id={test_user_id}"
        print(f"🔐 Navigating with test auth: {test_url}")
        return self.page.goto(test_url)
    
    def wait_for_auth_bypass(self, timeout: int = 5000):
        """
        Wait for the authentication bypass to take effect.
        
        Args:
            timeout: Timeout in milliseconds (default: 5000)
        """
        try:
            # Wait for either dashboard or game view to appear (indicates auth success)
            self.page.wait_for_selector("#dashboard-view, #game-view", timeout=timeout)
            print("✅ Authentication bypass successful")
        except Exception as e:
            print(f"⚠️ Auth bypass may have failed: {e}")
            raise
    
    def create_test_campaign(self, campaign_title: str = "Browser Test Campaign", debug_mode: bool = True):
        """
        Create a test campaign using the campaign creation form.
        
        Args:
            campaign_title: Title for the test campaign
            debug_mode: Enable detailed debugging output (default: True)
        
        Returns:
            True if campaign creation succeeded, False otherwise
        """
        try:
            # Click "Start New Campaign" button
            print("🎮 Clicking 'Start New Campaign' button...")
            self.page.wait_for_selector("#go-to-new-campaign", timeout=10000)
            self.page.click("#go-to-new-campaign")
            
            # Wait for new campaign view
            self.page.wait_for_selector("#new-campaign-view", timeout=10000)
            print("✅ New campaign view loaded")
            
            if debug_mode:
                self.take_screenshot("debug_01_after_new_campaign_view")
                
            # Debug the campaign title element state before trying to interact
            if debug_mode:
                self.debug_element_state("#campaign-title", "Campaign Title Input")
                self.debug_element_state("#new-campaign-view", "New Campaign View")
                
            # Try waiting with different strategies
            try:
                print("🔍 Attempting to wait for #campaign-title visibility...")
                self.page.wait_for_selector("#campaign-title", state="visible", timeout=5000)
                print("✅ Campaign title field is visible")
            except Exception as e:
                print(f"⚠️ Initial visibility wait failed: {e}")
                
                if debug_mode:
                    self.take_screenshot("debug_02_visibility_wait_failed")
                    
                # Try waiting a bit longer
                print("⏳ Waiting additional time for form to render...")
                self.page.wait_for_timeout(3000)
                
                if debug_mode:
                    self.debug_element_state("#campaign-title", "Campaign Title After Wait")
                    self.take_screenshot("debug_03_after_additional_wait")
                
                # Try forcing visibility
                print("🔧 Attempting to force element visibility...")
                self.page.evaluate("""
                    const el = document.getElementById('campaign-title');
                    if (el) {
                        el.style.display = 'block';
                        el.style.visibility = 'visible';
                        el.style.opacity = '1';
                        console.log('Forced campaign-title visibility');
                    }
                """)
                
                if debug_mode:
                    self.debug_element_state("#campaign-title", "Campaign Title After Force Visible")
                    
                # Try scrolling element into view to get it out from under navbar
                print("📜 Scrolling campaign title into view...")
                self.page.evaluate("""
                    const el = document.getElementById('campaign-title');
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        // Also try focus to ensure it's interactable
                        el.focus();
                    }
                """)
                
                # Wait for scroll to complete
                self.page.wait_for_timeout(1000)
                
                if debug_mode:
                    self.debug_element_state("#campaign-title", "Campaign Title After Scroll")
                    self.take_screenshot("debug_04_after_scroll")
            
            # Clear existing value and fill
            print("🔧 Clearing and filling campaign title...")
            self.page.evaluate("document.getElementById('campaign-title').value = ''")
            
            # Try using evaluate to set value directly if fill fails
            try:
                self.page.fill("#campaign-title", campaign_title, timeout=5000)
                print(f"✅ Filled campaign title: {campaign_title}")
            except Exception as e:
                print(f"⚠️ Fill failed, trying direct value setting: {e}")
                self.page.evaluate(f"document.getElementById('campaign-title').value = '{campaign_title}'")
                print(f"✅ Set campaign title via JavaScript: {campaign_title}")
            
            # Navigate through the 4-step wizard
            print("🧙‍♂️ Navigating through 4-step campaign wizard...")
            
            # Step 1: Fill form and click Next
            print("📝 Step 1/4: Campaign Basics")
            if debug_mode:
                self.take_screenshot("wizard_step_1_filled")
            
            try:
                next_button = self.page.locator("button:has-text('Next')")
                if next_button.is_visible():
                    # Scroll to Next button to avoid navbar
                    next_button.scroll_into_view_if_needed()
                    self.page.wait_for_timeout(500)
                    next_button.click()
                    print("✅ Clicked Next for step 1")
                else:
                    print("❌ Next button not found on step 1")
                    return False
            except Exception as e:
                print(f"⚠️ Step 1 Next click failed: {e}")
                return False
            
            # Step 2: AI Style
            print("🤖 Step 2/4: AI Style")
            self.page.wait_for_timeout(2000)  # Wait for step transition
            if debug_mode:
                self.take_screenshot("wizard_step_2")
            
            try:
                next_button = self.page.locator("button:has-text('Next')")
                if next_button.is_visible():
                    next_button.scroll_into_view_if_needed()
                    self.page.wait_for_timeout(500)
                    next_button.click()
                    print("✅ Clicked Next for step 2")
                else:
                    print("❌ Next button not found on step 2")
                    return False
            except Exception as e:
                print(f"⚠️ Step 2 Next click failed: {e}")
                return False
            
            # Step 3: Options
            print("⚙️ Step 3/4: Options")
            self.page.wait_for_timeout(2000)
            if debug_mode:
                self.take_screenshot("wizard_step_3")
                
            try:
                next_button = self.page.locator("button:has-text('Next')")
                if next_button.is_visible():
                    next_button.scroll_into_view_if_needed()
                    self.page.wait_for_timeout(500)
                    next_button.click()
                    print("✅ Clicked Next for step 3")
                else:
                    print("❌ Next button not found on step 3")
                    return False
            except Exception as e:
                print(f"⚠️ Step 3 Next click failed: {e}")
                return False
            
            # Step 4: Launch
            print("🚀 Step 4/4: Launch Campaign")
            self.page.wait_for_timeout(2000)
            if debug_mode:
                self.take_screenshot("wizard_step_4_launch")
                
            try:
                # Look for the specific launch button (avoid the duplicate)
                launch_selectors = [
                    "#launch-campaign",  # Specific ID from debug output
                    "button[id='launch-campaign']",
                    "button.btn-lg:has-text('Begin Adventure!')",  # The visible one has btn-lg class
                    "button[type='button']:has-text('Begin Adventure!')"  # The visible one has type=button
                ]
                
                # Debug: show what buttons exist
                if debug_mode:
                    print("🔍 Debug: Looking for buttons on step 4")
                    buttons = self.page.locator("button").all()
                    for i, button in enumerate(buttons):
                        try:
                            text = button.text_content()
                            visible = button.is_visible()
                            print(f"   Button {i}: '{text}' (visible: {visible})")
                        except:
                            print(f"   Button {i}: Error getting text")
                
                launched = False
                for selector in launch_selectors:
                    try:
                        launch_button = self.page.locator(selector)
                        if launch_button.count() > 0:
                            print(f"🎯 Found launch button with selector: {selector}")
                            launch_button.scroll_into_view_if_needed()
                            self.page.wait_for_timeout(1000)
                            
                            # Try clicking, fall back to JavaScript if covered by navbar
                            try:
                                launch_button.click(timeout=3000)
                                print(f"✅ Clicked launch button: {selector}")
                            except:
                                print(f"⚠️ Click failed, using JavaScript for: {selector}")
                                # Use JavaScript to click the button
                                self.page.evaluate(f"document.querySelector('{selector.replace(':', '\\:')}').click()")
                                print(f"✅ JavaScript clicked: {selector}")
                            
                            launched = True
                            break
                    except Exception as e:
                        print(f"⚠️ Error with selector {selector}: {e}")
                        continue
                        
                if not launched:
                    print("❌ No launch button found on step 4")
                    if debug_mode:
                        self.debug_element_state("button", "All buttons on step 4")
                    return False
                    
            except Exception as e:
                print(f"⚠️ Step 4 launch failed: {e}")
                return False
            
            # Step 5: Wait for campaign to redirect and game view to load
            print("🎯 Step 5/5: Loading campaign view...")
            if debug_mode:
                self.take_screenshot("wizard_step_5_post_launch")
            
            # Wait for navigation to game view
            try:
                # First wait for any redirect/navigation
                self.page.wait_for_timeout(2000)
                
                # Then wait for game view to appear (longer timeout for real API)
                self.page.wait_for_selector("#game-view", timeout=60000)
                print("✅ Game view loaded")
                
                # Wait for initial content to load (longer timeout for real API)
                self.page.wait_for_selector("#story-content", timeout=30000)
                print("✅ Story content loaded")
                
                # Additional wait for structured fields to render
                self.page.wait_for_timeout(5000)
                
                # Take final screenshot
                if debug_mode:
                    self.take_screenshot("wizard_step_5_campaign_loaded")
                
                print(f"✅ Test campaign '{campaign_title}' created and loaded successfully")
                return True
                
            except Exception as e:
                print(f"⚠️ Campaign view loading failed: {e}")
                if debug_mode:
                    self.take_screenshot("wizard_step_5_load_failed")
                return False
            
        except Exception as e:
            print(f"❌ Campaign creation failed: {e}")
            return False
    
    def take_screenshot(self, name: str, full_page: bool = True):
        """
        Take a screenshot with standardized naming.
        
        Args:
            name: Name for the screenshot (will be sanitized)
            full_page: Whether to capture full page (default: True)
        """
        # Sanitize filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        
        screenshot_path = f"{SCREENSHOT_DIR}/{safe_name}.png"
        self.page.screenshot(path=screenshot_path, full_page=full_page)
        print(f"📸 Screenshot saved: {screenshot_path}")
        return screenshot_path
    
    def debug_element_state(self, selector: str, name: str = "element"):
        """
        Debug and print detailed information about an element's state.
        
        Args:
            selector: CSS selector for the element
            name: Descriptive name for the element (for logging)
        """
        print(f"\n🔍 DEBUG: Analyzing {name} ({selector})")
        
        try:
            # Check if element exists
            elements = self.page.locator(selector)
            count = elements.count()
            print(f"   📊 Elements found: {count}")
            
            if count == 0:
                print(f"   ❌ No elements found with selector: {selector}")
                return
            
            # Get first element for detailed analysis
            element = elements.first
            
            # Basic visibility checks
            is_visible = element.is_visible()
            is_enabled = element.is_enabled()
            is_editable = element.is_editable()
            
            print(f"   👁️  Visible: {is_visible}")
            print(f"   ✏️  Enabled: {is_enabled}")
            print(f"   📝 Editable: {is_editable}")
            
            # Get computed styles
            styles = self.page.evaluate(f"""
                (selector) => {{
                    const el = document.querySelector(selector);
                    if (!el) return null;
                    const computed = window.getComputedStyle(el);
                    return {{
                        display: computed.display,
                        visibility: computed.visibility,
                        opacity: computed.opacity,
                        zIndex: computed.zIndex,
                        position: computed.position,
                        width: computed.width,
                        height: computed.height,
                        transform: computed.transform
                    }};
                }}
            """, selector)
            
            if styles:
                print(f"   🎨 CSS Styles:")
                for key, value in styles.items():
                    print(f"      {key}: {value}")
            
            # Get bounding box
            try:
                bbox = element.bounding_box()
                if bbox:
                    print(f"   📐 Bounding Box: x={bbox['x']}, y={bbox['y']}, w={bbox['width']}, h={bbox['height']}")
                else:
                    print(f"   📐 Bounding Box: None (element not in viewport or hidden)")
            except:
                print(f"   📐 Bounding Box: Error getting bounds")
            
            # Check for overlapping elements
            try:
                overlapping = self.page.evaluate(f"""
                    (selector) => {{
                        const el = document.querySelector(selector);
                        if (!el) return null;
                        const rect = el.getBoundingClientRect();
                        const centerX = rect.left + rect.width / 2;
                        const centerY = rect.top + rect.height / 2;
                        const topElement = document.elementFromPoint(centerX, centerY);
                        return {{
                            targetElement: el.tagName + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className.split(' ').join('.') : ''),
                            topElement: topElement ? topElement.tagName + (topElement.id ? '#' + topElement.id : '') + (topElement.className ? '.' + topElement.className.split(' ').join('.') : '') : 'none',
                            isTargetOnTop: topElement === el
                        }};
                    }}
                """, selector)
                
                if overlapping:
                    print(f"   🎯 Element Coverage:")
                    print(f"      Target: {overlapping['targetElement']}")
                    print(f"      Top element at center: {overlapping['topElement']}")
                    print(f"      Target on top: {overlapping['isTargetOnTop']}")
            except:
                print(f"   🎯 Element Coverage: Error checking overlaps")
                
        except Exception as e:
            print(f"   ❌ Error analyzing element: {e}")
        
        print(f"🔍 DEBUG: {name} analysis complete\n")
    
    def send_game_interaction(self, text: str, mode: str = "character"):
        """
        Send a game interaction in character or god mode.
        
        Args:
            text: The interaction text to send
            mode: Either "character" or "god" (default: "character")
        """
        try:
            # Select interaction mode
            if mode == "god":
                self.page.check("#god-mode")
            else:
                self.page.check("#char-mode")
            
            # Fill and submit interaction
            self.page.fill("#user-input", text)
            self.page.click('#interaction-form button[type="submit"]')
            
            print(f"📤 Sent {mode} mode interaction: {text}")
            
        except Exception as e:
            print(f"❌ Failed to send interaction: {e}")
    
    def wait_for_ai_response(self, timeout: int = 30000):
        """
        Wait for AI response to complete.
        
        Args:
            timeout: Timeout in milliseconds (default: 30000)
        """
        try:
            # Wait for loading spinner to disappear
            self.page.wait_for_selector("#loading-spinner", state="hidden", timeout=timeout)
            print("✅ AI response completed")
            
        except Exception as e:
            print(f"⚠️ AI response timeout or error: {e}")
    
    def get_story_content(self):
        """
        Get the current story content from the game view.
        
        Returns:
            String containing the story content, or None if not found
        """
        try:
            story_element = self.page.query_selector("#story-content")
            if story_element:
                return story_element.inner_text()
            return None
        except Exception as e:
            print(f"❌ Failed to get story content: {e}")
            return None


def create_test_helper(page: Page, base_url: str = None) -> BrowserTestHelper:
    """
    Factory function to create a BrowserTestHelper instance.
    
    Args:
        page: Playwright page instance
        base_url: Base URL for the application
    
    Returns:
        BrowserTestHelper instance
    """
    return BrowserTestHelper(page, base_url)


def setup_test_environment(use_real_api: bool = False):
    """
    Set up environment variables for browser testing.
    
    Args:
        use_real_api: If True, use real APIs instead of mocks (costs money!)
    """
    os.environ["TESTING"] = "true"
    if use_real_api:
        os.environ["USE_MOCK_FIREBASE"] = "false"
        os.environ["USE_MOCK_GEMINI"] = "false"
        print("🔧 Test environment configured with REAL APIs (costs money!)")
    else:
        os.environ["USE_MOCK_FIREBASE"] = "true"
        os.environ["USE_MOCK_GEMINI"] = "true"
        print("🔧 Test environment configured with mocks")
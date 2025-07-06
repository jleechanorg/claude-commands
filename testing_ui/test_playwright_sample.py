"""
Sample Playwright Test for WorldArchitect.AI
This file demonstrates basic Playwright testing patterns for the Flask application.
"""

import pytest
import asyncio
import time
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright.sync_api import sync_playwright, Browser as SyncBrowser, BrowserContext as SyncBrowserContext, Page as SyncPage
from playwright_config import PLAYWRIGHT_CONFIG, SELECTORS, PERFORMANCE_THRESHOLDS, TEST_USER_EMAIL

class TestWorldArchitectPlaywright:
    """
    Sample test class demonstrating Playwright testing patterns
    for WorldArchitect.AI Flask application.
    """
    
    def setup_method(self):
        """Setup before each test method."""
        self.base_url = PLAYWRIGHT_CONFIG["base_url"]
        self.timeout = PLAYWRIGHT_CONFIG["timeout"]
    
    def test_homepage_load_sync(self):
        """Test basic homepage loading using synchronous Playwright API."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport=PLAYWRIGHT_CONFIG["viewport"]
            )
            page = context.new_page()
            
            # Measure page load time
            start_time = time.time()
            try:
                page.goto(self.base_url, timeout=self.timeout)
                load_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                # Basic assertions
                assert page.title() is not None
                assert "WorldArchitect" in page.title()
                
                # Performance check
                assert load_time < PERFORMANCE_THRESHOLDS["page_load_time"], f"Page load too slow: {load_time}ms"
                
                # Check for critical elements
                assert page.locator("body").is_visible()
                
                print(f"✅ Homepage loaded successfully in {load_time:.2f}ms")
                
            except Exception as e:
                print(f"❌ Homepage load failed: {e}")
                # Take screenshot on failure
                page.screenshot(path="tmp/test-results/homepage_load_failure.png")
                raise
            finally:
                browser.close()
    
    def test_navigation_elements_sync(self):
        """Test navigation elements and basic UI components."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport=PLAYWRIGHT_CONFIG["viewport"]
            )
            page = context.new_page()
            
            try:
                page.goto(self.base_url, timeout=self.timeout)
                
                # Test navigation bar
                navbar = page.locator("nav.navbar")
                assert navbar.is_visible(), "Navigation bar not visible"
                
                # Test brand/logo
                brand = page.locator(".navbar-brand")
                assert brand.is_visible(), "Brand logo not visible"
                assert "WorldArchitect" in brand.text_content()
                
                # Test theme selector (if present)
                theme_dropdown = page.locator(".dropdown-toggle")
                if theme_dropdown.is_visible():
                    theme_dropdown.click()
                    # Wait for dropdown to open
                    page.wait_for_timeout(500)
                    
                print("✅ Navigation elements test passed")
                
            except Exception as e:
                print(f"❌ Navigation test failed: {e}")
                page.screenshot(path="tmp/test-results/navigation_failure.png")
                raise
            finally:
                browser.close()
    
    def test_responsive_design_sync(self):
        """Test responsive design across different viewport sizes."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Test different viewport sizes
            viewports = [
                {"width": 1920, "height": 1080, "name": "desktop"},
                {"width": 768, "height": 1024, "name": "tablet"},
                {"width": 375, "height": 667, "name": "mobile"}
            ]
            
            for viewport in viewports:
                context = browser.new_context(
                    viewport={"width": viewport["width"], "height": viewport["height"]}
                )
                page = context.new_page()
                
                try:
                    page.goto(self.base_url, timeout=self.timeout)
                    
                    # Basic visibility checks
                    assert page.locator("body").is_visible()
                    
                    # Check if navbar is responsive
                    navbar = page.locator("nav.navbar")
                    assert navbar.is_visible()
                    
                    # Take screenshot for manual review
                    page.screenshot(path=f"tmp/test-results/responsive_{viewport['name']}.png")
                    
                    print(f"✅ Responsive test passed for {viewport['name']} ({viewport['width']}x{viewport['height']})")
                    
                except Exception as e:
                    print(f"❌ Responsive test failed for {viewport['name']}: {e}")
                    raise
                finally:
                    context.close()
            
            browser.close()
    
    def test_javascript_errors_sync(self):
        """Test for JavaScript errors on page load."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Capture console messages
            console_messages = []
            page.on("console", lambda msg: console_messages.append(msg))
            
            # Capture JavaScript errors
            js_errors = []
            page.on("pageerror", lambda error: js_errors.append(str(error)))
            
            try:
                page.goto(self.base_url, timeout=self.timeout)
                
                # Wait for page to fully load
                page.wait_for_load_state("networkidle")
                
                # Check for JavaScript errors
                critical_errors = [error for error in js_errors if "error" in error.lower()]
                
                if critical_errors:
                    print(f"⚠️ JavaScript errors detected: {critical_errors}")
                
                # Log console messages for debugging
                warnings = [msg for msg in console_messages if msg.type == "warning"]
                if warnings:
                    print(f"⚠️ Console warnings: {len(warnings)}")
                
                print("✅ JavaScript error check completed")
                
            except Exception as e:
                print(f"❌ JavaScript error test failed: {e}")
                raise
            finally:
                browser.close()
    
    def test_form_interaction_simulation(self):
        """Simulate form interactions (when authentication is available)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                page.goto(self.base_url, timeout=self.timeout)
                
                # Look for forms or input elements
                forms = page.locator("form")
                inputs = page.locator("input")
                buttons = page.locator("button")
                
                form_count = forms.count()
                input_count = inputs.count()
                button_count = buttons.count()
                
                print(f"Forms detected: {form_count}")
                print(f"Inputs detected: {input_count}")
                print(f"Buttons detected: {button_count}")
                
                # Basic interaction test - try to click first button if exists
                if button_count > 0:
                    first_button = buttons.first
                    if first_button.is_visible() and first_button.is_enabled():
                        # Get button text for logging
                        button_text = first_button.text_content()
                        print(f"Testing button interaction: '{button_text}'")
                        
                        # Click the button
                        first_button.click()
                        
                        # Wait for any response
                        page.wait_for_timeout(1000)
                        
                        print("✅ Button interaction test completed")
                
                print("✅ Form interaction simulation completed")
                
            except Exception as e:
                print(f"❌ Form interaction test failed: {e}")
                page.screenshot(path="tmp/test-results/form_interaction_failure.png")
                raise
            finally:
                browser.close()

# Pytest fixtures for async testing
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def browser():
    """Create a browser instance for testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()

@pytest.fixture
async def context(browser):
    """Create a browser context for testing."""
    context = await browser.new_context(
        viewport=PLAYWRIGHT_CONFIG["viewport"]
    )
    yield context
    await context.close()

@pytest.fixture
async def page(context):
    """Create a page for testing."""
    page = await context.new_page()
    yield page
    await page.close()

# Async test examples
@pytest.mark.asyncio
async def test_homepage_load_async(page):
    """Test homepage loading using async Playwright API."""
    base_url = PLAYWRIGHT_CONFIG["base_url"]
    
    start_time = time.time()
    try:
        await page.goto(base_url, timeout=PLAYWRIGHT_CONFIG["timeout"])
        load_time = (time.time() - start_time) * 1000
        
        title = await page.title()
        assert "WorldArchitect" in title
        
        body = page.locator("body")
        assert await body.is_visible()
        
        print(f"✅ Async homepage loaded in {load_time:.2f}ms")
        
    except Exception as e:
        await page.screenshot(path="tmp/test-results/async_homepage_failure.png")
        raise

@pytest.mark.asyncio
async def test_network_requests_async(page):
    """Test network requests and API calls."""
    base_url = PLAYWRIGHT_CONFIG["base_url"]
    
    # Track network requests
    requests = []
    responses = []
    
    page.on("request", lambda request: requests.append(request))
    page.on("response", lambda response: responses.append(response))
    
    try:
        await page.goto(base_url, timeout=PLAYWRIGHT_CONFIG["timeout"])
        
        # Wait for network to settle
        await page.wait_for_load_state("networkidle")
        
        # Analyze requests
        api_requests = [req for req in requests if "/api/" in req.url]
        static_requests = [req for req in requests if any(ext in req.url for ext in [".js", ".css", ".png", ".jpg"])]
        
        print(f"Total requests: {len(requests)}")
        print(f"API requests: {len(api_requests)}")
        print(f"Static requests: {len(static_requests)}")
        
        # Check for failed requests
        failed_responses = [resp for resp in responses if resp.status >= 400]
        if failed_responses:
            print(f"⚠️ Failed requests: {len(failed_responses)}")
            for resp in failed_responses:
                print(f"  - {resp.status} {resp.url}")
        
        print("✅ Network requests test completed")
        
    except Exception as e:
        await page.screenshot(path="tmp/test-results/network_test_failure.png")
        raise

if __name__ == "__main__":
    # Run basic sync tests
    test_instance = TestWorldArchitectPlaywright()
    test_instance.setup_method()
    
    try:
        print("Running Playwright sample tests for WorldArchitect.AI...")
        print("=" * 60)
        
        test_instance.test_homepage_load_sync()
        test_instance.test_navigation_elements_sync()
        test_instance.test_responsive_design_sync()
        test_instance.test_javascript_errors_sync()
        test_instance.test_form_interaction_simulation()
        
        print("=" * 60)
        print("✅ All sync tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        exit(1)
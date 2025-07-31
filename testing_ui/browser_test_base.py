#!/usr/bin/env python3
"""
Base class and utilities for browser-based UI tests.
Handles common setup like Flask server management and test mode configuration.
"""

import os
import subprocess
import sys
import time

import psutil
import requests
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from testing_ui.config import BASE_URL, SCREENSHOT_DIR

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Standard configuration
TEST_USER_ID = "browser-test-user"


class FlaskServerManager:
    """Manages Flask server lifecycle for tests."""

    def __init__(self):
        self.process = None
        self.log_file = "/tmp/test_server.log"

    def ensure_fresh_server(self):
        """Kill any existing Flask servers and start a fresh one."""
        print("🔄 Ensuring fresh Flask server...")

        # Kill any existing Flask processes
        killed_any = False
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info.get("cmdline") or []
                if any("main.py" in arg for arg in cmdline) and any(
                    "mvp_site" in arg for arg in cmdline
                ):
                    print(
                        f"   🛑 Killing existing Flask process (PID: {proc.info['pid']})"
                    )
                    proc.kill()
                    killed_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Also try to kill processes on port 8080
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                # Get connections for this process
                connections = proc.connections()
                for conn in connections:
                    if hasattr(conn, "laddr") and conn.laddr.port == 8080:
                        print(
                            f"   🛑 Killing process on port 8080 (PID: {proc.info['pid']})"
                        )
                        proc.kill()
                        killed_any = True
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                pass

        if killed_any:
            time.sleep(2)  # Wait longer after killing

        # Start fresh server
        print("   🚀 Starting fresh Flask server with TESTING=true...")
        env = os.environ.copy()
        env["TESTING"] = "true"
        env["PORT"] = "8088"

        with open(self.log_file, "w") as log:
            self.process = subprocess.Popen(
                ["python3", "mvp_site/main.py", "serve"],
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            )

        # Wait for server to start
        print("   ⏳ Waiting for server to start...")
        time.sleep(5)

        # Verify server is running
        try:


            response = requests.get(BASE_URL, timeout=5)
            if response.status_code == 200:
                print("   ✅ Flask server started successfully")
            else:
                print(f"   ⚠️  Server responded with status {response.status_code}")
        except Exception as e:
            print(f"   ❌ Failed to connect to server: {e}")
            raise

    def __enter__(self):
        self.ensure_fresh_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.process:
            print("   🛑 Stopping Flask server...")
            self.process.terminate()
            time.sleep(1)
            if self.process.poll() is None:
                self.process.kill()


class BrowserTestBase:
    """Base class for browser tests with common functionality."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.screenshot_prefix = test_name.lower().replace(" ", "_")
        self.screenshots_taken = 0

    def setup_browser(self) -> tuple[Browser, BrowserContext, Page]:
        """Set up Playwright browser with standard configuration."""
        playwright = sync_playwright().start()
        # FORCE headless mode for all browser tests
        browser = playwright.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context()
        page = context.new_page()

        # Set up console logging
        self.console_logs = []
        page.on(
            "console", lambda msg: self.console_logs.append(f"{msg.type}: {msg.text}")
        )
        page.on("pageerror", lambda exc: self.console_logs.append(f"pageerror: {exc}"))

        # Set up request monitoring
        page.on(
            "requestfailed",
            lambda req: self.console_logs.append(
                f"request_failed: {req.url} - {req.failure}"
            ),
        )

        return browser, context, page

    def navigate_with_test_mode(self, page: Page) -> bool:
        """Navigate to the app with test mode enabled."""
        print(f"🌐 Navigating to {BASE_URL} with test mode...")

        test_url = f"{BASE_URL}?test_mode=true&test_user_id={TEST_USER_ID}"
        page.goto(test_url, wait_until="networkidle")

        # Wait for test mode to initialize
        print("⏳ Waiting for test mode initialization...")
        page.wait_for_timeout(3000)

        # Verify test mode is active
        auth_check = page.evaluate("""
            (() => {
                const urlParams = new URLSearchParams(window.location.search);
                return {
                    testModeParam: urlParams.get('test_mode'),
                    testUserIdParam: urlParams.get('test_user_id'),
                    windowTestAuthBypass: !!window.testAuthBypass,
                    authScriptFound: !!document.querySelector('script[src*="auth.js"]')
                };
            })();
        """)

        print(f"🔍 Auth check: {auth_check}")

        # Check if we need manual activation
        if not auth_check["windowTestAuthBypass"] and page.is_visible(
            "text=Sign in with Google"
        ):
            print("⚠️  Test mode not activated, attempting manual activation...")
            self._manually_activate_test_mode(page)
            page.wait_for_timeout(2000)

        # Verify we're on dashboard
        try:
            page.wait_for_selector("#dashboard-view.active-view", timeout=5000)
            print("✅ Dashboard view is active")
            return True
        except Exception:
            print("❌ Failed to reach dashboard view")
            return False

    def _manually_activate_test_mode(self, page: Page):
        """Manually activate test mode if URL params didn't work."""
        page.evaluate(f"""
            console.log('🔧 Manually activating test mode...');
            window.testAuthBypass = {{
                enabled: true,
                userId: '{TEST_USER_ID}'
            }};

            // Hide auth view and show dashboard
            const authView = document.getElementById('auth-view');
            const dashboardView = document.getElementById('dashboard-view');
            if (authView && dashboardView) {{
                authView.classList.remove('active-view');
                dashboardView.classList.add('active-view');
            }}

            // Fire test mode ready event
            window.dispatchEvent(new CustomEvent('testModeReady', {{
                detail: {{ userId: '{TEST_USER_ID}' }}
            }}));
        """)

    def take_screenshot(self, page: Page, description: str):
        """Take a screenshot with consistent naming."""
        self.screenshots_taken += 1
        filename = (
            f"{self.screenshot_prefix}_{self.screenshots_taken:02d}_{description}.png"
        )
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        page.screenshot(path=filepath)
        print(f"📸 Screenshot: {filename}")
        return filepath

    def print_console_errors(self):
        """Print any console errors encountered during the test."""
        errors = [log for log in self.console_logs if "error" in log.lower()]
        if errors:
            print("\n⚠️  Console errors detected:")
            for error in errors[:5]:
                print(f"   {error}")

    def run_test(self):
        """Override this method in subclasses to implement the actual test."""
        raise NotImplementedError("Subclasses must implement run_test()")

    def execute(self):
        """Execute the test with proper setup and teardown."""
        print(f"\n🚀 Starting {self.test_name}")
        print(f"📍 Target URL: {BASE_URL}")
        print(f"📸 Screenshots: {SCREENSHOT_DIR}")

        # Ensure screenshot directory exists
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)

        # Run with fresh Flask server
        with FlaskServerManager():
            browser = None
            try:
                browser, context, page = self.setup_browser()

                # Navigate with test mode
                if not self.navigate_with_test_mode(page):
                    print("❌ Failed to initialize test mode")
                    return False

                # Run the actual test
                success = self.run_test(page)

                # Print console errors if any
                self.print_console_errors()

                return success

            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                if browser:
                    page.screenshot(
                        path=os.path.join(
                            SCREENSHOT_DIR, f"{self.screenshot_prefix}_error.png"
                        )
                    )
                return False

            finally:
                if browser:
                    browser.close()


def wait_for_element(page: Page, selector: str, timeout: int = 5000) -> bool:
    """Helper to wait for an element with timeout."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except Exception:
        return False


def click_button_with_text(page: Page, text: str) -> bool:
    """Helper to click a button containing specific text."""
    selectors = [f"button:has-text('{text}')", f"text={text}", f"button >> text={text}"]

    for selector in selectors:
        try:
            if page.is_visible(selector):
                page.click(selector)
                return True
        except Exception:
            continue

    return False


def take_screenshot(page: Page, filename: str) -> str:
    """
    Centralized screenshot function for all UI tests.

    Args:
        page: Playwright page object
        filename: Base filename (will be saved to /tmp/worldarchitectai/browser/)

    Returns:
        str: Full path to the screenshot file
    """
    # Ensure screenshot directory exists
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # Ensure filename has .png extension
    if not filename.endswith(".png"):
        filename += ".png"

    filepath = os.path.join(SCREENSHOT_DIR, filename)
    page.screenshot(path=filepath)
    print(f"📸 Screenshot: {filename}")
    return filepath
